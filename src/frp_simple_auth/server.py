from __future__ import annotations

from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

from .config import get_global_deny, get_user, list_users
from .models import FrpLoginReq
from .policy import all_domains_allowed, any_domain_forbidden, port_allowed, port_in_ranges
from .reloader import install_signal_handler, safe_reload, start_config_watcher
from .settings import LISTEN_HOST, LISTEN_PORT, log

app = FastAPI()
install_signal_handler()


def reject(reason: str) -> Dict[str, str]:
    return {"reject": True, "reject_reason": reason}


@app.get("/health")
def health():
    return {"ok": True, "users": list_users()}


@app.post("/reload")
def http_reload():
    safe_reload()
    return {"ok": True, "users": list_users()}


@app.post("/handler")
async def handler(request: Request):
    op = request.query_params.get("op", "")
    if not op:
        raise HTTPException(status_code=400, detail="Missing 'op'")

    try:
        body_json = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Bad JSON")

    if op == "Login":
        try:
            body = FrpLoginReq(**body_json)
        except ValidationError as exc:
            log.warning("bad Login JSON: %s", exc)
            raise HTTPException(status_code=400, detail="Bad JSON")

        user_cfg = get_user(body.content.user)
        if not user_cfg:
            return reject("invalid user")

        token = body.content.metas.get("token")
        if token != user_cfg.password:
            return reject("invalid password")

        log.info(
            "Login ok: user=%s addr=%s",
            body.content.user,
            body.content.client_address,
        )
        return {"reject": False, "unchange": True}

    if op == "NewProxy":
        content = body_json.get("content")
        if not isinstance(content, dict):
            raise HTTPException(status_code=400, detail="Bad JSON: missing content")

        if content.get("subdomain"):
            return reject("subdomain routing not permitted")

        username = (content.get("user") or {}).get("user")
        if not username:
            return reject("invalid user")
        user_cfg = get_user(username)
        if not user_cfg:
            return reject("invalid user")

        proxy_type = content.get("proxy_type")
        if proxy_type not in set(user_cfg.allow.proxyTypes):
            return reject(f"proxy_type '{proxy_type}' not allowed")
        global_deny = get_global_deny()
        if proxy_type in set(global_deny.proxyTypes):
            return reject(f"proxy_type '{proxy_type}' globally forbidden")

        if proxy_type in ("tcp", "udp"):
            rp = content.get("remote_port")
            if rp is None:
                return reject("remote_port required for tcp/udp")
            try:
                remote_port = int(rp)
            except Exception:
                return reject("remote_port must be an integer")
            if not user_cfg.allow.remotePorts:
                return reject("no remote ports permitted")
            try:
                if not port_allowed(remote_port, user_cfg.allow.remotePorts):
                    return reject(f"remote_port {remote_port} not permitted")
                if global_deny.remotePorts and port_in_ranges(remote_port, global_deny.remotePorts):
                    return reject(f"remote_port {remote_port} globally forbidden")
            except ValueError as exc:
                log.error("invalid port spec: %s", exc)
                return reject("server config error")

        if proxy_type in ("http", "https"):
            allowed = user_cfg.allow.domains
            if not allowed:
                return reject("no domains allowed for http/https")
            req_domains = content.get("custom_domains") or []
            if not req_domains:
                return reject("custom_domains required for http/https")
            if not all_domains_allowed(req_domains, allowed):
                return reject("requested domain not permitted")
            if global_deny.domains and any_domain_forbidden(req_domains, global_deny.domains):
                return reject("requested domain globally forbidden")

        content.pop("subdomain", None)

        log.info(
            "NewProxy ok: user=%s type=%s name=%s",
            username,
            proxy_type,
            content.get("proxy_name"),
        )
        return {"reject": False, "unchange": False, "content": content}

    return {"reject": False, "unchange": True}


@app.on_event("startup")
def _startup():
    start_config_watcher()
    log.info("listening on %s:%d", LISTEN_HOST, LISTEN_PORT)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=LISTEN_HOST, port=LISTEN_PORT, reload=False)
