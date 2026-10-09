#!/usr/bin/env python3
"""Deployment shift stress test: fit on complete reporting, use frozen classifier in new reporting regimes."""
import argparse
from pathlib import Path
import numpy as np,pandas as pd
from virtual_queue_experiment import simulator,causal_features,make_classifier,group_split,SEEDS,CONTEXT,HISTORY,evaluate
REGIMES=[('complete',0.,1,0.,0.),('delay_8ms',8.,1,0.,0.),('delay_20ms',20.,1,0.,0.),('sample_every_8',0.,8,0.,0.),('missing_30pct',0.,1,.3,0.)]
def run(out):
    raw=simulator(); ds={v[0]:causal_features(raw,v)[0] for v in REGIMES};y=raw.violation.to_numpy();rows=[]
    for seed in SEEDS:
        tr,va,te=group_split(raw,seed)
        train=ds['complete'].iloc[tr][CONTEXT+HISTORY]
        model=make_classifier(seed).fit(train,y[tr])
        for name,d in ds.items():
            p=model.predict_proba(d.iloc[te][CONTEXT+HISTORY])[:,1]
            rows.append(dict(seed=seed,telemetry=name,training_regime='complete_only',method='causal_history',**evaluate(y[te],p)))
    r=pd.DataFrame(rows);out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);r.to_csv(out,index=False)
    summary=r.groupby('telemetry')[['pr_auc','brier','normalized_capture']].mean()
    print(summary.round(4).to_string());return r
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results/cross_regime_transfer.csv');args=ap.parse_args();run(args.out)
