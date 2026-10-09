from pathlib import Path
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent.parent/'results'; F=Path(__file__).resolve().parent.parent/'figures';F.mkdir(exist_ok=True)
d=pd.read_csv(R/'major_revision_metrics.csv')
fig,ax=plt.subplots(figsize=(7.1,3.3))
rows=d[(d.train=='complete_frozen')&(d.test=='complete')&(d.model.isin(['LR','HGB']))]
for model,ss in rows.groupby('model'):
 ax.plot(ss.fold.to_numpy()+1,ss.average_precision.to_numpy(),'o-',label=model)
ax.set(xlabel='Held-out scenario fold',ylabel='Average precision',xticks=[1,2,3,4],ylim=(.73,1.01))
ax.legend(loc='lower right');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(F/'fourfold_models.pdf',bbox_inches='tight');plt.close(fig)

df=pd.read_csv(R/'fourfold_matched_frozen_mixed.csv')
fig,axes=plt.subplots(1,2,figsize=(9,3.4),sharey=True)
reg=['delay_20ms','sample_every_8','missing_30pct']
for ax,model in zip(axes,['LR','HGB']):
 sub=df[(df.model==model)&(df.test.isin(reg))];x=np.arange(3)
 for off,name,lab in [(-.24,'complete_frozen','Frozen'),(0,'matched','Matched'),(.24,'mixed_equal_packet_count','Mixed')]:
  vals=[float(sub[(sub.test==k)&(sub.train==name)]['mean'].iloc[0]) for k in reg]
  ax.bar(x+off, vals, .23,label=lab)
 ax.set(title=model,xticks=x,xticklabels=['20-ms delay','Every 8th','30% missing'],ylim=(0,1.03))
 ax.grid(axis='y',alpha=.2);ax.tick_params(axis='x',labelrotation=16)
axes[0].set_ylabel('Mean fold average precision');axes[1].legend(fontsize=7,loc='lower left')
fig.tight_layout();fig.savefig(F/'fourfold_regime_training.pdf',bbox_inches='tight');plt.close(fig)

b=pd.read_csv(R/'operational_budgets_fourfold.csv');fig,ax=plt.subplots(figsize=(6.5,3))
for m,s in b.groupby('model'):
 mean=s.groupby('budget').alert_precision.mean()
 ax.plot(mean.index*100,mean.values,'o-',label=m)
ax.set(xlabel='Alert budget (% of test packets)',ylabel='Precision among alerted packets',xticks=[5,10,20],ylim=(.65,1.03))
ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(F/'fourfold_alert_precision.pdf',bbox_inches='tight');plt.close(fig)
