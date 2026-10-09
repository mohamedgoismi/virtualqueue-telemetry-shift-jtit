#!/usr/bin/env python3
"""VirtualQueue research simulator and strictly causal completion-telemetry experiment.

IMPORTANT: Not real NR measurements. All timeline features are computed at arrival
and only from completion reports received at or before the current arrival.
"""
from __future__ import annotations
import argparse, heapq, json, platform, sys, time, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.model_selection import GroupShuffleSplit, GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import average_precision_score, brier_score_loss, mean_absolute_error, mean_squared_error, recall_score
import sklearn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SEEDS=[42,52,72]
SLO=12.
CONTEXT=['ues','scs_khz','capability','sinr_observed','offered_mbps_per_ue','phase']
HISTORY=['arrival_ewma_gap','inflight_reports','oldest_pending_age','last_completed_delay','completed_delay_ewma','report_age','recent_reports']
ALL=CONTEXT+HISTORY
TELEMETRY=[('complete',0.,1,0.,0.),('delay_2ms',2.,1,0.,0.),('delay_8ms',8.,1,0.,0.),('delay_20ms',20.,1,0.,0.),('sample_every_4',0.,4,0.,0.),('sample_every_8',0.,8,0.,0.),('missing_30pct',0.,1,.3,0.),('quantized_4ms',0.,1,0.,4.)]

def simulator(n_per_episode=150, repetitions=2, seed=20261009):
    rng=np.random.default_rng(seed);rows=[]; sid=0
    for ues in (1,4,10):
      for scs in (15,30):
       for cap in (1,2):
        for sinr in (5.,15.):
         for offered in (2.,5.,10.):
          sid+=1
          for rep in range(repetitions):
           t=0.; q_end=0.; hidden=float(np.exp(rng.normal(0.,.12)))
           for i in range(n_per_episode):
            phase=(i%60)/60.
            sinr_now=float(sinr+rng.normal(0,2.))
            rate_coeff=cap*(scs/15)**.32*max(.36,1+.042*(sinr_now-8))
            service_avg=1.6/rate_coeff
            load=(ues*offered)/(40.*cap*(scs/15)**.20)
            burst=.91+.32*(np.sin(2*np.pi*phase)**2)
            util=.24+.90*load*burst*hidden*max(.65,1-.025*(sinr_now-9))
            gap=float(rng.exponential(service_avg/max(util,.03)))
            t+=gap
            wait=max(0.,q_end-gap)
            service=float(rng.gamma(2.2,service_avg/2.2))
            noise=float(rng.exponential(.35+.06*max(0,8-sinr_now)))
            delay=2.4+wait+service+noise
            q_end=min(wait+service,65.)
            rows.append(dict(scenario_id=sid,replica=rep,packet_id=i,arrival_ms=t,
                complete_ms=t+delay,latency_ms=delay,violation=int(delay>SLO),
                true_wait_ms=wait,ues=ues,scs_khz=scs,capability=cap,
                nominal_sinr=sinr,sinr_observed=sinr_now,offered_mbps_per_ue=offered,phase=phase))
    return pd.DataFrame(rows)

def causal_features(data, variant, seed=9981):
    """Each episode is independently reset. Reports are delivered after COMPLETION + lag.
    Report loss and sampling are applied to reporting, not to truth. Unreported arrivals
    remain pending until a fixed 120 ms timeout. No future labels are consulted at inference.
    Input 'complete_ms' is used solely by the telemetry-source/event scheduler, never
    as a feature, and only after report_time <= arrival_time.
    """
    name,lag,sample,drop,quant=variant
    rng=np.random.default_rng(seed+sum(ord(c) for c in name))
    rows=[]; strict_count=0; report_count=0
    for (sid,rep), ep in data.groupby(['scenario_id','replica'],sort=False):
       ep=ep.sort_values('packet_id')
       scheduled=[]; reported=set(); recent=[]; arrivals=[]
       last_report_t=None; last_delay=2.4; delay_ema=2.4; gap_ema=3.; prev_t=None
       for row in ep.itertuples(index=False):
           now=float(row.arrival_ms)
           while scheduled and scheduled[0][0] <= now:
               rt,pid,delivered=heapq.heappop(scheduled)
               if delivered:
                   reported.add(pid);last_report_t=rt
                   val=float(data.loc[pid,'latency_ms'])
                   if quant>0:val=quant*round(val/quant)
                   last_delay=val; delay_ema=.8*delay_ema+.2*val
                   recent.append(rt);report_count+=1
                   if rt>now+1e-9:raise AssertionError('future report')
           # Exclude completed or timed-out packet indices. Timed out still cannot be inferred from its delay.
           arrivals=[(pid,a) for pid,a in arrivals if pid not in reported and now-a<120.]
           recent=[x for x in recent if now-x<=25.]
           if prev_t is not None:gap_ema=.80*gap_ema+.20*(now-prev_t)
           oldest=max([now-a for _,a in arrivals],default=0.)
           hist=dict(arrival_ewma_gap=gap_ema,inflight_reports=len(arrivals),
                   oldest_pending_age=oldest,last_completed_delay=last_delay,
                   completed_delay_ewma=delay_ema,
                   report_age=(now-last_report_t if last_report_t is not None else 120.),
                   recent_reports=len(recent))
           item=dict(scenario_id=sid,replica=rep,packet_id=row.packet_id,
                     true_wait_ms=row.true_wait_ms,violation=row.violation)
           item.update({k:getattr(row,k) for k in CONTEXT});item.update(hist)
           rows.append(item)
           arrivals.append((int(row.Index) if hasattr(row,'Index') else int(ep.index[row.packet_id]),now))
           # Schedule AFTER features have been recorded; this prevents current packet leakage.
           if (int(row.packet_id) % sample)==0 and rng.random()>=drop:
               rt=float(row.complete_ms)+lag
               pid=int(ep.index[row.packet_id]);heapq.heappush(scheduled,(rt,pid,True))
           prev_t=now; strict_count+=1
    out=pd.DataFrame(rows)
    assert len(out)==len(data)
    assert out[ALL].notna().all().all()
    return out,dict(variant=name,eligible_reports=report_count,feature_rows=strict_count,
                    timing_rule='completion+reporting_lag<=current_arrival')

