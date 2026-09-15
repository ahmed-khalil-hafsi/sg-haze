# Analysis plan v2 — pre-specified before any v2 data were retrieved

Written 15 September 2026, before downloading any meteorological, PM2.5 or
CAMS forecast data. The commit that adds this file is the timestamp. Every
model below will be reported, whatever its result. Anything added after
results are seen will be labelled *exploratory*.

## Targets

- **Primary:** NEA 24-hour PSI, daily island mean (mean over all hours and the
  five regions, days with ≥ 12 hourly reports), June–November 2014–2026. As in v1.
- **Secondary:** NEA 24-hour PM2.5 (`pm25_twenty_four_hourly`), daily island
  mean under the same rules, June–November, from 14 March 2016 onward.
  Sources: the yearly historical datasets (2016–2024) plus the real-time API
  (2025–2026), as far as retrievable. Coverage actually achieved will be reported.

## Information set

Every predictor for day *t* is dated *t − 1* or earlier. This matches what is
known on the morning of *t*: GFAS for day *t − 1* is published then. The single
exception is the diagnostic model M6, which is labelled as such.

## Predictors

**Distance-weighted index, Φ_dist** — unchanged from v1:

    Φ_dist(t; L) = Σ_pixels E_i(t) · exp(−d_i / L),   d_i ≤ 1800 km

**Wind-weighted index, Φ_wind.** The pixel sums are split by the pixel's bearing
from Singapore into eight 45° sectors *s* (sector 0 centred on north):
S_s(t; L) = Σ_{pixels in s} E_i(t) · exp(−d_i / L), so that Σ_s S_s = Φ_dist.
Then

    Φ_wind(t; L) = Σ_s S_s(t; L) · max(0, c_s(t))

where c_s(t) is the component, in m/s, of the daily-mean 850 hPa wind vector
directed **toward Singapore**. The wind is taken at the point 400 km from
Singapore along the sector's centre bearing; the daily mean is the vector mean
of hourly u and v. Winds blowing away from Singapore contribute zero. There is
no floor term and no exponent on c_s.

**Rainfall, R(t)** = log(1 + daily precipitation sum at Singapore, mm).

**Meteorology source:** Open-Meteo historical weather API, ERA5-family
reanalysis. If a pure-ERA5 request cannot supply 850 hPa winds, the provider's
default model mix will be used, and that will be documented.

**CAMS forecast, C(t):** daily mean surface PM2.5 at Singapore (1.35°N,
103.82°E) from the Open-Meteo air-quality API, which serves CAMS global
forecasts from 2022. The lead time is as stitched by the provider — at most
about one day, to be documented. This is the one forecast input dated *t*: it
is itself a forecast issued before or on day *t*.

## Models (confirmatory)

| ID | Model | Seasons |
|---|---|---|
| M1 | Persistence: Y(t) = Y(t−1) | all |
| M2 | AR(1): Y(t) ~ Y(t−1) | all |
| M3 | AR(1) + Φ_dist(t−τ)^p | all |
| M4 | AR(1) + Φ_wind(t−τ)^p, wind at t−τ | all |
| M5 | M4 + R(t−1) | all |
| M6 | *Diagnostic, not a forecast:* AR(1) + Φ_wind(t−τ)^p with wind averaged over t−τ…t, + R(t). Upper bound given perfect knowledge of the day's weather. | all |
| M7 | C(t) alone (linear) | 2022–2026 |
| M8 | AR(1) + C(t) | 2022–2026 |
| M9 | AR(1) + C(t) + Φ_wind(t−τ)^p | 2022–2026 |

Y is PSI for the primary analysis and PM2.5 for the secondary.

**Structure selection** happens inside each fold only, over L ∈ {150, 250, 400,
600, 900, 1400} km, τ ∈ {1, …, 5} d and p ∈ {0.33, 0.5, 0.75, 1}. For M3–M6
and M9 the choice maximises training-fold R² of the full model.

## Evaluation

- Nested leave-one-season-out cross-validation. M1–M6 use all available seasons.
  M7–M9 use leave-one-season-out within 2022–2026 only, so they train on four
  seasons; this is stated as a limitation.
- Out-of-sample R² and RMSE: pooled, per season, and over fire seasons
  (2014, 2015, 2019, 2023, 2026).
- Season-block bootstrap (B = 2000) of the pooled RMSE change relative to M2
  for every model, and relative to M8 for M9.
- For the comparison of M3–M6 with M7–M9, all models are also reported on the
  common 2022–2026 subset.

## Exploratory, labelled as such

- **p2predict** (author's tabular modelling toolkit): trained on the M5
  predictor set (and the M9 set where C is available), using exactly the same
  leave-one-season-out folds, with metrics computed by the same code as for
  M1–M9. Any prediction intervals will be assessed for empirical coverage on
  held-out seasons.

## Deviations from this plan

**D1 — wind level, 850 hPa → 100 m (recorded 15 September 2026, before any v2
results were computed).** After this plan was committed, the Open-Meteo
historical archive turned out to return no values for 850 hPa wind: every
hour is null, for both the `era5` and the default model mix, in 2015 and in
2024. It does supply ERA5 wind at 100 m above ground for the whole 2014–2026
period. Φ_wind therefore uses the daily vector-mean **100 m** wind, with the
same points (400 km along each sector's centre bearing), the same
toward-Singapore component, the same max(0, ·) rule and the same models. No
other change was made. Boundary-layer height, which is also available, is
**not** added to the confirmatory models.

Physical rationale: smoke from smouldering peat fires, which dominate
Indonesian emissions, rises only a short way and is largely confined to the
boundary layer, so 100 m wind is a defensible transport level. An 850 hPa
sensitivity run using ERA5 pressure-level data from the Copernicus Climate
Data Store remains possible and, if performed, will be reported as a
sensitivity analysis.
