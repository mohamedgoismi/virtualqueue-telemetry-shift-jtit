#!/usr/bin/env python3
"""Named factor-level exclusions (not random-packet CV); controls same as main study."""
import argparse
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.model_selection import GroupShuffleSplit,GroupKFold
from sklearn.metrics import mean_absolute_error
from virtual_queue_experiment import simulator,causal_features,make_classifier,make_q_reg,CONTEXT,HISTORY,evaluate
from label_free_proxy_baseline import pressure_proxy

EXCLUSIONS=[('ues_10','ues',10),('sinr_5','nominal_sinr',5.),('offered_10','offered_mbps_per_ue',10.),('scs_30','scs_khz',30)]

def run(out):
    raw=simulator();d,_=causal_features(raw,('complete',0.,1,0.,0.));d['observable_pressure']=pressure_proxy(d)
    y=raw.violation.to_numpy();rows=[]
    for tag,field,value in EXCLUSIONS:
        test=np.flatnonzero(raw[field].to_numpy()==value)
        remain=np.flatnonzero(raw[field].to_numpy()!=value)
        spl=GroupShuffleSplit(n_splits=1,test_size=.22,random_state=420)
        a,b=next(spl.split(remain,groups=raw.iloc[remain].scenario_id.to_numpy()))
        tr,va=remain[a],remain[b]
        assert not (set(raw.iloc[tr].scenario_id)&set(raw.iloc[test].scenario_id))
        assert not (set(raw.iloc[va].scenario_id)&set(raw.iloc[test].scenario_id))
        assert len(test)>0 and y[test].sum()>0 and y[tr].sum()>0
        qtr=d.iloc[tr].true_wait_ms.to_numpy()
        qmod=make_q_reg(42);qmod.fit(d.iloc[tr][CONTEXT+HISTORY],qtr)
        qtrain=np.zeros(len(tr)); groups=d.iloc[tr].scenario_id.to_numpy()
        for ix,jx in GroupKFold(n_splits=3).split(d.iloc[tr],groups=groups):
            fold=make_q_reg(42).fit(d.iloc[tr[ix]][CONTEXT+HISTORY],qtr[ix])
            qtrain[jx]=np.maximum(0.,fold.predict(d.iloc[tr[jx]][CONTEXT+HISTORY]))
        qtest=np.maximum(0.,qmod.predict(d.iloc[test][CONTEXT+HISTORY]))
        sets={
            'context':(d.iloc[tr][CONTEXT],d.iloc[test][CONTEXT]),
            'causal_history':(d.iloc[tr][CONTEXT+HISTORY],d.iloc[test][CONTEXT+HISTORY]),
            'label_free_pressure':(d.iloc[tr][CONTEXT+HISTORY+['observable_pressure']],d.iloc[test][CONTEXT+HISTORY+['observable_pressure']]),
            'virtual_queue':(d.iloc[tr][CONTEXT+HISTORY].assign(virtual_wait=qtrain),d.iloc[test][CONTEXT+HISTORY].assign(virtual_wait=qtest))
        }
        for kind,(xtr,xte) in sets.items():
            model=make_classifier(42).fit(xtr,y[tr]);p=model.predict_proba(xte)[:,1]
            rows.append(dict(exclusion=tag,train=len(tr),validation=len(va),test=len(test),
                             test_scenarios=raw.iloc[test].scenario_id.nunique(),method=kind,**evaluate(y[test],p)))
    res=pd.DataFrame(rows);out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);res.to_csv(out,index=False)
    print(res.pivot(index='exclusion',columns='method',values='pr_auc').round(4).to_string())
    print(res.groupby('exclusion').first()[['test','test_scenarios','prevalence']].round(4).to_string())
    return res

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results/factor_holdout.csv');args=ap.parse_args();run(args.out)
