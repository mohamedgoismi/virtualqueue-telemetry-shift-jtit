"""Fast integrity tests. No network or GPU required."""
from pathlib import Path
import sys, unittest, json, hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'))
from virtual_queue_experiment import simulator, causal_features, TELEMETRY, CONTEXT, HISTORY, group_split

class TestRepository(unittest.TestCase):
    def test_small_deterministic_trace(self):
        x=simulator(n_per_episode=8,repetitions=1,seed=123)
        y=simulator(n_per_episode=8,repetitions=1,seed=123)
        self.assertEqual(len(x),72*8)
        self.assertTrue(x.equals(y))
        self.assertEqual(x.scenario_id.nunique(),72)
    def test_event_time_features(self):
        data=simulator(n_per_episode=16,repetitions=1,seed=123)
        features,_=causal_features(data,TELEMETRY[0],seed=9981)
        self.assertTrue(np.isfinite(features[CONTEXT+HISTORY].to_numpy()).all())
        tampered=data.copy()
        ix=data[(data.scenario_id==1)&(data.replica==0)].index
        tampered.loc[ix[8:],'complete_ms']+=10000
        tampered.loc[ix[8:],'latency_ms']+=10000
        altered,_=causal_features(tampered,TELEMETRY[0],seed=9981)
        np.testing.assert_allclose(features.loc[ix[:8],CONTEXT+HISTORY],altered.loc[ix[:8],CONTEXT+HISTORY])
    def test_scenario_disjointness(self):
        data=simulator(n_per_episode=5,repetitions=1,seed=123)
        for seed in (42,52,72):
            tr,va,te=group_split(data,seed)
            groups=[set(data.iloc[x].scenario_id) for x in (tr,va,te)]
            self.assertFalse(groups[0]&groups[1] or groups[0]&groups[2] or groups[1]&groups[2])
    def test_archived_artifacts(self):
        for f in ['results/synthetic_trace.csv','results/round3_independent_traces.csv',
                  'results/round3_trace_paired.json','results/round3_oof_predictions.csv',
                  'CITATION.cff','LICENSE','docs/PROVENANCE.md']:
            self.assertTrue((ROOT/f).is_file(),f)
        with (ROOT/'results/round3_trace_paired.json').open() as h: x=json.load(h)
        self.assertEqual(x['n_traces'],10)

if __name__=='__main__':unittest.main()
