#!/usr/bin/env python3
"""12-ms threshold sensitivity, each threshold LR re-fit using training labels of that threshold.
Single fixed simulator trace and 4 held-out configuration folds, NOT external validation.
"""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import average_precision_score
from reviewer_round3_experiments import grouped_folds,lr,scalar_metric
from virtual_queue_experiment import simulator,causal_features,CONTEXT,HISTORY
R=Path(__file__).resolve().parent.parent/'results'
raw=simulator(); X,_=causal_features(raw,('complete',0,1,0.,0)); arr=[]
for threshold in (8.,12.,16.,20.):
 y=(raw.latency_ms.to_numpy()>threshold).astype(int)
 for fold,tr,te in grouped_folds(raw):
  m=lr(500+fold).fit(X.iloc[tr][CONTEXT+HISTORY],y[tr]);p=m.predict_proba(X.iloc[te][CONTEXT+HISTORY])[:,1]
  arr.extend([dict(threshold_ms=threshold,fold=fold,method='LR_history',AP=scalar_metric(y[te],p),prevalence=float(y[te].mean())),dict(threshold_ms=threshold,fold=fold,method='pending_count',AP=scalar_metric(y[te],X.iloc[te].inflight_reports),prevalence=float(y[te].mean()))])
df=pd.DataFrame(arr);df.to_csv(R/'round3_threshold_sensitivity.csv',index=False)
print(df.groupby(['threshold_ms','method'])[['AP','prevalence']].mean().round(4).to_string())
