"""Forecast-honest evaluation: nested leave-one-season-out CV with structure
re-selected inside each fold, lag >= 1 day, against persistence and AR(1),
plus season-block bootstrap intervals. Writes evaluation.json."""
import json, datetime as dt, numpy as np
from scipy.optimize import nnls

E = dt.date(2003, 1, 1)
A = np.load('daily_agg.npz'); DEC = A['decays']; D = A['decay'] / 1e3
RS = A['ringsec']; RINGS = A['rings']; NSEC = int(A['nsec']); NR = len(RINGS) - 1
nd = D.shape[0]; dates = [E + dt.timedelta(days=i) for i in range(nd)]
yrs = np.array([d.year for d in dates]); seas = np.array([d.month in (6,7,8,9,10,11) for d in dates])
y = np.full(nd, np.nan)
for k, v in json.load(open('psi_daily.json')).items():
    i = (dt.date.fromisoformat(k) - E).days
    if 0 <= i < nd and v['n'] >= 12: y[i] = v['mean']
y1 = np.roll(y, 1); y1[0] = np.nan
rng = np.random.default_rng(20260915)
SEASONS = list(range(2014, 2027))

def feat(j, lag, p):
    x = np.roll(D[:, j], lag); x[:lag] = np.nan
    return np.power(np.clip(x, 0, None), p)
FE = {(j, l, p): feat(j, l, p) for j in range(len(DEC)) for l in range(1, 6) for p in (0.33, 0.5, 0.75, 1.0)}
base = seas & ~np.isnan(y) & ~np.isnan(y1)
X1 = lambda *cols: np.c_[np.ones(len(cols[0])), np.column_stack(cols)]
ols = lambda X, t: np.linalg.lstsq(X, t, rcond=None)[0]
r2 = lambda t, p: 1 - ((t - p) ** 2).sum() / ((t - t.mean()) ** 2).sum()

preds = {m: np.full(nd, np.nan) for m in ('persist', 'ar1', 'index', 'ar1_index')}
chosen = {}
for yr in SEASONS:
    tr = base & (yrs != yr); te = base & (yrs == yr)
    bi = max(FE, key=lambda k: np.corrcoef(FE[k][tr & ~np.isnan(FE[k])], y[tr & ~np.isnan(FE[k])])[0, 1])
    def fit_both(k):
        m = tr & ~np.isnan(FE[k]); c = ols(X1(y1[m], FE[k][m]), y[m])
        return r2(y[m], X1(y1[m], FE[k][m]) @ c), c
    bb = max(FE, key=lambda k: fit_both(k)[0])
    x = FE[bi]; m = tr & ~np.isnan(x)
    preds['index'][te] = X1(x[te]) @ ols(X1(x[m]), y[m])
    preds['persist'][te] = y1[te]
    preds['ar1'][te] = X1(y1[te]) @ ols(X1(y1[tr]), y[tr])
    _, c = fit_both(bb); preds['ar1_index'][te] = X1(y1[te], FE[bb][te]) @ c
    chosen[yr] = {'index': [int(DEC[bi[0]]), bi[1], bi[2]], 'ar1_index': [int(DEC[bb[0]]), bb[1], bb[2]]}

def metrics(mask):
    t = y[mask]; out = {}
    for mname, p in preds.items():
        out[mname] = {'r2': float(r2(t, p[mask])), 'rmse': float(np.sqrt(((t - p[mask]) ** 2).mean()))}
    return out
per_season = {yr: metrics(base & (yrs == yr)) for yr in SEASONS}
pooled = metrics(base)
HAZE = [2014, 2015, 2019, 2023, 2026]
haze = metrics(base & np.isin(yrs, HAZE))

# season-block bootstrap of pooled RMSE gain (AR1 -> AR1+index) and of R2
B = 2000; gains = []; r2_idx = []; r2_ar = []; r2_both = []
for _ in range(B):
    s = rng.choice(SEASONS, size=len(SEASONS), replace=True)
    idx = np.concatenate([np.where(base & (yrs == q))[0] for q in s]); t = y[idx]
    ra = np.sqrt(((t - preds['ar1'][idx]) ** 2).mean()); rb = np.sqrt(((t - preds['ar1_index'][idx]) ** 2).mean())
    gains.append((ra - rb) / ra * 100)
    r2_idx.append(r2(t, preds['index'][idx])); r2_ar.append(r2(t, preds['ar1'][idx])); r2_both.append(r2(t, preds['ar1_index'][idx]))
ci = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]

# season-block bootstrap of the NNLS source apportionment (lags fixed per ring)
RS3 = RS.reshape(nd, NR, NSEC); lags = []
for r in range(NR):
    s = RS3[:, r, :].sum(1); best = (-9, 0)
    for lag in range(1, 7):
        x = np.roll(s, lag); x[:lag] = np.nan; m = base & ~np.isnan(x)
        best = max(best, (np.corrcoef(np.sqrt(x[m]), y[m])[0, 1], lag))
    lags.append(best[1])
