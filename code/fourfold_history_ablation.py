"""One-feature-out LR ablation on four scenario-disjoint folds.
Exactly the same LR preprocessing and group allocation as the published
four-fold fixed model. No test tuning or privileged queue information.
"""
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from virtual_queue_experiment import simulator,causal_features,CONTEXT,HISTORY
raw=simulator();df=causal_features(raw,('complete',0,1,0.,0.))[0]; yy=raw.violation.to_numpy()
folds=list(GroupKFold(4).split(raw,yy,raw.scenario_id)); rng=np.random.default_rng(341)
rr=[]
for f,(alltr,te) in enumerate(folds):
  sc=np.unique(raw.iloc[alltr].scenario_id);ch=rng.choice(sc,size=12,replace=False)
  tr=alltr[~np.isin(raw.iloc[alltr].scenario_id,ch)]
  for omit in ['NONE']+HISTORY:
    feats=CONTEXT+[x for x in HISTORY if x!=omit]
    m=make_pipeline(StandardScaler(),LogisticRegression(C=1,max_iter=350,random_state=100+f))
    m.fit(df.iloc[tr][feats],yy[tr]);p=m.predict_proba(df.iloc[te][feats])[:,1]
    rr.append(dict(fold=f,excluded_feature=omit,ap=float(average_precision_score(yy[te],p))))
rows=pd.DataFrame(rr);dest=Path(__file__).resolve().parent.parent/'results'/'fourfold_LR_feature_ablation.csv';rows.to_csv(dest,index=False)
print(rows.groupby('excluded_feature').ap.agg(['mean','std']).round(5).to_string())
