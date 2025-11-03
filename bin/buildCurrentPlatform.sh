#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller

pyinstaller --onefile --name frp-simple-auth src/frp_simple_auth.py

platform_tag="$(python3 - <<'PY'
import platform
system = platform.system().lower()
arch = platform.machine().lower()
print(f"{system}-{arch}")
PY
)"

mkdir -p dist
cp dist/frp-simple-auth "dist/frp-simple-auth.${platform_tag}"
echo "Built binary available at dist/frp-simple-auth and dist/frp-simple-auth.${platform_tag}"