Xs = np.zeros((nd, NR * NSEC))
for r in range(NR):
    blk = np.roll(RS3[:, r, :], lags[r], axis=0); blk[:lags[r]] = np.nan
    Xs[:, r * NSEC:(r + 1) * NSEC] = np.sqrt(np.clip(blk, 0, None))
okX = base & ~np.isnan(Xs).any(1)
def apportion(rows):
    Xf = np.c_[np.ones(len(rows)), Xs[rows]]; lam = np.sqrt(50.0)
    Xa = np.vstack([Xf, lam * np.eye(Xf.shape[1])]); Xa[len(rows), 0] = 0
    b, _ = nnls(Xa, np.r_[y[rows], np.zeros(Xf.shape[1])])
    return (b[1:] * Xs[rows].mean(0)).reshape(NR, NSEC)
Cfull = apportion(np.where(okX)[0])
share = lambda C: float(C[1:4, [3, 4]].sum() / C.sum()) if C.sum() > 0 else np.nan
shares = []; topbin = []
for _ in range(500):
    s = rng.choice(SEASONS, size=len(SEASONS), replace=True)
    rows = np.concatenate([np.where(okX & (yrs == q))[0] for q in s]); C = apportion(rows)
    shares.append(share(C)); topbin.append(int(np.argmax(C)))
names = ['N','NE','E','SE','S','SW','W','NW']
tb = np.bincount(topbin, minlength=NR * NSEC) / len(topbin)
top3 = [{'bin': f"{names[i % NSEC]} {RINGS[i // NSEC]}-{RINGS[i // NSEC + 1]} km", 'freq': float(tb[i])} for i in np.argsort(tb)[::-1][:3]]

# province lag correlations with season-block CI: South Sumatra vs Central Kalimantan
P = A['prov']; PI = list(A['prov_idx']); RI = json.load(open('region_index.json'))
def pidx(code): return PI.index(RI['admin1'].index(code))
def corr_at(series, rows, lag=1):
    x = np.roll(series, lag); x[:lag] = np.nan; m = rows[~np.isnan(x[rows])]
    return np.corrcoef(np.sqrt(np.clip(x[m], 0, None)), y[m])[0, 1]
ss, ck = P[pidx('IDN.031')], P[pidx('IDN.014')]
allrows = np.where(base)[0]; diffs = []
for _ in range(1000):
    s = rng.choice(SEASONS, size=len(SEASONS), replace=True)
    rows = np.concatenate([np.where(base & (yrs == q))[0] for q in s])
    diffs.append(corr_at(ss, rows, 1) - corr_at(ck, rows, 3))

out = {
  'per_season': per_season, 'pooled': pooled, 'haze_seasons': haze, 'haze_list': HAZE, 'chosen': chosen,
  'bootstrap': {'B': B, 'rmse_gain_pct_ar1_to_ar1_index': {'mean': float(np.mean(gains)), 'ci95': ci(gains),
                'p_gain_le_0': float(np.mean(np.array(gains) <= 0))},
                'r2_index_ci95': ci(r2_idx), 'r2_ar1_ci95': ci(r2_ar), 'r2_ar1_index_ci95': ci(r2_both)},
  'apportionment': {'lags': lags, 'se_s_250_1200_share': share(Cfull), 'share_ci95': ci(shares), 'top_bin_freq': top3},
  'province': {'r_south_sumatra_lag1': float(corr_at(ss, allrows, 1)), 'r_central_kalimantan_lag3': float(corr_at(ck, allrows, 3)),
               'diff_ci95': ci(diffs), 'p_diff_le_0': float(np.mean(np.array(diffs) <= 0))},
}
json.dump(out, open('evaluation.json', 'w'), indent=1)
f = lambda d: f"R2 {d['r2']:.3f}  RMSE {d['rmse']:.2f}"
print('POOLED     ', {k: f(v) for k, v in pooled.items()})
print('HAZE       ', {k: f(v) for k, v in haze.items()})
print('RMSE gain AR1->AR1+idx: %.1f%%  CI %s  P(gain<=0)=%.3f' % (np.mean(gains), [round(v,1) for v in ci(gains)], np.mean(np.array(gains)<=0)))
print('R2 CI  index', [round(v,2) for v in ci(r2_idx)], ' ar1', [round(v,2) for v in ci(r2_ar)], ' both', [round(v,2) for v in ci(r2_both)])
print('S/SE 250-1200 share %.2f  CI %s' % (share(Cfull), [round(v,2) for v in ci(shares)]), ' top bins', top3)
print('SSumatra r=%.3f  CKalimantan r=%.3f  diff CI %s  P(diff<=0)=%.3f' % (out['province']['r_south_sumatra_lag1'], out['province']['r_central_kalimantan_lag3'], [round(v,3) for v in ci(diffs)], out['province']['p_diff_le_0']))
for yr in SEASONS:
    p = per_season[yr]; print(yr, ' '.join(f"{m}:{p[m]['r2']:.2f}/{p[m]['rmse']:.1f}" for m in ('persist','ar1','index','ar1_index')))
