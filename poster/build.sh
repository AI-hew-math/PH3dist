#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if command -v tectonic >/dev/null 2>&1; then
  echo "[build] using tectonic"
  tectonic -X compile poster.tex --outdir . 2>&1 | tail -3 || tectonic poster.tex 2>&1 | tail -3
elif command -v lualatex >/dev/null 2>&1; then
  echo "[build] using lualatex (ensure beamerposter installed: tlmgr install beamerposter qrcode)"
  lualatex -interaction=nonstopmode poster.tex >/dev/null
else
  echo "no LaTeX engine found"; exit 1
fi
echo "[build] wrote poster/poster.pdf"
