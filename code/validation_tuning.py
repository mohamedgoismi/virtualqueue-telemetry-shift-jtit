"""Validation selection by held-out scenario groups, without test leakage."""
from pathlib import Path
import sys
import numpy as np,pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,brier_score_loss
from virtual_queue_experiment import simulator,causal_features,CONTEXT,HISTORY

raw=simulator();d=causal_features(raw,('complete',0,1,0.,0.))[0];X=d[CONTEXT+HISTORY];y=raw.violation.to_numpy()
folds=list(GroupKFold(n_splits=4).split(raw,y,raw.scenario_id));rng=np.random.default_rng(341)
rows=[]
for f,(alltr,te) in enumerate(folds):
    scen=np.unique(raw.iloc[alltr].scenario_id);chosen=rng.choice(scen,size=12,replace=False)
    va=alltr[np.isin(raw.iloc[alltr].scenario_id,chosen)];tr=alltr[~np.isin(raw.iloc[alltr].scenario_id,chosen)]
    for kind in ['LR','HGB']:
        configs=([('C=0.1',.1),('C=1',1.),('C=10',10.)] if kind=='LR' else [('iter50_leaf12',(50,12)),('iter90_leaf12',(90,12)),('iter50_leaf24',(50,24)),('iter90_leaf24',(90,24))])
        trials=[]
        def get_model(v):
            if kind=='LR':return make_pipeline(StandardScaler(),LogisticRegression(C=v,max_iter=500,random_state=313+f))
            return HistGradientBoostingClassifier(max_iter=v[0],max_leaf_nodes=v[1],min_samples_leaf=42,learning_rate=.065,l2_regularization=4.,random_state=313+f)
        for name,v in configs:
            m=get_model(v);m.fit(X.iloc[tr],y[tr]);p=m.predict_proba(X.iloc[va])[:,1]
            trials.append((average_precision_score(y[va],p),name,v))
        best=max(trials,key=lambda z:z[0]);m=get_model(best[2]);m.fit(X.iloc[alltr],y[alltr]);p=m.predict_proba(X.iloc[te])[:,1]
        rows.append(dict(fold=f,model=kind,selected=best[1],validation_ap=float(best[0]),test_ap=float(average_precision_score(y[te],p)),test_brier=float(brier_score_loss(y[te],p)),test_prev=float(y[te].mean()),n_train=len(tr),n_validation=len(va),n_fit_final=len(alltr),n_test=len(te)))
    print('tuned',f+1,flush=True)
p=Path(__file__).resolve().parent.parent/'results'/'validation_tuned_models.csv';pd.DataFrame(rows).to_csv(p,index=False)
print(pd.DataFrame(rows).groupby('model')[['validation_ap','test_ap','test_brier']].agg(['mean','std']).round(4))
