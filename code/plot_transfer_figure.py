#!/usr/bin/env python3
"""Generate a figure from recorded CSV results (no model execution)."""
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
frozen=pd.read_csv(root/'results/cross_regime_transfer.csv')
matched=pd.read_csv(root/'results/model_metrics.csv')
matched=matched[matched.method=='causal_history']
labels=['complete','delay_8ms','delay_20ms','sample_every_8','missing_30pct']
fd=frozen.groupby('telemetry').pr_auc.mean().reindex(labels)
md=matched.groupby('telemetry').pr_auc.mean().reindex(labels)
xs=np.arange(len(labels))
fig,ax=plt.subplots(figsize=(6.2,3.6))
ax.plot(xs,md.values,marker='o',linewidth=2,label='Train/test matched reporting')
ax.plot(xs,fd.values,marker='s',linewidth=2,label='Frozen complete-feedback model')
ax.set_xticks(xs,['Complete','8-ms lag','20-ms lag','Every 8th','30% missing'],fontsize=8)
ax.set_ylim(0.55,1.01)
ax.set_ylabel('PR-AUC on group-held-out configurations')
ax.legend(fontsize=8,loc='lower left')
ax.grid(alpha=.2)
fig.tight_layout()
for ext in ('pdf','png'):
 fig.savefig(root/'figures'/('frozen_transfer.'+ext),dpi=200,bbox_inches='tight')
plt.close(fig)
