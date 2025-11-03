from __future__ import annotations

from typing import Dict, List, Optional

import yaml

from .models import AppCfg, GlobalDeny, UserCfg
from .settings import CONFIG_PATH, log

_cfg: AppCfg | None = None
_users: Dict[str, UserCfg] = {}
_global_deny: GlobalDeny = GlobalDeny()


def load_config() -> None:
    global _cfg, _users, _global_deny
    with open(CONFIG_PATH, "r") as f:
        raw = yaml.safe_load(f) or {}
    parsed = AppCfg(**raw)
    users = {user.user: user for user in parsed.users}

    _cfg = parsed
    _users = users
    _global_deny = parsed.globalDeny
    log.info("config loaded: users=%s", list(_users.keys()))


def get_user(username: str) -> Optional[UserCfg]:
    return _users.get(username)


def list_users() -> List[str]:
    return list(_users.keys())


def get_global_deny() -> GlobalDeny:
    return _global_deny


try:
    load_config()
except Exception as exc:
    log.error("failed to load %s: %s", CONFIG_PATH, exc)
