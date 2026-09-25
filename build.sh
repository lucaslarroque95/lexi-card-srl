#!/usr/bin/env bash
# Builds this service's Lambda deployment artifacts under dist/, for
# infra/lambda.tf to pick up:
#
#   dist/layer.zip        - one shared layer: pip deps + this repo's own
#                            packages (routes, services, repositories, ...)
#                            + bootstrap.py/apigw.py. All 45 functions share
#                            this one layer instead of each bundling its own
#                            copy of the same ~40 files.
#   dist/functions/*.zip  - one tiny zip per endpoint, just its own main.py.
set -euo pipefail
cd "$(dirname "$0")"

DIST=dist
# No dedicated venv ships with this repo yet; point PYTHON_BIN at your own
# venv's interpreter for local builds if you have one (same spirit as
# DEPLOY.md's note). CI overrides this to plain python3 already.
PYTHON_BIN="${PYTHON_BIN:-python3}"

rm -rf "$DIST"
mkdir -p "$DIST/layer/python" "$DIST/functions"

echo "installing dependencies into the layer"
"$PYTHON_BIN" -m pip install --quiet --no-cache-dir \
  -r requirements.txt -t "$DIST/layer/python"

echo "copying shared packages into the layer"
cp -r ./{auth,db,middlewares,models,repositories,routes,schemas,services,keys} "$DIST/layer/python/"
cp bootstrap.py apigw.py "$DIST/layer/python/"
find "$DIST/layer/python" -name '__pycache__' -type d -prune -exec rm -rf {} +

python3 ./zip_dir.py "$DIST/layer" "$DIST/layer.zip"

count=0
for dir in */; do
  name="${dir%/}"
  [ -f "$dir/main.py" ] || continue
  work="$(mktemp -d)"
  cp "$dir/main.py" "$work/"
  python3 ./zip_dir.py "$work" "$DIST/functions/$name.zip"
  rm -rf "$work"
  count=$((count + 1))
done

echo "built dist/layer.zip and $count function zips in $DIST/functions/"
