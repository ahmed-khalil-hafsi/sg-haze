import json, datetime as dt
import numpy as np
import pyarrow.parquet as pq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'font.family':'serif','font.serif':['DejaVu Serif'],'mathtext.fontset':'dejavuserif','savefig.facecolor':'#ffffff'})
from matplotlib.colors import LogNorm
from matplotlib.collections import PolyCollection, LineCollection

SCRATCH = "."
DAY = dt.date(2026, 9, 13)
EPOCH = dt.date(2003, 1, 1)
LON0, LAT0, RES = -179.95, -89.95, 0.1
BOX = (92.0, 142.0, -11.0, 22.0)  # W, E, S, N

t = pq.read_table(f"{SCRATCH}/gfas/pixels/2026_09.parquet").to_pydict()
day = np.array(t["day_idx"])
lon = LON0 + RES * np.array(t["lon_idx"], dtype=float)
lat = LAT0 + RES * np.array(t["lat_idx"], dtype=float)
val = np.array(t["value"], dtype=float)

m = (day == (DAY - EPOCH).days) & (lon >= BOX[0]) & (lon <= BOX[1]) & (lat >= BOX[2]) & (lat <= BOX[3])
plon, plat, pval = lon[m], lat[m], val[m]
order = np.argsort(pval)
plon, plat, pval = plon[order], plat[order], pval[order]

# coastlines / borders
gj = json.load(open(f"{SCRATCH}/ne50_countries.geojson"))
land, borders = [], []
for f in gj["features"]:
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        ring = np.array(poly[0], dtype=float)
        if ring[:, 0].max() < BOX[0] - 4 or ring[:, 0].min() > BOX[1] + 4:
            continue
        if ring[:, 1].max() < BOX[2] - 4 or ring[:, 1].min() > BOX[3] + 4:
            continue
        land.append(ring)
        borders.append(ring)

fig = plt.figure(figsize=(16, 10.6), dpi=125)
fig.patch.set_facecolor("#ffffff")
ax = fig.add_axes([0.045, 0.085, 0.905, 0.80])
ax.set_facecolor("#ffffff")

ax.add_collection(PolyCollection(land, facecolors="#eeeeee", edgecolors="none", zorder=1))
ax.add_collection(LineCollection(borders, colors="#9a9a9a", linewidths=0.6, zorder=2))

norm = LogNorm(vmin=10, vmax=max(2e4, pval.max()))
sc = ax.scatter(plon, plat, c=pval, s=26, marker="s", cmap='YlOrRd', norm=norm,
                linewidths=0, alpha=0.95, zorder=3)

# Singapore
ax.plot(103.82, 1.35, marker="*", ms=20, mfc="#000000", mec="#ffffff", mew=1.2, zorder=6)
ax.annotate("SINGAPORE", (103.82, 1.35), textcoords="offset points", xytext=(0, -22),
            ha="center", color="#000000", fontsize=11, fontweight="bold", zorder=6)

labels = [
    ("SUMATRA", 101.0, -1.0), ("KALIMANTAN\n(BORNEO)", 114.0, 0.6), ("JAVA", 110.5, -7.6),
    ("SULAWESI", 121.0, -2.5), ("PAPUA", 138.5, -4.5), ("MALAYSIA", 102.2, 4.6),
    ("THAILAND", 100.5, 15.5), ("VIETNAM", 106.6, 17.5), ("PHILIPPINES", 122.5, 12.5),
    ("PAPUA NEW\nGUINEA", 143.0, -6.0),
]
for txt, x, y in labels:
    if BOX[0] < x < BOX[1] and BOX[2] < y < BOX[3]:
        ax.text(x, y, txt, color="#555555", fontsize=9.5, ha="center", va="center",
                fontweight="semibold", zorder=4)

ax.set_xlim(BOX[0], BOX[1]); ax.set_ylim(BOX[2], BOX[3])
ax.set_aspect(1 / np.cos(np.deg2rad(5)))
for s in ax.spines.values():
    s.set_color("#666666")
ax.tick_params(colors="#444444", labelsize=8)
ax.grid(color="#dcdcdc", lw=0.5)

cb = fig.colorbar(sc, ax=ax, fraction=0.028, pad=0.012)
cb.set_label("Wildfire carbon emissions  (tonnes C per 0.1°×0.1° cell, per day)",
             color="#222222", fontsize=10)
cb.ax.yaxis.set_tick_params(color="#444444", labelsize=9)
plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="#222222")
cb.outline.set_edgecolor("#666666")

total = pval.sum() / 1e6
fig.text(0.045, 0.955, "Total daily wildfire emissions — South East Asia", color="#ffffff",
         fontsize=25, fontweight="bold", ha="left", va="top")
fig.text(0.045, 0.905,
         f"Saturday 13 September 2026 (latest CAMS analysis)   ·   {total:.2f} Mt of carbon released in this view in 24 h",
         color="#333333", fontsize=13.5, ha="left", va="top")
fig.text(0.045, 0.022,
         "Source: Copernicus Atmosphere Monitoring Service (CAMS) Global Fire Assimilation System (GFAS) v2, 0.1° daily wildfire carbon emissions.\n"
         "Data retrieved from sites.ecmwf.int/data/cams/products/gfas (analysis generated 2026-09-14 06:25 UTC). Coastlines: Natural Earth 50m.",
         color="#555555", fontsize=8.5, ha="left", va="bottom")

fig.savefig(f"{SCRATCH}/sea_wildfire_emissions_2026-09-13.png", facecolor=fig.get_facecolor())
print("saved", total)