def group_split(data,seed):
    groups=data.scenario_id.to_numpy(); ids=np.arange(len(data))
    g=GroupShuffleSplit(n_splits=1,test_size=.22,random_state=seed)
    trval,te=next(g.split(ids,groups=groups))
    g2=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=seed+121)
    a,b=next(g2.split(trval,groups=groups[trval]))
    tr,va=trval[a],trval[b]
    assert not(set(groups[tr])&set(groups[va])) and not(set(groups[tr])&set(groups[te]))
    return tr,va,te

def make_classifier(seed):
    return HistGradientBoostingClassifier(max_iter=50,max_leaf_nodes=15,min_samples_leaf=32,
        learning_rate=.065,l2_regularization=4.,random_state=seed)

def make_q_reg(seed):
    return HistGradientBoostingRegressor(max_iter=55,max_leaf_nodes=12,min_samples_leaf=30,
        learning_rate=.055,l2_regularization=4.,random_state=seed)

def evaluate(y,p):
    p=np.asarray(p)
    ap=float(average_precision_score(y,p)); b=float(brier_score_loss(y,p))
    n=max(1,int(np.ceil(.1*len(y)))); order=np.argsort(-p,kind='stable')[:n]
    capture=float(np.sum(y[order])/max(1,np.sum(y)))
    prev=float(np.mean(y));cap=min(1.,.1/prev) if prev>0 else np.nan
    return dict(pr_auc=ap,brier=b,capture=capture,capture_ceiling=cap,
                normalized_capture=capture/cap if cap>0 else np.nan,prevalence=prev)

