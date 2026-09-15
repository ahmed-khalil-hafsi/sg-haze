import json, glob, datetime as dt
import numpy as np, pyarrow.parquet as pq

SG_LON, SG_LAT = 103.82, 1.35
EPOCH = dt.date(2003,1,1)
LON0, LAT0, RES = -179.95, -89.95, 0.1
RI = json.load(open('region_index.json'))
a1, a1n, a1p = RI['admin1'], RI['admin1_names'], RI['admin1_parent']

RINGS = [0,250,500,800,1200,1800]
SECTORS = 8            # 45-degree sectors, sector 0 centred on North
DECAYS = [150,250,400,600,900,1400]
KEY_PROV = ['IDN.024','IDN.008','IDN.031','IDN.026','IDN.012','IDN.001','IDN.002',   # Riau, Jambi, S.Sumatra, Sumatera Barat?, Lampung.., placeholders resolved below
            ]

ndays = (dt.date(2026,9,13)-EPOCH).days + 1
nring, nsec = len(RINGS)-1, SECTORS
ringsec = np.zeros((ndays, nring*nsec))
decay   = np.zeros((ndays, len(DECAYS)))
# province accumulator: dict idx -> array
prov = {}

def hav(lon, lat):
    p1, p2 = np.deg2rad(SG_LAT), np.deg2rad(lat)
    dl = np.deg2rad(lon-SG_LON); dp = p2-p1
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 6371.0*2*np.arcsin(np.sqrt(a))

def bearing(lon, lat):
    p1, p2 = np.deg2rad(SG_LAT), np.deg2rad(lat)
    dl = np.deg2rad(lon-SG_LON)
    y = np.sin(dl)*np.cos(p2)
    x = np.cos(p1)*np.sin(p2)-np.sin(p1)*np.cos(p2)*np.cos(dl)
    return (np.degrees(np.arctan2(y,x))+360) % 360

files = sorted(glob.glob('gfas/pixels/*.parquet'))
for f in files:
    t = pq.read_table(f).to_pydict()
    day = np.array(t['day_idx'], dtype=np.int64)
    lon = LON0 + RES*np.array(t['lon_idx'], dtype=float)
    lat = LAT0 + RES*np.array(t['lat_idx'], dtype=float)
    val = np.array(t['value'], dtype=float)
    reg = np.array(t['region_idx'], dtype=np.int64)
    # coarse pre-filter: within ~2000 km box of Singapore
    k = (lon > 84) & (lon < 124) & (lat > -17) & (lat < 20)
    if not k.any(): continue
    day, lon, lat, val, reg = day[k], lon[k], lat[k], val[k], reg[k]
    r = hav(lon, lat); b = bearing(lon, lat)
    k = (r <= RINGS[-1]) & (day < ndays)
    day, val, reg, r, b = day[k], val[k], reg[k], r[k], b[k]
    ri = np.clip(np.digitize(r, RINGS)-1, 0, nring-1)
    si = (((b+22.5) % 360)//45).astype(int)
    cell = ri*nsec + si
    np.add.at(ringsec, (day, cell), val)
    for j, L in enumerate(DECAYS):
        np.add.at(decay, (day, np.full(day.shape, j)), val*np.exp(-r/L))
    for u in np.unique(reg):
        m = reg == u
        if u not in prov: prov[u] = np.zeros(ndays)
        np.add.at(prov[u], day[m], val[m])

keep = {int(u): arr for u, arr in prov.items() if arr.sum() > 5e4}
names = {int(u): (a1[u] if u < len(a1) else str(u), a1n[u] if u < len(a1n) else '?', a1p[u] if u < len(a1p) else '?') for u in keep}
np.savez_compressed('daily_agg.npz',
                    ringsec=ringsec, decay=decay,
                    rings=np.array(RINGS), decays=np.array(DECAYS), nsec=nsec,
                    prov_idx=np.array(sorted(keep)),
                    prov=np.array([keep[u] for u in sorted(keep)]))
json.dump({str(u): names[u] for u in sorted(keep)}, open('prov_names.json','w'))
print('days', ndays, 'provinces kept', len(keep))
print('total within 1800km, 2026-09-13:', ringsec[(dt.date(2026,9,13)-EPOCH).days].sum())
