"""Lightweight independent smoke tests for event-time integrity and disjoint splits."""
import numpy as np
from virtual_queue_experiment import simulator,causal_features,group_split,TELEMETRY,ALL

df=simulator(n_per_episode=20,repetitions=1,seed=123)
a,meta=causal_features(df,TELEMETRY[0],9981)
assert len(a)==len(df)
assert np.isfinite(a[ALL].to_numpy()).all()
for seed in [42,52,72]:
 tr,va,te=group_split(df,seed)
 ids=[set(df.iloc[z].scenario_id) for z in [tr,va,te]]
 assert ids[0].isdisjoint(ids[1]) and ids[1].isdisjoint(ids[2]) and ids[0].isdisjoint(ids[2])
# Outcomes and completion timestamps of last half of a specific episode cannot change
# historical feature rows earlier in that same episode (no access to future outcomes).
b=df.copy()
ix=df[(df.scenario_id==1)&(df.replica==0)].index
second=ix[10:]
b.loc[second,'complete_ms']+=25000.
b.loc[second,'latency_ms']+=25000.
b2,_=causal_features(b,TELEMETRY[0],9981)
assert np.allclose(a.loc[ix[:10],ALL].to_numpy(), b2.loc[ix[:10],ALL].to_numpy())
print('PASS: disjoint scenarios, no missing inputs, earlier features invariant to future completion changes.')