def run(outdir,figdir,n_per_episode=150):
    outdir.mkdir(parents=True,exist_ok=True);figdir.mkdir(parents=True,exist_ok=True)
    t0=time.time();df=simulator(n_per_episode=n_per_episode)
    data_sha=hashlib.sha256(pd.util.hash_pandas_object(df,index=True).values.tobytes()).hexdigest()
    # Save entire synthetic trace only because this artifact is explicitly not real 5G data.
    df.to_csv(outdir/'synthetic_trace.csv',index=False)
    features={};telemeta=[]
    for name,lag,sample,drop,quant in TELEMETRY:
        d,m=causal_features(df,(name,lag,sample,drop,quant));features[name]=d;telemeta.append(m)
    results=[];splits=[];diagnostics=[]
    for seed in SEEDS:
        tr,va,te=group_split(df,seed)
        splits.append(dict(seed=seed,train=len(tr),validation=len(va),test=len(te),
            groups_train=df.iloc[tr].scenario_id.nunique(),groups_validation=df.iloc[va].scenario_id.nunique(),
            groups_test=df.iloc[te].scenario_id.nunique(),test_prevalence=df.iloc[te].violation.mean()))
        ytr=df.iloc[tr].violation.to_numpy(); yte=df.iloc[te].violation.to_numpy()
        for name,*_ in TELEMETRY:
            d=features[name]
            qtr=d.iloc[tr].true_wait_ms.to_numpy();qte=d.iloc[te].true_wait_ms.to_numpy()
            qmodel=make_q_reg(seed)
            qmodel.fit(d.iloc[tr][ALL],qtr)
            qhat=np.maximum(0.,qmodel.predict(d.iloc[te][ALL]))
            # Cross-fit virtual estimates on TRAIN groups. Without this precaution,
            # supervised queue labels could leak into the downstream training feature.
            qtrain=np.empty(len(tr),dtype=float)
            x_group=d.iloc[tr].scenario_id.to_numpy()
            for fold_a,fold_b in GroupKFold(n_splits=3).split(d.iloc[tr],groups=x_group):
                qm_fold=make_q_reg(seed)
                qm_fold.fit(d.iloc[tr[fold_a]][ALL],qtr[fold_a])
                qtrain[fold_b]=np.maximum(0.,qm_fold.predict(d.iloc[tr[fold_b]][ALL]))
            # Both history and virtual use the same observable inputs; virtual adds a task-guided auxiliary estimate.
            sets={
                'context':(d.iloc[tr][CONTEXT],d.iloc[te][CONTEXT]),
                'causal_history':(d.iloc[tr][ALL],d.iloc[te][ALL]),
                'virtual_queue':(d.iloc[tr][ALL].assign(virtual_wait=qtrain),d.iloc[te][ALL].assign(virtual_wait=qhat)),
                'oracle_wait':(d.iloc[tr][CONTEXT].assign(true_wait=qtr),d.iloc[te][CONTEXT].assign(true_wait=qte))
            }
            for kind,(xtr,xte) in sets.items():
                # Once trained on group-held-out data, evaluate at test once.
                m=make_classifier(seed);m.fit(xtr,ytr);p=m.predict_proba(xte)[:,1]
                results.append(dict(seed=seed,telemetry=name,method=kind,**evaluate(yte,p)))
            diagnostics.append(dict(seed=seed,telemetry=name,
                virtual_rmse_ms=float(np.sqrt(mean_squared_error(qte,qhat))),
                virtual_mae_ms=float(mean_absolute_error(qte,qhat)),
                target_wait_mean=float(qte.mean()),
                target_wait_p90=float(np.quantile(qte,.9))))
    res=pd.DataFrame(results);diag=pd.DataFrame(diagnostics)
    res.to_csv(outdir/'model_metrics.csv',index=False);diag.to_csv(outdir/'queue_reconstruction.csv',index=False)
    pd.DataFrame(splits).to_csv(outdir/'split_summary.csv',index=False)
    (outdir/'telemetry_audit.json').write_text(json.dumps(telemeta,indent=2))
    summary=res.groupby(['telemetry','method'],as_index=False)[['pr_auc','brier','capture','normalized_capture']].mean()
    summary.to_csv(outdir/'summary.csv',index=False)
    def figure(name, y, ylabel):
      fig,ax=plt.subplots(figsize=(7.,3.8))
      s=summary.pivot(index='telemetry',columns='method',values=y).reindex([x[0] for x in TELEMETRY])
      for col in ['context','causal_history','virtual_queue','oracle_wait']:
          ax.plot(np.arange(len(s)),s[col],marker='o',label=col.replace('_',' '))
      ax.set_xticks(np.arange(len(s)),[x.replace('_','\n') for x in s.index],rotation=15,ha='right',fontsize=7)
      ax.set_ylabel(ylabel);ax.grid(alpha=.18);ax.legend(fontsize=7,ncol=2)
      fig.tight_layout();fig.savefig(figdir/(name+'.pdf'),bbox_inches='tight');fig.savefig(figdir/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
    figure('pr_auc_telemetry','pr_auc','PR-AUC on unseen scenarios')
    figure('normalized_capture','normalized_capture','Normalized capture, top 10% alarms')
    fig,ax=plt.subplots(figsize=(6.9,3.5))
    g=diag.groupby('telemetry').virtual_mae_ms.mean().reindex([x[0] for x in TELEMETRY]);ax.bar(np.arange(len(g)),g)
    ax.set_xticks(np.arange(len(g)),[x.replace('_','\n') for x in g.index],rotation=15,ha='right',fontsize=7)
    ax.set_ylabel('Queue waiting-time MAE (ms)');ax.grid(axis='y',alpha=.2);fig.tight_layout()
    fig.savefig(figdir/'queue_mae.pdf',bbox_inches='tight');fig.savefig(figdir/'queue_mae.png',dpi=180,bbox_inches='tight');plt.close(fig)
    meta=dict(label='SYNTHETIC_QUEUEING_PILOT_NOT_NR',generator_seed=20261009,
         split_seeds=SEEDS,scenarios=int(df.scenario_id.nunique()),episodes=int(df.groupby(['scenario_id','replica']).ngroups),
         packets=len(df),latency_limit_ms=SLO,trace_sha256=data_sha,elapsed_seconds=round(time.time()-t0,2),
         sklearn_version=sklearn.__version__,numpy_version=np.__version__,python=sys.version.split()[0],
         note='Virtual queue regressor supervised by privileged simulator wait values at TRAIN time only')
    (outdir/'metadata.json').write_text(json.dumps(meta,indent=2))
    print('\n== DATA ==\n',meta)
    print('\n== SUMMARY ==\n',summary.to_string(index=False))
    print('\n== QUEUE MAE ==\n',diag.groupby('telemetry').virtual_mae_ms.mean().to_string())
    return res,diag,summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',default='results');p.add_argument('--figures',default='figures');p.add_argument('--rows',type=int,default=150)
    a=p.parse_args();run(Path(a.out),Path(a.figures),a.rows)
