"""Figure: out-of-sample R^2 by season for persistence, AR(1), index, AR(1)+index."""
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
matplotlib.rcParams.update({'font.family':'serif','font.serif':['DejaVu Serif'],'savefig.facecolor':'#ffffff'})
ev=json.load(open('evaluation.json')); S=sorted(int(k) for k in ev['per_season'])
models=[('persist','Persistence','#bdbdbd'),('ar1','AR(1)','#6b6b6b'),('index','Index alone','#d95f02'),('ar1_index','AR(1) + index','#08519c')]
fig,ax=plt.subplots(figsize=(13,5.6),dpi=150)
w=.2; x=np.arange(len(S)+1)
for i,(k,lab,c) in enumerate(models):
    v=[ev['per_season'][str(s)][k]['r2'] for s in S]+[ev['pooled'][k]['r2']]
    ax.bar(x+(i-1.5)*w,v,w*.92,color=c,label=lab,zorder=3)
ax.axhline(0,color='#000',lw=.8); ax.axvline(len(S)-.5,color='#999',lw=.8,ls=':')
ax.set_xticks(x); ax.set_xticklabels([str(s) for s in S]+['pooled'],fontsize=10)
for s_,lbl in zip(S,S):
    if s_ in ev['haze_list']: ax.get_xticklabels()[S.index(s_)].set_fontweight('bold')
ax.set_ylabel('Out-of-sample $R^2$ (held-out season)',fontsize=11); ax.set_ylim(-.4,.9)
ax.grid(axis='y',color='#e0e0e0',zorder=0); ax.spines[['top','right']].set_visible(False)
ax.legend(frameon=False,ncol=4,loc='upper left',fontsize=10)
b=ev['bootstrap']['rmse_gain_pct_ar1_to_ar1_index']
ax.set_title('Nested leave-one-season-out skill, June-November (bold: fire-affected seasons)',fontsize=12,loc='left')
fig.text(.01,.01,f"Structure (L, lag >= 1 d, exponent) re-selected within each fold. Pooled RMSE reduction of AR(1)+index over AR(1): {b['mean']:.1f}% (95% CI {b['ci95'][0]:.1f}-{b['ci95'][1]:.1f}%, season-block bootstrap, B={ev['bootstrap']['B']}).",fontsize=8.5,color='#444')
fig.tight_layout(rect=(0,.04,1,1)); fig.savefig('fig_skill.png'); print('fig_skill ok')
