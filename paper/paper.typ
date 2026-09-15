#set document(
  title: "A distance-weighted wildfire emission index for Singapore haze: diagnostic value and limited incremental forecast skill, 2014–2026",
  author: "Ahmed Khalil Hafsi",
)
#set page(paper: "a4", margin: (x: 2.3cm, top: 2.4cm, bottom: 2.6cm),
  numbering: "1",
  footer: context [#set text(8.5pt); #h(1fr) #counter(page).display("1") #h(1fr)])
#set text(size: 10.5pt, lang: "en")
#set par(justify: true, leading: 0.62em, first-line-indent: 1.2em, spacing: 0.62em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => { v(1.1em); set text(11.5pt, weight: "bold"); it; v(0.45em) }
#show heading.where(level: 2): it => { v(0.8em); set text(10.5pt, weight: "bold", style: "italic"); it; v(0.3em) }
#show heading: set par(first-line-indent: 0em)
#set math.equation(numbering: "(1)")
#show figure.caption: set text(9pt)
#show figure.caption: set par(justify: true, first-line-indent: 0em)
#set figure(gap: 0.8em)
#show figure: set block(spacing: 1.4em)
#set table(stroke: none)

#align(center)[
  #block(width: 90%)[
    #set par(justify: false, first-line-indent: 0em)
    #text(16pt, weight: "bold")[A distance-weighted wildfire emission index for Singapore haze: diagnostic value and limited incremental forecast skill, 2014–2026]
  ]
  #v(0.9em)
  #text(11.5pt)[Ahmed Khalil Hafsi]
  #v(0.25em)
  #text(9.5pt, fill: luma(80))[Preprint draft · 15 September 2026 · Data through 13 September 2026]
  #v(0.15em)
  #text(9.5pt, fill: luma(80))[#link("https://doi.org/10.5281/zenodo.22764305")[doi:10.5281/zenodo.22764305]]
]

#v(1.2em)
#block(inset: (x: 1.6em))[
  #set par(first-line-indent: 0em)
  #set text(9.8pt)
  *Abstract.* Episodic haze in Singapore is driven by biomass burning in Sumatra and Borneo. This note examines how much of the day-to-day variation in Singapore's air quality can be recovered from openly available, near-real-time fire emission estimates alone. Daily wildfire carbon emissions from the Copernicus Atmosphere Monitoring Service Global Fire Assimilation System (CAMS GFAS v2, 0.1°) are aggregated into a scalar index by weighting each grid cell with an exponential decay in great-circle distance from Singapore, and the index is related to the National Environment Agency 24-hour Pollutant Standards Index (PSI) over the June–November seasons of 2014–2026. In-sample, a square-root response to the index lagged by one day with a 900 km decay length correlates with PSI at $r = 0.72$. Under nested leave-one-season-out cross-validation with forecast-consistent lags, however, the index alone ($R^2 = 0.43$) is substantially outperformed by persistence ($R^2 = 0.67$). Added to a first-order autoregressive model of PSI, the index reduces pooled root-mean-square error by 3.6% (95% CI 1.1–5.3%, season-block bootstrap), a small but consistent improvement concentrated in the 2015 episode. Non-negative least-squares apportionment over distance–bearing bins places 65% of the fitted fire contribution in the southern and south-eastern sectors at 250–1200 km, with wide uncertainty (95% CI 24–81%). The index is therefore better suited to diagnosing the regional fire situation than to forecasting PSI.
]

= Introduction

Transboundary smoke from peat and vegetation fires in Indonesia is the principal cause of severe particulate pollution episodes in Singapore, most notably in 2015. Physically based chemical transport models are the appropriate tool for attributing such episodes to specific sources, but they are computationally demanding and not generally available to individual users on a daily basis. By contrast, satellite-derived fire emission estimates are published openly each morning.

