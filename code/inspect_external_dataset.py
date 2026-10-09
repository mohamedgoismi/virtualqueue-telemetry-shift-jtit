#!/usr/bin/env python3
"""Inspect the user's locally downloaded public latency CSV files. This script is
INTENTIONALLY not a trained external-validation experiment; it checks whether
packet arrival, delay and completion-feedback semantics support a valid study.
"""
import argparse, json
from pathlib import Path
import pandas as pd

def audit(paths, rows=100):
 out=[]
 for fp in paths:
  try:
   df=pd.read_csv(fp,nrows=rows)
   cols=list(df.columns);lc=[str(c).lower() for c in cols]
   def match(items):return [cols[i] for i,c in enumerate(lc) if any(x in c for x in items)]
   out.append(dict(file=fp.name,columns=cols,arrival_candidates=match(['arrival','timestamp','time_ms','tx_time']),
                   latency_candidates=match(['latency','delay','e2e']),
                   completion_candidates=match(['complete','departure','ack','rx_time','receive']),
                   loss_candidates=match(['deliver','lost','drop','success']),
                   rows_inspected=len(df),status='SCHEMA INSPECTED ONLY — no results computed'))
  except Exception as e:out.append(dict(file=fp.name,error=str(e),status='FAILED'))
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output',default='external_schema_report.json')
 a=p.parse_args();root=Path(a.directory);paths=sorted(root.glob('*.csv'))
 if not paths:raise SystemExit('No CSV files in directory. Obtain files from the original dataset publisher.')
 result=audit(paths);Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False))
 print(json.dumps(result[:2],indent=2))
 print('Only schema checked. A matched column name does not establish its timing semantics.')
