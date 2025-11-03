from __future__ import annotations

from typing import Iterable, List, Optional, Tuple


def parse_port_spec(spec: str) -> Tuple[int, int]:
    spec = spec.strip()
    if "-" in spec:
        a, b = spec.split("-", 1)
        lo, hi = int(a), int(b)
        if lo > hi or lo < 1 or hi > 65535:
            raise ValueError(f"bad port range: {spec}")
        return lo, hi
    port = int(spec)
    if not (1 <= port <= 65535):
        raise ValueError(f"bad port: {spec}")
    return port, port


def port_allowed(port: int, specs: Iterable[str]) -> bool:
    for spec in specs:
        lo, hi = parse_port_spec(spec)
        if lo <= port <= hi:
            return True
    return False


def port_in_ranges(port: int, specs: Iterable[str]) -> bool:
    for spec in specs:
        lo, hi = parse_port_spec(spec)
        if lo <= port <= hi:
            return True
    return False


def _domain_allowed(requested: str, allowed: Iterable[str]) -> bool:
    req = requested.lower().strip(".")
    for candidate in allowed:
        cand = candidate.lower().strip(".")
        if cand == req:
            return True
        if cand.startswith("*."):
            base = cand[2:]
            if req.endswith("." + base) and req != base:
                return True
    return False


def all_domains_allowed(requested: Optional[List[str]], allowed: List[str]) -> bool:
    if not requested:
        return False
    return all(_domain_allowed(domain, allowed) for domain in requested)


def any_domain_forbidden(requested: Optional[List[str]], forbidden: List[str]) -> bool:
    if not requested:
        return False
    for req in requested:
        if _domain_allowed(req, forbidden):
            return True
    return False