This note asks a narrower question: how much of the variation in Singapore's measured air quality is recoverable from those emission estimates through a transparent statistical construction, and does that information add anything to the most basic forecast, that tomorrow will resemble today? The analysis is intentionally minimal. It uses no meteorological inputs and no transport modelling, and it is evaluated against simple baselines so that its value can be stated without overstatement. A review of the substantial literature on transport-model attribution of Southeast Asian haze is outside the scope of this draft.

= Data

Wildfire emissions are taken from CAMS GFAS v2 [1], which estimates daily carbon emissions on a 0.1° global grid from satellite observations of fire radiative power. The complete archive from 1 January 2003 to 13 September 2026 was used. Values are tonnes of carbon per grid cell per day.

Air quality observations are the 24-hour PSI published by the National Environment Agency of Singapore [2], reported hourly for five regions. Records from 1 April 2014 to 31 July 2026 were obtained as an archival file, and records from 1 August to 13 September 2026 from the real-time interface. The daily value used throughout is the mean over all hours and all five regions, retained only when at least twelve hourly reports were available. The analysis is restricted to June–November, giving 13 seasons. Coastlines in @fig:map are from Natural Earth.

= Methods

== Emission index

For day $t$, emissions $E_i (t)$ in each grid cell $i$ within 1800 km of Singapore (1.35°N, 103.82°E) are weighted by great-circle distance $d_i$ and summed:

$ Phi(t) = sum_i E_i (t) exp(-d_i / L). $ <eq:index>

$Phi$ is expressed in kilotonnes of carbon after weighting ("kt-effective").

== Response model and in-sample fit

Daily PSI is modelled as

$ "PSI"(t) = a + b dot Phi(t - tau)^p . $ <eq:resp>

For the descriptive, in-sample fit, the structural parameters were chosen by grid search over $L in {150, 250, 400, 600, 900, 1400}$ km, $tau in {0, dots, 8}$ days and $p in {0.25, 0.33, 0.5, 0.75, 1}$, maximising Pearson correlation over all June–November days. This selection uses all data and is reported only as a description of the relationship; it is not used to assess skill.

== Forecast evaluation

Four models are compared. _Persistence_ sets $"PSI"(t) = "PSI"(t-1)$. _AR(1)_ regresses $"PSI"(t)$ on $"PSI"(t-1)$. _Index_ is @eq:resp. _AR(1) + index_ adds the transformed, lagged index as a second regressor to AR(1).

Skill is assessed by nested leave-one-season-out cross-validation. For each of the 13 seasons, the structural parameters ($L$, $tau$, $p$) and the regression coefficients are selected using the remaining 12 seasons only, and predictions are made for the held-out season. Lags are restricted to $tau >= 1$ day, because GFAS estimates for a given day are published on the following morning; a same-day lag would use information unavailable at forecast time. Performance is summarised by out-of-sample $R^2$ and root-mean-square error (RMSE), per season and pooled across all held-out predictions.

Uncertainty is estimated by a season-block bootstrap: seasons are resampled with replacement ($B = 2000$) and pooled metrics recomputed on the resampled held-out predictions. Resampling whole seasons preserves the strong within-season autocorrelation of PSI, which would otherwise make intervals too narrow.

== Source apportionment

Emissions are binned into five distance rings (0–250, 250–500, 500–800, 800–1200 and 1200–1800 km) and eight 45° bearing sectors, giving 40 bins. A single transport lag ($>= 1$ day) is selected for each ring. PSI is regressed on the square roots of the lagged bin totals using non-negative least squares with a ridge penalty ($lambda = 50$), and the contribution of each bin is taken as its coefficient multiplied by its mean regressor value. Stability is assessed with 500 season-block bootstrap replicates, holding the ring lags fixed.

= Results

== Regional emissions on 13 September 2026

Emissions within the mapped domain on 13 September 2026 totalled 2.30 Mt C, against a global total of 4.47 Mt C (@fig:map). Kalimantan contributed 1.92 Mt C and Sumatra 0.18 Mt C.

