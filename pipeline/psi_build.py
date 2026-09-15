import csv, json, datetime as dt, numpy as np

rows={}
with open('psi_24h.csv') as f:
    r=csv.DictReader(f)
    for x in r:
        ts=x['24hr_psi']
        try:
            d,tm=ts.split(' ')
            dd,mm,yy=[int(v) for v in d.split('/')]
            day=dt.date(yy,mm,dd)
        except Exception: continue
        vals=[]
        for k in ('north','south','east','west','central'):
            v=x.get(k,'')
            try: vals.append(float(v))
            except: pass
        if vals: rows.setdefault(day,[]).append(vals)

# recent from API
import glob, os
rec={}
for p in sorted(glob.glob('psi_days/*.json')):
    try:
        j=json.load(open(p))
    except Exception:
        continue
    if j.get('code')==0:
        rec[os.path.basename(p)[:-5]]=j['data']['items']
for ds,items in rec.items():
    day=dt.date(*[int(v) for v in ds.split('-')])
    for it in items:
        rd=it.get('readings',{}).get('psi_twenty_four_hourly',{})
        vals=[float(v) for k,v in rd.items() if k in ('north','south','east','west','central') and v is not None]
        if vals: rows.setdefault(day,[]).append(vals)

days=sorted(rows)
out={}
for d in days:
    arr=np.array(rows[d],dtype=float)          # hours x regions
    out[d.isoformat()]={'mean':float(arr.mean()),
                        'max':float(arr.max()),
                        'natmax_mean':float(arr.max(axis=1).mean()),
                        'n':int(arr.shape[0])}
json.dump(out,open('psi_daily.json','w'))
print('days',len(out), days[0], days[-1])
import collections
yrs=collections.Counter(d.year for d in days)
print(sorted(yrs.items()))
