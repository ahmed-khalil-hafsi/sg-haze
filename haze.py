#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pyarrow"]
# ///
"""
haze.py - Singapore haze check.
Author: Ahmed Khalil Hafsi

Pulls the latest CAMS GFAS daily wildfire emissions, turns them into a
distance-weighted "haze pressure index" for Singapore, converts that to an
implied 24-hr PSI, and compares against what NEA actually measured.

  ./haze.py                 last 7 days + outlook + top sources + season rank
  ./haze.py --days 14       longer history
  ./haze.py --no-psi        skip the NEA lookup (no network calls to data.gov.sg)
  ./haze.py --json          machine-readable output
  ./haze.py --refresh       ignore cached GFAS/PSI files and re-download

Model (baked into baseline.json, fitted on Jun-Nov 2014-2026):
    PSI = a + b * index^0.5,  index = sum(emissions * exp(-km/900)), lagged 1 day
In-sample r = 0.72, but under nested cross-validation the index alone does not
beat persistence (out-of-sample R^2 0.43 vs 0.67). Added to yesterday's PSI it
cuts forecast error by only ~3.6%. Treat "implied PSI" as a fire-signal gauge,
not a forecast. Details: paper/paper.pdf.

Data: sites.ecmwf.int/data/cams/products/gfas (CAMS GFAS v2, ECMWF/Copernicus)
      api-open.data.gov.sg real-time PSI (NEA)
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, sys, time, urllib.request, urllib.error

BASE = "https://sites.ecmwf.int/data/cams/products/gfas/v2_gisco_fp/"
PSI_API = "https://api-open.data.gov.sg/v2/real-time/api/psi?date={}"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
UA = {"User-Agent": "haze.py/1.0 (personal air-quality check)"}
EPOCH = dt.date(2003, 1, 1)

C = {"dim": "\033[2m", "b": "\033[1m", "r": "\033[0m", "cy": "\033[36m",
     "or": "\033[38;5;208m", "gn": "\033[32m", "yl": "\033[33m", "rd": "\033[31m"}
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C = {k: "" for k in C}


def get(url: str, dest: str | None = None, refresh: bool = False, tries: int = 4):
    """Fetch a URL, optionally caching to disk. Returns bytes."""
    if dest and os.path.exists(dest) and not refresh and os.path.getsize(dest) > 0:
        return open(dest, "rb").read()
    last = None
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            if dest:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(data)
            return data
        except Exception as e:                      # noqa: BLE001
            last = e
            time.sleep(1.5 + 3 * a)
    raise RuntimeError(f"could not fetch {url}: {last}")


def haversine_km(lon, lat, sg_lon, sg_lat):
    import numpy as np
    p1, p2 = np.deg2rad(sg_lat), np.deg2rad(lat)
    dl, dp = np.deg2rad(lon - sg_lon), p2 - p1
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def compass(lon, lat, sg_lon, sg_lat):
    import numpy as np
    p1, p2 = np.deg2rad(sg_lat), np.deg2rad(lat)
    dl = np.deg2rad(lon - sg_lon)
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    b = (np.degrees(np.arctan2(y, x)) + 360) % 360
    names = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
             "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return b, [names[int(((v + 11.25) % 360) // 22.5)] for v in np.atleast_1d(b)]


def load_gfas(months, refresh):
    """Return (day_idx, lon, lat, tonnes, region_idx) for the given (year, month) list."""
    import numpy as np, pyarrow.parquet as pq
    cols = {k: [] for k in ("day", "lon", "lat", "val", "reg")}
    for (yr, mo) in months:
        path = f"pixels/cfire/{yr}/{mo:02d}.parquet"
        dest = os.path.join(CACHE, f"{yr}_{mo:02d}.parquet")
        # the current month's file changes daily; always refresh it
        cur = (yr, mo) == (months[-1][0], months[-1][1])
        raw = get(BASE + path, dest, refresh=refresh or cur)
        t = pq.read_table(dest).to_pydict()
        cols["day"].append(np.asarray(t["day_idx"], dtype=np.int64))
        cols["lon"].append(np.asarray(t["lon_idx"], dtype=np.float64))
        cols["lat"].append(np.asarray(t["lat_idx"], dtype=np.float64))
        cols["val"].append(np.asarray(t["value"], dtype=np.float64))
        cols["reg"].append(np.asarray(t["region_idx"], dtype=np.int64))
    return [np.concatenate(cols[k]) for k in ("day", "lon", "lat", "val", "reg")]


def fetch_psi(days, refresh):
    """{date -> mean 24-hr PSI across the 5 regions}. Missing days are skipped."""
    out = {}
    for d in days:
        s = d.isoformat()
        dest = os.path.join(CACHE, "psi", f"{s}.json")
        try:
            raw = get(PSI_API.format(s), dest, refresh=refresh, tries=3)
            j = json.loads(raw)
            if j.get("code") != 0:
                if os.path.exists(dest):
                    os.remove(dest)          # don't cache a rate-limit error
                continue
            vals = []
            for it in j["data"]["items"]:
                rd = it.get("readings", {}).get("psi_twenty_four_hourly", {})
                vals += [float(v) for k, v in rd.items()
                         if k in ("north", "south", "east", "west", "central") and v is not None]
            if vals:
                out[s] = sum(vals) / len(vals)
        except Exception:                     # noqa: BLE001
            pass
        time.sleep(1.4)
    return out


def main():
    ap = argparse.ArgumentParser(description="Singapore haze check (CAMS GFAS + NEA PSI)")
    ap.add_argument("--days", type=int, default=7, help="days of history to show (default 7)")
    ap.add_argument("--no-psi", action="store_true", help="skip the NEA PSI lookup")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--refresh", action="store_true", help="ignore cached downloads")
    args = ap.parse_args()
    import numpy as np

    base = json.load(open(os.path.join(HERE, "baseline.json")))
    M, FLT, SG = base["model"], base["filter"], base["sg"]
    L, LAG, POW, A, B = M["L_km"], M["lag_days"], M["power"], M["a"], M["b"]

    man = json.loads(get(BASE + "manifest.json", os.path.join(CACHE, "manifest.json"), refresh=True))
    latest = dt.date.fromisoformat(man["variables"]["cfire"]["latest_day"])
    issued = man["generated_at"]

    # months needed: June of the current season through the latest month.
    # Outside Jun-Nov there is no season to accumulate, so just grab the last two months.
    in_season = latest.month >= 6
    months, y, m = [], latest.year, (6 if in_season else max(1, latest.month - 1))
    while (y, m) <= (latest.year, latest.month):
        months.append((y, m)); m += 1
        if m > 12: m, y = 1, y + 1
    day, lonx, latx, val, reg = load_gfas(months, args.refresh)

    g = base["grid"]
    lon = g["lon0"] + g["res"] * lonx
    lat = g["lat0"] + g["res"] * latx
    k = ((lon > FLT["lon"][0]) & (lon < FLT["lon"][1]) &
         (lat > FLT["lat"][0]) & (lat < FLT["lat"][1]))
    day, lon, lat, val, reg = day[k], lon[k], lat[k], val[k], reg[k]
    km = haversine_km(lon, lat, SG["lon"], SG["lat"])
    k = km <= FLT["max_km"]
    day, lon, lat, val, reg, km = day[k], lon[k], lat[k], val[k], reg[k], km[k]

    w = val * np.exp(-km / L)
    ndays = (latest - EPOCH).days + 1
    idx = np.zeros(ndays)
    np.add.at(idx, day, w)
    idx /= 1e3                                        # kt-effective
    implied = lambda v: A + B * max(v, 0.0) ** POW    # noqa: E731

    show = [latest - dt.timedelta(days=i) for i in range(args.days - 1, -1, -1)]
    psi = {} if args.no_psi else fetch_psi(show, args.refresh)

    # season position
    sd, cum = base["season_start_doy"], base["season_cum_Mt_eff"]
    doy_now = latest.timetuple().tm_yday
    k = (np.array([(EPOCH + dt.timedelta(days=int(i))).year for i in range(ndays)]) == latest.year)
    dd = np.array([(EPOCH + dt.timedelta(days=int(i))).timetuple().tm_yday for i in range(ndays)])
    this = idx[k & (dd >= sd) & (dd <= doy_now)].sum() / 1e3
    others = {}
    for yr, rec in cum.items():
        j = doy_now - rec["doy0"]
        if 0 <= j < len(rec["cum"]):
            others[int(yr)] = rec["cum"][j]
    others[latest.year] = round(float(this), 3)
    order = sorted(others.items(), key=lambda kv: -kv[1])
    rank = [i for i, (yr, _) in enumerate(order) if yr == latest.year][0] + 1
    median = float(np.median(list(others.values())))

    # top source provinces yesterday
    ridx = json.loads(get(BASE + "regions/region_index.json",
                          os.path.join(CACHE, "region_index.json")))
    a1n, a1p = ridx["admin1_names"], ridx["admin1_parent"]
    kd = day == (latest - EPOCH).days
    top = []
    for u in np.unique(reg[kd]):
        s = reg[kd] == u
        tot = val[kd][s].sum()
        if tot < 1000:
            continue
        d_km = float(np.average(km[kd][s], weights=val[kd][s]))
        brg = compass(float(np.average(lon[kd][s], weights=val[kd][s])),
                      float(np.average(lat[kd][s], weights=val[kd][s])), SG["lon"], SG["lat"])[1][0]
        nm = a1n[u] if u < len(a1n) else str(u)
        pa = a1p[u] if u < len(a1p) else ""
        if pa == "OFFSHORE":
            nm, pa = "offshore / unattributed", "--"
        top.append((float(tot), nm, pa, d_km, brg))
    top.sort(reverse=True)

    if args.json:
        print(json.dumps({
            "latest_analysis": latest.isoformat(), "issued": issued,
            "days": [{"date": d.isoformat(),
                      "index_kt_eff": round(float(idx[(d - EPOCH).days]), 1),
                      "implied_psi": round(implied(idx[(d - EPOCH).days - LAG]), 1),
                      "actual_psi": round(psi[d.isoformat()], 1) if d.isoformat() in psi else None}
                     for d in show],
            "outlook": {"date": (latest + dt.timedelta(days=LAG)).isoformat(),
                        "implied_psi": round(implied(idx[(latest - EPOCH).days]), 1)},
            "season": ({"mt_eff_since_jun1": round(float(this), 2), "rank": rank,
                        "of": len(others), "median": round(median, 2),
                        "ref": {y: others.get(y) for y in (2015, 2019) if y in others}}
                       if in_season else None),
            "top_sources": [{"province": n, "country": p, "kt_C": round(t / 1e3, 1),
                             "km": round(k_, 0), "bearing": b} for t, n, p, k_, b in top[:8]],
            "model": M,
        }, indent=2))
        return

    w_ = 74
    print(f"\n{C['b']}CAMS GFAS haze check - Singapore{C['r']}")
    print(f"{C['dim']}analysis through {latest:%a %d %b %Y} - issued {issued}{C['r']}")
    print(f"{C['dim']}{'-' * w_}{C['r']}")
    print(f"  {'date':<12}{'index':>10}{'implied':>10}{'actual':>9}")
    print(f"  {'':12}{'kt-eff':>10}{'PSI':>10}{'PSI':>9}   {C['dim']}fires -> air{C['r']}")
    for d in show:
        i = (d - EPOCH).days
        ip = implied(idx[i - LAG])
        ap_ = psi.get(d.isoformat())
        bar = "#" * min(28, int(idx[i] / 90))
        col = C["gn"] if (ap_ or ip) < 55 else C["yl"] if (ap_ or ip) < 100 else C["rd"]
        act = f"{ap_:>9.0f}" if ap_ is not None else f"{C['dim']}{'-':>9}{C['r']}"
        print(f"  {d:%d %b}      {idx[i]:>10.0f}{ip:>10.0f}{act}   {col}{bar}{C['r']}")
    nxt = latest + dt.timedelta(days=LAG)
    print(f"\n  {C['b']}{nxt:%a %d %b}: implied PSI {implied(idx[(latest - EPOCH).days]):.0f}{C['r']}"
          f"  {C['dim']}(from fires that have already burned){C['r']}")

    print(f"\n{C['b']}TOP SOURCES{C['r']} {C['dim']}on {latest:%d %b}, within 1800 km{C['r']}")
    for t, n, p, d_km, b in top[:6]:
        eta = 1 if d_km < 800 else 2 if d_km < 1200 else 3
        print(f"  {n[:26]:<27}{C['dim']}{p[:4]:<5}{C['r']}{t/1e3:>8.1f} kt C"
              f"{d_km:>8.0f} km  {b:<4}{C['dim']}~{eta} d out{C['r']}")

    if in_season:
        ratio = this / median if median else float("nan")
        print(f"\n{C['b']}SEASON{C['r']}  {this:.1f} Mt-eff since 1 Jun  -  "
              f"{C['b']}#{rank} of {len(others)}{C['r']} seasons since 2003  -  {ratio:.1f}x the median")
        for yr in (2015, 2019):
            if yr in others:
                print(f"  {C['dim']}{yr} on this date: {others[yr]:.1f} Mt-eff{C['r']}")
    else:
        print(f"\n{C['dim']}Outside the Jun-Nov burning season - no seasonal ranking.{C['r']}")
    print(f"\n{C['dim']}model: PSI = {A:.1f} + {B:.2f} * index^{POW:g}, index lagged {LAG} d, "
          f"exp(-km/{L}) weighting")
    print(f"fitted on {M['fitted_on']}, in-sample r = {M['r_season']}. Out of sample the index")
    print(f"alone does not beat persistence - read it as a fire-signal gauge, not a forecast.{C['r']}\n")


if __name__ == "__main__":
    main()
