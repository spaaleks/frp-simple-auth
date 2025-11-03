#!/bin/bash
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "${ROOT_DIR}/.." || exit 1

set -e
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

python3 src/frp_simple_auth.py
