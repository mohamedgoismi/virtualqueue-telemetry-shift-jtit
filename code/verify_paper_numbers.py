#!/usr/bin/env python3
"""Machine-readable numerical consistency checks for the JTIT manuscript."""
from pathlib import Path
import pandas as pd
root=Path(__file__).resolve().parents[1]
sm=pd.read_csv(root/'results/summary.csv')
lf=pd.read_csv(root/'results/label_free_pressure.csv')
lofo=pd.read_csv(root/'results/factor_holdout.csv')
fr=pd.read_csv(root/'results/cross_regime_transfer.csv')

expected={
 ('complete','context'):0.8261,
 ('complete','causal_history'):0.9777,
 ('complete','virtual_queue'):0.9798,
 ('complete','oracle_wait'):0.9989,
 ('delay_20ms','causal_history'):0.9520,
 ('delay_20ms','virtual_queue'):0.9497,
}
for (tel,method),v in expected.items():
 x=sm[(sm.telemetry==tel)&(sm.method==method)].iloc[0].pr_auc
 assert abs(x-v)<.00006,(tel,method,x,v)
for regime,val in [('complete',0.9752),('delay_20ms',0.9511),('sample_every_8',0.9612),('missing_30pct',0.9745)]:
 x=lf[(lf.telemetry==regime)&(lf.method=='label_free_pressure')].pr_auc.mean()
 assert abs(x-val)<.00006,('label-free',regime,x,val)
for tag, expected_history in [('ues_10',0.9608),('sinr_5',0.9621),('offered_10',0.9672),('scs_30',0.9759)]:
 x=lofo[(lofo.exclusion==tag)&(lofo.method=='causal_history')].iloc[0].pr_auc
 assert abs(x-expected_history)<.00006,(tag,x,expected_history)
for tel,v in [('complete',0.9777),('delay_8ms',0.9462),('delay_20ms',0.8316),('sample_every_8',0.6408),('missing_30pct',0.7649)]:
 x=fr[fr.telemetry==tel].pr_auc.mean()
 assert abs(x-v)<.00006,(tel,x,v)
print('PASS: historical results and all three new result files agree with the manuscript to 4 decimal places.')
