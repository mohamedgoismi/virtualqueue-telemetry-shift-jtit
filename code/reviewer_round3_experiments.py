#!/usr/bin/env python3
"""Third reviewer: 4-fold context controls, moderate-load analysis, repeated synthetic traces,
and queue telemetry regime normalization, without test-set fitting.
Run from project root: python code/reviewer_round3_experiments.py --repeat 10
All results are for the *synthetic* queue generator, not network/NR measurements.
"""
import argparse, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from virtual_queue_experiment import simulator, causal_features, CONTEXT, HISTORY
BASE=Path(__file__).resolve().parent.parent
R=BASE/'results'; R.mkdir(exist_ok=True)
C=CONTEXT+HISTORY
COMPLETE=('complete',0,1,0.,0.)
SPARSE=('sample_every_8',0,8,0.,0.)

def lr(seed):
    return make_pipeline(StandardScaler(),LogisticRegression(C=1.,max_iter=350,random_state=seed))

def hgb(seed):
    return HistGradientBoostingClassifier(max_iter=75,max_leaf_nodes=12,min_samples_leaf=42,learning_rate=.065,l2_regularization=4,random_state=seed)

def grouped_folds(raw, seed=341):
    """Existing M4 allocation when seed=341; vary 72-group identities in other repeats."""
    groups=raw.scenario_id.to_numpy()
    if seed!=341:
        rng=np.random.default_rng(seed)
        p=rng.permutation(np.unique(groups))
        mapping={int(x):int(z) for x,z in zip(np.unique(groups),p)}
        groups=np.array([mapping[int(x)] for x in groups]);
    folds=list(GroupKFold(n_splits=4).split(raw,raw.violation,groups))
    rng=np.random.default_rng(341 if seed==341 else seed)
    for f,(trval,te) in enumerate(folds):
        va_scen=rng.choice(np.unique(raw.iloc[trval].scenario_id),size=12,replace=False)
        tr=trval[~np.isin(raw.iloc[trval].scenario_id.to_numpy(),va_scen)]
        assert not set(raw.iloc[tr].scenario_id)&set(raw.iloc[te].scenario_id)
        yield f,tr,te

def scalar_metric(y,p):
    if np.unique(y).size<2:return np.nan
    return float(average_precision_score(y,p))

def test_main_trace():
    raw=simulator(); x,_=causal_features(raw, COMPLETE); y=raw.violation.to_numpy()
    conf=raw.groupby('scenario_id').violation.mean()
    moderate=set(conf[(conf>=.05)&(conf<=.50)].index)
    nonzero=set(conf[(conf>0)&(conf<1)].index)
    ctx_rows=[]; pred_rows=[]; subsets=[]
    for f,tr,te in grouped_folds(raw):
        for label, cols, factory in [('LR_context',CONTEXT,lr),('HGB_context',CONTEXT,hgb),('LR_history',C,lr),('HGB_history',C,hgb)]:
            m=factory(100+f)
            m.fit(x.iloc[tr][cols],y[tr])
            pr=m.predict_proba(x.iloc[te][cols])[:,1]
            ctx_rows.append(dict(fold=f,model=label,AP=scalar_metric(y[te],pr),brier=brier_score_loss(y[te],pr),n=len(te),prevalence=float(y[te].mean())))
            pred_rows.extend(dict(fold=f,scenario_id=int(raw.iloc[ix].scenario_id),replica=int(raw.iloc[ix].replica),packet_id=int(raw.iloc[ix].packet_id),y=int(y[ix]),model=label,p=float(q)) for ix,q in zip(te,pr))
        count=x.iloc[te].inflight_reports.to_numpy()
        pred_rows.extend(dict(fold=f,scenario_id=int(raw.iloc[ix].scenario_id),replica=int(raw.iloc[ix].replica),packet_id=int(raw.iloc[ix].packet_id),y=int(y[ix]),model='pending_count',p=float(q)) for ix,q in zip(te,count))
    P=pd.DataFrame(pred_rows);P.to_csv(R/'round3_oof_predictions.csv',index=False)
    pd.DataFrame(ctx_rows).to_csv(R/'round3_context_fourfold.csv',index=False)
    for model,group in P.groupby('model'):
        for scope,ids in [('all',set(conf.index)),('intermediate_5to50pct',moderate),('nondegenerate',nonzero)]:
            for fold,d in group[group.scenario_id.isin(ids)].groupby('fold'):
                subsets.append(dict(model=model,scope=scope,fold=fold,n=len(d),configs=d.scenario_id.nunique(),prevalence=float(d.y.mean()),AP=scalar_metric(d.y.to_numpy(),d.p.to_numpy())))
    S=pd.DataFrame(subsets);S.to_csv(R/'round3_intermediate_load.csv',index=False)
    comp=S.groupby(['model','scope']).agg(mean_AP=('AP','mean'),valid_folds=('AP','count'),n_configs=('configs','sum'),avg_prevalence=('prevalence','mean')).reset_index();comp.to_csv(R/'round3_intermediate_summary.csv',index=False)
    print('main 4fold',pd.DataFrame(ctx_rows).groupby('model').AP.mean().round(4).to_dict(),flush=True)
    print('moderate configs',len(moderate),'of 72',comp[comp.scope=='intermediate_5to50pct'][['model','mean_AP']].round(4).to_string(index=False),flush=True)
    return raw,x,y,P