#figure(
  image("figures/fig1_map.png", width: 100%),
  caption: [Daily wildfire carbon emissions on 13 September 2026 on the native 0.1° GFAS grid. The largest single cell (114.05°E, 3.05°S; approximately 140 kt C d#super[−1]) lies in South Kalimantan, 1238 km from Singapore; the second largest (104.35°E, 3.05°S) lies in South Sumatra, 490 km away.],
) <fig:map>

== Relationship between the index and PSI

The in-sample grid search selected $L = 900$ km, $tau = 1$ day and $p = 0.5$, giving

$ "PSI" = 41.9 + 1.14 dot Phi^0.5, quad r = 0.72 . $ <eq:fit>

The intercept is close to the background PSI of low-fire periods. @fig:series shows the index and observed PSI for the three most relevant seasons. The index captures the onset and broad timing of the 2015 and 2019 episodes but not their day-to-day structure.

#figure(
  image("figures/fig2_index_psi.png", width: 100%),
  caption: [Index $Phi$ (filled) and observed 24-hour PSI (solid line) for 2015, 2019 and 2026 to date. Shading extends from the island mean to the worst region; the dashed line is the PSI implied by @eq:fit. Peak regional PSI was 322 in 2015, 154 in 2019 and 123 to date in 2026.],
) <fig:series>

== Forecast skill

Pooled out-of-sample results are given in @tab:skill and per-season results in @fig:skill.

#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 0.8pt),
    table.header([*Model*], [*$R^2$, all*], [*RMSE, all*], [*$R^2$, fire seasons*], [*RMSE, fire seasons*]),
    table.hline(stroke: 0.5pt),
    [Persistence], [0.669], [9.39], [0.689], [12.41],
    [AR(1)], [0.692], [9.06], [0.705], [12.09],
    [Index alone], [0.426], [12.36], [0.436], [16.71],
    [AR(1) + index], [*0.716*], [*8.70*], [*0.731*], [*11.54*],
    table.hline(stroke: 0.8pt),
  ),
  caption: [Nested leave-one-season-out performance, June–November 2014–2026. RMSE in PSI units. Fire seasons are 2014, 2015, 2019, 2023 and 2026. Season-block bootstrap 95% intervals for pooled $R^2$: index 0.17–0.48; AR(1) 0.55–0.72; AR(1) + index 0.57–0.75.],
  kind: table,
) <tab:skill>

Three results follow. First, the index alone is a poor forecaster: its pooled $R^2$ is 0.24 lower than persistence, and it has negative skill in six of the eight seasons without substantial burning. Second, the index nonetheless carries information that persistence does not. Adding it to AR(1) reduces pooled RMSE by 3.6% (95% CI 1.1–5.3%); the improvement is at or below zero in only 0.1% of bootstrap replicates. Third, the improvement is uneven across fire seasons. It is largest in 2015 (RMSE 21.5 to 20.2) and absent in 2019 and 2026, where persistence alone already achieves $R^2$ of 0.71 and 0.77.

#figure(
  image("figures/fig3_skill.png", width: 100%),
  caption: [Out-of-sample $R^2$ by held-out season for the four models, with the pooled result at right. Fire-affected seasons are shown in bold.],
) <fig:skill>

== Source apportionment

In the full-sample fit, the largest contributions lie in the southern and south-eastern sectors (@fig:apport). Bins in those two sectors between 250 and 1200 km account for 65% of the total fitted contribution (95% CI 24–81%). The single largest bin, due south at 250–500 km, is also the largest in 47% of bootstrap replicates; the south-eastern bin at 1200–1800 km and the southern bin at 500–800 km are largest in 20% and 17% respectively. The broad sectoral pattern is therefore reasonably consistent, but the ranking of individual bins is not robust.

