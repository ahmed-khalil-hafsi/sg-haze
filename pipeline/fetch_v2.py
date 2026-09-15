"""Fetch v2 inputs: ERA5 850 hPa wind + precipitation (Open-Meteo archive),
CAMS PM2.5 forecast at Singapore (Open-Meteo air quality), NEA PM2.5 archive."""
import json, math, time, urllib.request, urllib.parse, csv, io, os, datetime as dt
UA = {"User-Agent": "sg-haze research fetch (github.com/ahmed-khalil-hafsi/sg-haze)"}
SG = (1.35, 103.82)
os.makedirs("v2", exist_ok=True)

def get(url, tries=5):
    for a in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception as e:
            last = e; time.sleep(5 + 10 * a)
    raise RuntimeError(f"{url[:120]}: {last}")

def dest(lat, lon, bearing_deg, km):
    R = 6371.0; d = km / R; th = math.radians(bearing_deg); p1 = math.radians(lat); l1 = math.radians(lon)
    p2 = math.asin(math.sin(p1)*math.cos(d) + math.cos(p1)*math.sin(d)*math.cos(th))
    l2 = l1 + math.atan2(math.sin(th)*math.sin(d)*math.cos(p1), math.cos(d) - math.sin(p1)*math.sin(p2))
    return round(math.degrees(p2), 4), round(math.degrees(l2), 4)

points = [SG] + [dest(*SG, s * 45, 400) for s in range(8)]
json.dump({"points": points, "note": "index 0 = Singapore; 1..8 = sectors N,NE,E,SE,S,SW,W,NW at 400 km"}, open("v2/points.json", "w"))

# ---- A. ERA5 wind + precip --------------------------------------------------
model_used = None
for yr in range(2014, 2027):
    out = f"v2/era5_{yr}.json"
    if os.path.exists(out): continue
    start, end = f"{yr}-05-25", (f"{yr}-11-30" if yr < 2026 else "2026-09-14")
    q = {"latitude": ",".join(str(p[0]) for p in points), "longitude": ",".join(str(p[1]) for p in points),
         "start_date": start, "end_date": end, "wind_speed_unit": "ms", "timezone": "UTC",
         "hourly": "wind_speed_100m,wind_direction_100m,precipitation"}  # deviation D1: 850 hPa unavailable
    for model in (["era5"] if model_used in (None, "era5") else []) + ["best_match"]:
        qq = dict(q, models=model)
        try:
            raw = json.loads(get("https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(qq)))
            locs = raw if isinstance(raw, list) else [raw]
            ok = all(sum(v is not None for v in L["hourly"]["wind_speed_100m"]) > 0.95 * len(L["hourly"]["time"]) for L in locs)
            if ok:
                model_used = model_used or model
                json.dump({"model": model, "locations": locs}, open(out, "w")); print(f"ERA5 {yr}: {model}, {len(locs)} points"); break
            print(f"ERA5 {yr}: model {model} returned incomplete 100 m wind, trying next")
        except Exception as e:
            print(f"ERA5 {yr}: model {model} failed: {str(e)[:100]}")
    time.sleep(3)

# ---- B. CAMS PM2.5 forecast at Singapore ------------------------------------
if not os.path.exists("v2/cams_pm25.json"):
    q = {"latitude": SG[0], "longitude": SG[1], "hourly": "pm2_5", "timezone": "Asia/Singapore",
         "start_date": "2022-06-01", "end_date": "2026-09-14"}
    raw = json.loads(get("https://air-quality-api.open-meteo.com/v1/air-quality?" + urllib.parse.urlencode(q)))
    json.dump(raw, open("v2/cams_pm25.json", "w"))
    v = [x for x in raw["hourly"]["pm2_5"] if x is not None]
    print(f"CAMS: {len(v)} hourly values, {raw['hourly']['time'][0]} .. {raw['hourly']['time'][-1]}")

# ---- C. NEA PM2.5 historical archive (2016-2024) ----------------------------
meta = json.loads(get("https://api-production.data.gov.sg/v2/public/api/collections/2215/metadata"))
kids = meta["data"]["collectionMetadata"]["childDatasets"]
for did in kids:
    out = f"v2/nea_{did}.csv"
    if os.path.exists(out): continue
    poll = json.loads(get(f"https://api-open.data.gov.sg/v1/public/api/datasets/{did}/poll-download"))
    url = poll["data"]["url"]
    open(out, "wb").write(get(url))
    head = open(out).readline().strip()
    first = open(out).readlines()[1][:40]
    print(f"NEA {did}: {os.path.getsize(out)//1024} KB, first row {first!r}")
    time.sleep(4)
print("FETCH_V2_DONE")
