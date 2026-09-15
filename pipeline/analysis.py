import json, datetime as dt
import numpy as np

EPOCH = dt.date(2003,1,1)
A = np.load('daily_agg.npz')
decay, DEC = A['decay'], A['decays']
prov, pidx = A['prov'], A['prov_idx']
pnames = json.load(open('prov_names.json'))
ndays = decay.shape[0]
dates = [EPOCH+dt.timedelta(days=i) for i in range(ndays)]

psi = json.load(open('psi_daily.json'))
y = np.full(ndays, np.nan); ymax = np.full(ndays, np.nan)
for k,v in psi.items():
    d = dt.date(*[int(x) for x in k.split('-')])
    i = (d-EPOCH).days
    if 0 <= i < ndays and v['n'] >= 12:
        y[i] = v['mean']; ymax[i] = v['max']

obs = ~np.isnan(y)
print('PSI days', obs.sum(), dates[np.where(obs)[0][0]], '->', dates[np.where(obs)[0][-1]])

def r2(a,b):
    m = ~np.isnan(a) & ~np.isnan(b)
    if m.sum() < 30: return np.nan
    return np.corrcoef(a[m],b[m])[0,1]

# ---------- 1. grid search L, lag, power ----------
best = None
for j,L in enumerate(DEC):
    x0 = decay[:,j]/1e3            # kilotonnes-effective
    for lag in range(0,9):
        x = np.roll(x0, lag); x[:lag] = np.nan
        for p in (0.25,0.33,0.5,0.75,1.0):
            xp = np.where(np.isnan(x), np.nan, np.power(np.clip(x,0,None), p))
            r = r2(xp, y)
            if r == r or True:
                if best is None or (r > best[0]): best = (r, L, lag, p, j)
print('best all-days:', best[:4])

# season-only (Jun-Nov) fit
seas = np.array([d.month in (6,7,8,9,10,11) for d in dates])
bests = None
for j,L in enumerate(DEC):
    x0 = decay[:,j]/1e3
    for lag in range(0,9):
        x = np.roll(x0, lag); x[:lag] = np.nan
        for p in (0.25,0.33,0.5,0.75,1.0):
            xp = np.power(np.clip(x,0,None), p)
            a=np.where(seas,xp,np.nan); b=np.where(seas,y,np.nan)
            r = r2(a,b)
            if bests is None or r > bests[0]: bests = (r,L,lag,p,j)
print('best season-only:', bests[:4])

R, L, LAG, P, J = bests
HPI = decay[:,J]/1e3
X = np.roll(HPI, LAG); X[:LAG] = np.nan
XP = np.power(np.clip(X,0,None), P)

# ---------- 2. leave-one-year-out skill ----------
years = np.array([d.year for d in dates])
mask = obs & seas & ~np.isnan(XP)
res = {}
for yr in range(2014,2027):
    tr = mask & (years != yr); te = mask & (years == yr)
    if te.sum() < 20 or tr.sum() < 200: continue
    A1 = np.c_[np.ones(tr.sum()), XP[tr]]
    coef, *_ = np.linalg.lstsq(A1, y[tr], rcond=None)
    pred = coef[0] + coef[1]*XP[te]
    ss = 1 - np.sum((y[te]-pred)**2)/np.sum((y[te]-y[te].mean())**2)
    res[yr] = (float(ss), float(np.corrcoef(pred,y[te])[0,1]), int(te.sum()))
print('leave-one-year-out R2:', {k:(round(v[0],2),round(v[1],2),v[2]) for k,v in res.items()})

A1 = np.c_[np.ones(mask.sum()), XP[mask]]
COEF, *_ = np.linalg.lstsq(A1, y[mask], rcond=None)
print('global fit PSI = %.2f + %.4f * HPI^%.2f (L=%dkm, lag=%dd), r=%.3f'%(COEF[0],COEF[1],P,L,LAG,R))

# ---------- 3. per-province lag curves ----------
want = {'IDN.024':'Riau','IDN.008':'Jambi','IDN.031':'South Sumatra','IDN.032':'West Sumatra',
        'IDN.012':'Lampung','IDN.014':'West Kalimantan','IDN.013':'Central Kalimantan',
        'IDN.011':'South Kalimantan','IDN.015':'East Kalimantan','MYS.':'',}
prov_curves={}
for i,u in enumerate(pidx):
    code,name,parent = pnames[str(u)]
    if code in want or (parent=='IDN' and prov[i][seas&obs].sum()>0):
        lab = want.get(code, name)
        s = prov[i]
        tot = s[mask].sum()
        if tot < 1e5: continue
        curve=[]
        for lag in range(0,9):
            xs = np.roll(s,lag); xs[:lag]=np.nan
            curve.append(r2(np.where(mask, np.power(np.clip(xs,0,None),P), np.nan), np.where(mask,y,np.nan)))
        prov_curves[f'{name} ({code})'] = (curve, float(tot))
top = sorted(prov_curves.items(), key=lambda kv:-max([c for c in kv[1][0] if c==c] or [0]))[:8]
for k,(c,t) in top:
    b=int(np.nanargmax(c)); print(f'{k:38s} best lag {b}d  r={c[b]:.3f}')

np.savez('fit.npz', HPI=HPI, XP=XP, y=y, ymax=ymax, mask=mask, seas=seas, obs=obs,
         COEF=COEF, L=L, LAG=LAG, P=P, R=R)
json.dump({'loyo':res,'best':[float(R),int(L),int(LAG),float(P)],
           'coef':[float(c) for c in COEF],
           'prov':{k:[[None if c!=c else float(c) for c in v[0]], v[1]] for k,v in prov_curves.items()}},
          open('fit.json','w'))
print('saved')