At the provincial level, one-day-lagged emissions from South Sumatra correlate with PSI at $r = 0.72$ and three-day-lagged emissions from Central Kalimantan at $r = 0.64$. The bootstrap interval for this difference (−0.09 to 0.11) includes zero, so the data do not establish that either province is the stronger predictor.

#figure(
  image("figures/fig4_apportionment.png", width: 100%),
  caption: [Left: fitted contribution to PSI by bearing sector and distance ring (full sample). Centre: correlation between provincial daily emissions and PSI as a function of lag. Right: all June–November days, 2014–2026, with the in-sample fit of @eq:fit. All panels are in-sample; see the text for bootstrap intervals.],
) <fig:apport>

== Seasonal context

Cumulative weighted emissions from 1 June to 13 September 2026 reached 28.0 Mt-effective. This ranks fifth of the 24 seasons since 2003 and is 2.2 times the median season, against 51.6 in 2015 and 35.0 in 2019 on the same date (@fig:season). The largest increase in 2015 came after mid-September, so this ranking does not indicate how the 2026 season will develop.

#figure(
  image("figures/fig5_season.png", width: 100%),
  caption: [Cumulative weighted emissions from 1 June for each season from 2003 to 2026.],
) <fig:season>

= Discussion and limitations

The index describes where fires must lie, on average, to affect Singapore, and summarises the regional fire situation in a single number that can be computed each morning from open data. That makes it useful for diagnosis and context. It is not an adequate forecast: PSI is highly persistent, and most of what the index explains is already contained in the previous day's observation. Its incremental contribution is statistically robust but practically small.

Several limitations apply. The exponential distance weighting is a climatological surrogate for transport and contains no information about wind on a given day, which is the most likely reason the index captures episode timing but not daily variability. Rainfall, boundary-layer depth and local emissions are not represented. PSI is a composite index; PM#sub[2.5] concentration would be a cleaner target. GFAS estimates carry their own uncertainties, particularly for smouldering peat fires. The effective sample is small, with only five seasons showing substantial burning, and the apportionment in particular is sensitive to which of those seasons are included. The ridge penalty and ring lags were not tuned by cross-validation.

Natural extensions are the addition of reanalysis winds and precipitation, direct comparison with operational transport-model forecasts, the use of PM#sub[2.5] as the target, and a review of the existing attribution literature.

= Code and data availability

All code, the fitted coefficients and the figures are available at #link("https://github.com/ahmed-khalil-hafsi/sg-haze")[github.com/ahmed-khalil-hafsi/sg-haze] and archived at Zenodo under #link("https://doi.org/10.5281/zenodo.22764305")[doi:10.5281/zenodo.22764305] (release described here) and #link("https://doi.org/10.5281/zenodo.22764304")[doi:10.5281/zenodo.22764304] (all versions). The input datasets are publicly available from their providers [1, 2] and are not redistributed.

#v(0.6em)
#text(9pt)[
  *Disclaimer.* This is independent work, not affiliated with or endorsed by ECMWF, the Copernicus programme or the National Environment Agency of Singapore. It is not health guidance; official air quality information for Singapore is published at #link("https://www.haze.gov.sg")[haze.gov.sg].
]

#v(0.4em)
#heading(numbering: none)[References]
#set par(first-line-indent: 0em, hanging-indent: 1.4em)
#set text(9.5pt)

[1] Copernicus Atmosphere Monitoring Service. Global Fire Assimilation System (GFAS) v2, daily wildfire carbon emissions. ECMWF. #link("https://sites.ecmwf.int/data/cams/products/gfas/")[sites.ecmwf.int/data/cams/products/gfas]

[2] National Environment Agency, Singapore. Historical 24-hr PSI and real-time PSI. Singapore Open Data. #link("https://data.gov.sg")[data.gov.sg]

[3] Natural Earth. 1:50m Cultural Vectors, Admin 0 Countries. #link("https://www.naturalearthdata.com")[naturalearthdata.com]
