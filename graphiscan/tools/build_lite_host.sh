#!/bin/sh
set -eu
python -m pip install --no-cache-dir -r requirements-lite.txt
python tools/fetch_v1_lite_bundle.py
