#!/usr/bin/env bash
# Regenerates /pages from /config + src/templates. Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 src/build.py
