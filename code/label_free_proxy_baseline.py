#!/usr/bin/env python3
"""Auxiliary comparator requiring no privileged queue labels at training or inference.

Count-derived congestion proxy is a deterministic transform of event-time features,
not an estimator validated against a physical queue. No look-ahead is possible.
"""
from pathlib import Path
import argparse
import numpy as np, pandas as pd
from virtual_queue_experiment import (simulator,causal_features,group_split,make_classifier,SEEDS,CONTEXT,HISTORY,evaluate)

REGIMES=[('complete',0.,1,0.,0.),('delay_20ms',20.,1,0.,0.),('sample_every_8',0.,8,0.,0.),('missing_30pct',0.,1,.3,0.)]

def pressure_proxy(d):
    # Treat an unresolved completion as a backlog hint, NOT as proof of active service.
    # A report lag/drop increases its persistence; cap its effect via a mean report-latency estimate.
    unfinished=d['inflight_reports'].to_numpy(dtype=float)
    duration=np.clip(d['completed_delay_ewma'].to_numpy(dtype=float)-2.4,0.1,20.)
    return np.minimum(65., unfinished*duration/(1.+0.2*unfinished))

def run(out):
    d0=simulator();rows=[]
    for tv in REGIMES:
        v=tv[0]; data,_=causal_features(d0,tv)
        data['observable_pressure']=pressure_proxy(data)
        # The summary features and the deterministic pressure proxy are all observable at arrival.
        for seed in SEEDS:
            tr,va,te=group_split(d0,seed)
            ytr=d0.iloc[tr].violation.to_numpy();yte=d0.iloc[te].violation.to_numpy()
            for method,cols in [('causal_history',CONTEXT+HISTORY),('label_free_pressure',CONTEXT+HISTORY+['observable_pressure'])]:
                mdl=make_classifier(seed).fit(data.iloc[tr][cols],ytr)
                p=mdl.predict_proba(data.iloc[te][cols])[:,1]
                rows.append(dict(seed=seed,telemetry=v,method=method,**evaluate(yte,p)))
    result=pd.DataFrame(rows);out=Path(out);out.parent.mkdir(exist_ok=True,parents=True)
    result.to_csv(out,index=False)
    s=result.groupby(['telemetry','method'])[['pr_auc','brier','normalized_capture']].mean().round(6)
    print(s.to_string());return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',default='results/label_free_pressure.csv');x=a.parse_args()
    run(x.out)
