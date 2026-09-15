#!/usr/bin/env bash
set -uo pipefail
# Full reproduction: downloads ~300 MB of GFAS + NEA PSI into ./work, rebuilds
# every intermediate, reruns the evaluation, regenerates figures and the PDF.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; W="$ROOT/work"; mkdir -p "$W"; cd "$W"
cp "$ROOT"/pipeline/*.py .
B=https://sites.ecmwf.int/data/cams/products/gfas/v2_gisco_fp
echo "[1/9] manifest + regions"; curl -sS -o manifest.json $B/manifest.json && curl -sS -o region_index.json $B/regions/region_index.json
echo "[2/9] GFAS archive"; uv run --quiet python3 dl.py || { echo FAIL_DL; exit 1; }
echo "[3/9] PSI archive"
U=$(curl -sS https://api-open.data.gov.sg/v1/public/api/datasets/d_b4cf557f8750260d229c49fd768e11ed/poll-download | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['url'])") && curl -sSL "$U" -o psi_24h.csv || { echo FAIL_PSI_CSV; exit 1; }
echo "[4/9] PSI recent days"; mkdir -p psi_days
for i in $(seq 0 44); do d=$(date -j -v+${i}d -f %Y-%m-%d 2026-08-01 +%Y-%m-%d); [ -s psi_days/$d.json ] && grep -q '"code":0' psi_days/$d.json && continue
  for a in 1 2 3 4 5 6; do curl -sS --max-time 25 "https://api-open.data.gov.sg/v2/real-time/api/psi?date=$d" -o psi_days/$d.json; grep -q '"code":0' psi_days/$d.json && break; sleep 12; done; sleep 4; done
echo "PSI days bad: $(grep -L '"code":0' psi_days/*.json | wc -l)"
echo "[5/9] build"; uv run --quiet --with numpy python3 psi_build.py && uv run --quiet --with numpy --with pyarrow python3 aggregate.py || { echo FAIL_BUILD; exit 1; }
echo "[6/9] fit + apportionment"; uv run --quiet --with numpy python3 analysis.py && uv run --quiet --with numpy --with scipy python3 sectors.py
echo "[7/9] evaluation"; uv run --quiet --with numpy --with scipy python3 evaluate.py
echo "[8/9] figures"; curl -sSL -o ne50_countries.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
uv run --quiet --with numpy --with matplotlib python3 figs.py && uv run --quiet --with numpy --with matplotlib python3 fig_skill.py && uv run --quiet --with pyarrow --with numpy --with matplotlib python3 plot_fire.py
F="$ROOT/paper/figures"; cp sea_wildfire_emissions_2026-09-13.png "$F/fig1_map.png"; cp fig1_haze_index_vs_psi.png "$F/fig2_index_psi.png"; cp fig_skill.png "$F/fig3_skill.png"; cp fig2_sources_and_lag.png "$F/fig4_apportionment.png"; cp fig3_season_ranking.png "$F/fig5_season.png"
echo "[9/9] paper"; cd "$ROOT/paper" && uv run --quiet --with typst python3 -c "import typst; typst.compile('paper.typ', output='paper.pdf')" && echo DONE
