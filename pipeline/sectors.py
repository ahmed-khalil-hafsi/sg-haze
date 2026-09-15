import json, datetime as dt, numpy as np
from scipy.optimize import nnls

EPOCH=dt.date(2003,1,1)
A=np.load('daily_agg.npz'); RS=A['ringsec']; RINGS=A['rings']; NSEC=int(A['nsec'])
NR=len(RINGS)-1
nd=RS.shape[0]; dates=[EPOCH+dt.timedelta(days=i) for i in range(nd)]
psi=json.load(open('psi_daily.json'))
y=np.full(nd,np.nan)
for k,v in psi.items():
    d=dt.date(*[int(x) for x in k.split('-')]); i=(d-EPOCH).days
    if 0<=i<nd and v['n']>=12: y[i]=v['mean']
seas=np.array([d.month in (6,7,8,9,10,11) for d in dates])
obs=~np.isnan(y)

RS3=RS.reshape(nd,NR,NSEC)
# per-ring best lag
lags=[]
for r in range(NR):
    s=RS3[:,r,:].sum(1); bestr,bl=-9,0
    for lag in range(0,7):
        x=np.roll(s,lag); x[:lag]=np.nan
        m=obs&seas&~np.isnan(x)
        if m.sum()<200: continue
        c=np.corrcoef(np.sqrt(x[m]),y[m])[0,1]
        if c>bestr: bestr,bl=c,lag
    lags.append(bl)
    print(f'ring {RINGS[r]}-{RINGS[r+1]} km: best lag {bl} d, r={bestr:.3f}, season total {s[seas].sum()/1e6:.1f} Mt')

X=np.zeros((nd,NR*NSEC))
for r in range(NR):
    lg=lags[r]
    blk=np.roll(RS3[:,r,:],lg,axis=0); blk[:lg]=np.nan
    X[:,r*NSEC:(r+1)*NSEC]=np.sqrt(np.clip(blk,0,None))
m=obs&seas&~np.isnan(X).any(1)
Xf=np.c_[np.ones(m.sum()),X[m]]; yf=y[m]
lam=np.sqrt(50.0)
Xa=np.vstack([Xf, lam*np.eye(Xf.shape[1])]); Xa[Xf.shape[0],0]=0
ya=np.r_[yf, np.zeros(Xf.shape[1])]
beta,_=nnls(Xa,ya)
pred=Xf@beta
print('in-sample r=%.3f R2=%.3f  intercept=%.1f'%(np.corrcoef(pred,yf)[0,1],1-((yf-pred)**2).sum()/((yf-yf.mean())**2).sum(),beta[0]))

contrib=beta[1:]*X[m].mean(0)
C=contrib.reshape(NR,NSEC)
comp=['N','NE','E','SE','S','SW','W','NW']
print('\ncontribution to mean season PSI (index points):')
print('ring'.ljust(14)+''.join(c.rjust(7) for c in comp))
for r in range(NR):
    print(f'{RINGS[r]}-{RINGS[r+1]}km'.ljust(14)+''.join(f'{C[r,s]:7.2f}' for s in range(NSEC)))
print('total explained above baseline: %.1f PSI pts'%C.sum())
np.savez('sectors.npz',C=C,beta=beta,lags=np.array(lags),rings=RINGS,nsec=NSEC,pred=pred,yf=yf)
