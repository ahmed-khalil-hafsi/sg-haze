# sg-haze

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22764304.svg)](https://doi.org/10.5281/zenodo.22764304)

A distance-weighted wildfire emission index for Singapore haze, built entirely
from open, near-real-time data.

**Author:** Ahmed Khalil Hafsi ·
**Paper:** [`paper/paper.pdf`](paper/paper.pdf) ·
**Web version:** https://sg-haze.mail-7dd.workers.dev ·
**DOI:** [10.5281/zenodo.22764305](https://doi.org/10.5281/zenodo.22764305)

Every morning CAMS publishes satellite-derived wildfire carbon emissions on a
0.1° grid. This project weights every fire cell by its distance from Singapore,
sums them into one number, and asks how much of Singapore's measured air quality
(NEA 24-hour PSI) that number explains.

## Findings, briefly

Evaluated with nested leave-one-season-out cross-validation over the
June–November seasons of 2014–2026, with forecast-consistent lags:

| Model | Out-of-sample R² | RMSE (PSI) |
|---|---|---|
| Persistence (tomorrow = today) | 0.669 | 9.39 |
| AR(1) on yesterday's PSI | 0.692 | 9.06 |
| **Emission index alone** | **0.426** | **12.36** |
| AR(1) + emission index | 0.716 | 8.70 |

- **The index alone does not beat persistence.** PSI is highly persistent, and
  yesterday's reading already contains most of what the index knows.
- **It does add a little on top of persistence:** RMSE −3.6% (95% CI 1.1–5.3%,
  season-block bootstrap), mostly in the 2015 episode.
- **The fitted signal comes mainly from the south and south-east at
  250–1200 km** (65% of the fitted contribution) — but the 95% CI is 24–81%, and
  the ranking of individual source bins is not stable.
- In-sample the index correlates with PSI at r = 0.72; that number describes the
  relationship and is not a measure of skill.

So: useful as a daily summary of the regional fire situation, not as a PSI
forecast. See the paper for methods and limitations — notably, no wind or rain.

## Quick start: the daily check

```bash
./haze.py
```

Needs [uv](https://docs.astral.sh/uv/) on PATH. The shebang installs numpy and
pyarrow into a throwaway environment, so there is nothing else to set up.

```
  date             index   implied   actual
                  kt-eff       PSI      PSI   fires -> air
  12 Sep             584        81       73   ######
  13 Sep             664        69       73   #######

TOP SOURCES on 13 Sep, within 1800 km
  Kalimantan Tengah          IDN     961.3 kt C    1179 km  ESE ~2 d out
  Sumatera Selatan           IDN     157.5 kt C     502 km  S   ~1 d out

SEASON  28.0 Mt-eff since 1 Jun  -  #5 of 24 seasons since 2003  -  2.2x the median
```

| Flag | Effect |
|---|---|
| `--days N` | days of history (default 7) |
| `--no-psi` | skip the NEA lookup |
| `--json` | machine-readable output |
| `--refresh` | ignore the local cache |

The first run downloads about 4 MB into `cache/`; after that only the current
month is re-fetched. "Implied PSI" is the index-only model — read it as a
fire-signal gauge, per the findings above.

## Reproducing the paper

```bash
pipeline/run_all.sh
```

This downloads the full GFAS archive (about 300 MB, 2003–present) and the NEA
PSI record into `work/`, then rebuilds every intermediate, reruns the
evaluation, regenerates all figures and recompiles `paper/paper.pdf`. Allow
roughly 20 minutes: the data.gov.sg API rate-limits aggressively, and the
script backs off accordingly.

| Script | Role |
|---|---|
| `dl.py` | download the GFAS pixel archive |
| `psi_build.py` | assemble daily PSI from the archive CSV and API days |
| `aggregate.py` | daily distance-decay sums, distance × bearing bins, provincial totals |
| `analysis.py` | in-sample grid search for decay length, lag and exponent |
| `sectors.py` | in-sample non-negative least-squares source apportionment |
| `evaluate.py` | nested cross-validation, baselines, season-block bootstrap → `evaluation.json` |
| `figs.py`, `fig_skill.py`, `plot_fire.py` | figures |

`plot_fire.py` is pinned to the 13 September 2026 map used in the paper.

## Repository layout

```
haze.py            daily check (single file)
baseline.json      fitted coefficients + seasonal curves used by haze.py
pipeline/          full analysis and figure generation
paper/             typst source, figures and compiled PDF
site/              static web version (Cloudflare Workers assets)
wrangler.jsonc     Cloudflare config; ./publish.sh deploys site/
```

## Data and licences

Code is MIT-licensed. The data are not, and are not redistributed here:

- **Wildfire emissions:** Copernicus Atmosphere Monitoring Service, Global Fire
  Assimilation System (GFAS) v2, via
  [sites.ecmwf.int/data/cams/products/gfas](https://sites.ecmwf.int/data/cams/products/gfas/).
  Subject to the Copernicus licence.
- **Air quality:** National Environment Agency, Singapore, 24-hour PSI via
  [data.gov.sg](https://data.gov.sg). Subject to the Singapore Open Data
  Licence.
- **Coastlines:** Natural Earth (public domain).

`baseline.json` contains coefficients and seasonal totals derived from these
sources. Check both licences before redistributing derived outputs.

This is independent work, not affiliated with or endorsed by ECMWF, the
Copernicus programme or NEA. It is not health guidance — official air quality
information for Singapore is at [haze.gov.sg](https://www.haze.gov.sg).

## Citation

See [`CITATION.cff`](CITATION.cff), or:

> Hafsi, A. K. (2026). *A distance-weighted wildfire emission index for Singapore
> haze: diagnostic value and limited incremental forecast skill, 2014–2026.*
> Preprint. https://doi.org/10.5281/zenodo.22764305

To cite the software regardless of version, use the concept DOI
[10.5281/zenodo.22764304](https://doi.org/10.5281/zenodo.22764304).