def eligible_report_count(raw, sample=8, timeout=120.):
    """Causal count using publicly known deterministic reporting schedule, and arrival/report times.
    Computed solely from arrivals and reports received by each decision time.
    """
    from collections import deque
    out=np.empty(len(raw),dtype=float)
    for _,ep in raw.groupby(['scenario_id','replica'],sort=False):
        ep=ep.sort_values('packet_id'); active=deque()
        import heapq
        events=[]; delivered=set()
        for idx,row in ep.iterrows():
            now=float(row.arrival_ms)
            while events and events[0][0]<=now:
                _,pid=heapq.heappop(events);delivered.add(pid)
            active=deque((pid,t) for pid,t in active if pid not in delivered and now-t<timeout)
            out[idx]=len(active)
            if row.packet_id%sample==0:
                active.append((idx,now))
                heapq.heappush(events,(float(row.complete_ms),idx))
    return out

def regime_aware(raw,x,y):
    sample,_=causal_features(raw, SPARSE)
    corrected=sample.copy()
    corrected['inflight_reports']=eligible_report_count(raw,8)
    rr=[]
    for f,tr,te in grouped_folds(raw):
        frozen=lr(100+f).fit(x.iloc[tr][C],y[tr])
        for method,d in [('frozen_uncorrected',sample),('frozen_sampling_aware',corrected)]:
            p=frozen.predict_proba(d.iloc[te][C])[:,1]
            rr.append(dict(fold=f,method=method,AP=scalar_metric(y[te],p),brier=brier_score_loss(y[te],p)))
    df=pd.DataFrame(rr);df.to_csv(R/'round3_sampling_aware.csv',index=False)
    print('sample8 aware',df.groupby('method').AP.mean().round(4).to_dict(),flush=True)

def repeated_runs(n):
    """Fresh RNG generator seeds, each with four new test-group folds; inference on all 72 configs.
    One training run per model/fold; no HGB reruns in this affordable extension.
    """
    out=[]; t0=time.time()
    for i in range(n):
        gen_seed=20261100+i
        raw=simulator(seed=gen_seed)
        d,_=causal_features(raw,COMPLETE,seed=gen_seed+100)
        y=raw.violation.to_numpy()
        for fold,tr,te in grouped_folds(raw,seed=5000+i):
            for label,cols in [('LR_context',CONTEXT),('LR_history',C)]:
                m=lr(700+i*10+fold).fit(d.iloc[tr][cols],y[tr]);p=m.predict_proba(d.iloc[te][cols])[:,1]
                out.append(dict(generator_seed=gen_seed,split_seed=5000+i,fold=fold,method=label,AP=scalar_metric(y[te],p),prevalence=y[te].mean()))
            out.append(dict(generator_seed=gen_seed,split_seed=5000+i,fold=fold,method='pending_count',AP=scalar_metric(y[te],d.iloc[te].inflight_reports),prevalence=y[te].mean()))
        print('fresh trace',i+1,'/',n,'elapsed',round(time.time()-t0,1),flush=True)
    df=pd.DataFrame(out);df.to_csv(R/'round3_independent_traces.csv',index=False)
    tr=df.groupby(['generator_seed','method']).AP.mean().unstack('method')
    means=tr.agg(['mean','std']).round(6)
    from scipy.stats import t
    confidence=[]
    for method in tr.columns:
        vals=tr[method].to_numpy();mean=np.mean(vals);sem=np.std(vals,ddof=1)/np.sqrt(n)
        ci=t.ppf(.975,n-1)*sem
        confidence.append(dict(method=method,n_traces=n,mean_AP=float(mean),ci_low=float(mean-ci),ci_high=float(mean+ci),sd_traces=float(np.std(vals,ddof=1))))
    dfci=pd.DataFrame(confidence);dfci.to_csv(R/'round3_trace_confidence.csv',index=False)
    paired=tr['LR_history']-tr['pending_count']; other=tr['LR_history']-tr['LR_context']
    pair={'n_traces':n,'LR_history_minus_count_mean':float(paired.mean()),'LR_history_minus_count_min':float(paired.min()),'LR_history_minus_context_mean':float(other.mean()),'LR_history_minus_context_min':float(other.min()),'note':'Paired over independent RNG traces, but still from same simulator family and related group-design.'}
    (R/'round3_trace_paired.json').write_text(json.dumps(pair,indent=2))
    print('repeats',means.to_string(),flush=True)

def budget_ceiling():
    b=pd.read_csv(R/'operational_budgets_fourfold.csv')
    b['precision_ceiling']=np.minimum(1.,b.prevalence/b.budget)
    b['fraction_of_precision_ceiling']=b.alert_precision/b.precision_ceiling
    b.to_csv(R/'round3_budgets_with_ceiling.csv',index=False)
    print('budget',b.groupby(['model','budget'])[['alert_precision','precision_ceiling','fraction_of_precision_ceiling']].mean().round(3).to_string(),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--repeat',type=int,default=10);args=ap.parse_args()
    raw,x,y,p=test_main_trace();budget_ceiling();regime_aware(raw,x,y);repeated_runs(args.repeat)
