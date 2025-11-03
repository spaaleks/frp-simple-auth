from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("frp-simple-auth")

CONFIG_PATH = os.environ.get("FRP_AUTH_CONFIG", "./auth.yml")
LISTEN_HOST = os.environ.get("FRP_AUTH_LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("FRP_AUTH_LISTEN_PORT", "7005"))
