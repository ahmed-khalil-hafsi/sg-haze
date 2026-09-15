import json, urllib.request, os
from concurrent.futures import ThreadPoolExecutor
m=json.load(open('manifest.json'))
base='https://sites.ecmwf.int/data/cams/products/gfas/v2_gisco_fp/'
os.makedirs('gfas/pixels',exist_ok=True)
items=[(base+p['path'], 'gfas/pixels/%d_%02d.parquet'%(p['year'],p['month']), p['bytes']) for p in m['variables']['cfire']['pixels']]
def get(it):
    u,o,b=it
    if os.path.exists(o) and abs(os.path.getsize(o)-b)<64: return 0
    urllib.request.urlretrieve(u,o); return 1
with ThreadPoolExecutor(12) as ex: r=list(ex.map(get,items))
print('downloaded',sum(r),'of',len(items))
