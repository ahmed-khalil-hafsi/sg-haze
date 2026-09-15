# Analysis plan v3 — p2predict with rich inputs, pre-specified before running

Written 15 September 2026, before any v3 model was trained. v2 had already
shown that p2predict loses to OLS when both are given the three-input M5
predictor set (exploratory result). v3 asks a different question: **with a
richer, pre-specified input set, used through its own CLI, does p2predict beat
(a) the best confirmatory v2 model M5 and (b) a plain ridge regression on the
same rich inputs?** Every configuration below will be reported, whatever its
result. The author of this study also wrote p2predict; that competing interest
will be declared in any output that uses these results.

## Target and folds

- Target: NEA 24-hour PSI, daily island mean (as v1/v2), June–November.
- Outer evaluation: the same leave-one-season-out folds and the same day set as
  v2 (`common` mask in `v2/pred_psi.npz`, 2014–2026).

## Feature set F2 (fixed a priori)

All features are dated *t − 1* or earlier.

| Feature | Definition |
|---|---|
| `psi_lag1`, `psi_lag2`, `psi_lag3` | PSI on *t−1*, *t−2*, *t−3* |
| `emis_{N..NW}` (8) | sector distance-weighted emissions S_s(*t−1*; L = 600 km) |
| `wind_{N..NW}` (8) | toward-Singapore ERA5 100 m wind component c_s(*t−1*), m/s |
| `transport_{N..NW}` (8) | S_s(*t−1*; 600) × max(0, c_s(*t−1*)) |
| `phi_lag1..3` | Φ_dist(*t−1*, *t−2*, *t−3*; L = 600 km) |
| `rain_lag1` | log(1 + precipitation at Singapore, *t−1*) |
| `blh_lag1` | ERA5 daily-mean boundary-layer height at Singapore, *t−1* |
| `day_of_season` | days since 1 June |

L = 600 km is fixed a priori as the geometric midpoint of the v2 grid. It was
**not** chosen by fitting outcomes (the v1 in-sample optimum was 900 km).
Boundary-layer height is new in v3 and is declared here before being fetched.

## p2predict configurations (all via the `p2predict-train` CLI)

Common to all: `--time-column date`, `--outliers keep` (the target's upper
outliers *are* the haze days and must not be removed), `--json`, training CSV
containing only the outer fold's training seasons.

| ID | Flags |
|---|---|
| C1 | auto mode, `--budget fast`, `--max-features 12`, `--log-target auto` |
| C2 | auto mode, `--budget thorough`, `--max-features 34`, `--log-target auto` |
| C3 | expert `-a ridge --tune`, `-tf <all F2>`, `--log-target off` |
| C4 | expert `-a xgboost --tune --budget thorough`, `-tf <all F2>`, `--log-target auto` |
| C5 | auto mode, `--budget fast`, `--max-features 12`, `--feature-outliers winsorize` |

**Selection within each outer fold** is by the lowest RMSE on p2predict's own
chronological holdout: the last 20% of the fold's *training* rows. The test
season is never seen during selection. The selected configuration's
held-out-season predictions are "p2predict (selected)". Every configuration's
held-out performance is also reported individually. The per-fold best
configuration *by test score* is not reported as p2predict performance.

## Comparators

- M2 (AR(1)) and M5 (AR(1) + wind index + rain), taken from v2 unchanged.
- **Ridge-F2:** scikit-learn ridge regression on standardised F2. α is chosen
  from {0.1, 1, 10, 100, 1000} by the same chronological last-20% holdout
  within training seasons, then refitted on all training seasons. This
  separates the value of the rich inputs from the value of p2predict.

## Metrics

- Out-of-sample R² and RMSE, pooled, in fire seasons, and per season.
- Season-block bootstrap (B = 2000) of the RMSE change of p2predict (selected)
  relative to M2, M5 and Ridge-F2, and of Ridge-F2 relative to M5.
- Intervals: p2predict `--interval 80` and `--interval 90` from the selected
  configuration. Empirical coverage and mean width are reported on all days,
  fire seasons, and the 10% highest-PSI days.

## Claims rule

Any statement about p2predict in a paper, README, website or marketing will
cite only numbers produced under this protocol, with the comparators alongside.
