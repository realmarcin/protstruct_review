#!/usr/bin/env bash
# Mirror the PHENIX documentation into ref/phenix_docs/ for offline reference.
#
# Re-runnable: wget --mirror will skip unchanged files on subsequent runs.
# Polite: 1s base wait + --random-wait to avoid hammering the server.
#
# Usage:
#   bash ref/download_phenix_docs.sh
#
# Expected footprint: ~20-50 MB, ~200-300 HTML pages.
# Sanity check after run:
#   find ref/phenix_docs -name '*.html' | wc -l   # should be >= 100

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/phenix_docs"

mkdir -p "${OUT_DIR}"

# Seed URLs for the recursive mirror. --no-parent keeps wget inside /documentation/.
# We pass the top-level /documentation/ URL as the primary seed so recursion reaches
# every linked overview, reference, and tutorial page. Additional seeds below are
# belt-and-suspenders in case any of them are not linked from the index page.
SEEDS=(
  "https://phenix-online.org/documentation/"
  "https://phenix-online.org/documentation/index.html"
  "https://phenix-online.org/documentation/overviews/xray_index.html"
  "https://phenix-online.org/documentation/overviews/cryo-em_index.html"
  "https://phenix-online.org/documentation/overviews/predicted_models_index.html"
  "https://phenix-online.org/documentation/tutorials.html"
  "https://phenix-online.org/documentation/reference/index.html"
  "https://phenix-online.org/documentation/phenix_index.html"
  "https://phenix-online.org/documentation/faqs/index.html"
)

wget \
  --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --no-parent \
  --accept-regex='phenix-online\.org/documentation/' \
  --wait=1 \
  --random-wait \
  --tries=3 \
  --timeout=30 \
  --user-agent="protstruct_review-docs-mirror (offline reference copy)" \
  --directory-prefix="${OUT_DIR}" \
  --no-verbose \
  "${SEEDS[@]}"

echo ""
echo "=== Mirror complete ==="
echo "Output: ${OUT_DIR}"
echo "HTML pages: $(find "${OUT_DIR}" -name '*.html' | wc -l | tr -d ' ')"
echo "Total size: $(du -sh "${OUT_DIR}" | awk '{print $1}')"
