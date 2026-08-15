"""Fail-closed compatibility boundary for FCX features in CAD 2.

CAD 2 is a community CAD client.  It may call FCX-Control through
``fcx_client.FcxClient`` but it must never initialize or execute a local copy of
the FCX market engine.  A few legacy admin handlers still reference the old
function names; keeping explicit blockers here makes those handlers fail closed
while the routes are removed from the CAD 2 user interface.
"""

from __future__ import annotations

import json
from typing import Any, NoReturn


LOCAL_FCX_FORBIDDEN_MESSAGE = (
    "Local FCX engine execution is forbidden in CAD 2; use the authenticated "
    "FCX-Control service API"
)


PERSONALITY_PROFILES = {
    name: {}
    for name in (
        "retail",
        "conservative",
        "growth",
        "panic",
        "contrarian",
        "institutional",
        "momentum",
        "value",
        "day_trader",
        "speculator",
        "dividend",
        "short_seller",
        "market_maker",
        "whale",
        "algorithmic",
    )
}

DEFAULT_DISTRIBUTION = {
    "retail": 30.0,
    "conservative": 10.0,
    "growth": 10.0,
    "momentum": 10.0,
    "day_trader": 8.0,
    "value": 8.0,
    "contrarian": 6.0,
    "speculator": 5.0,
    "dividend": 4.0,
    "short_seller": 3.0,
    "institutional": 2.0,
    "market_maker": 2.0,
    "algorithmic": 1.5,
    "whale": 0.5,
    "panic": 0.0,
}

CYCLE_DEFAULTS = {
    "minute": 60,
    "five_minute": 300,
    "fifteen_minute": 900,
    "thirty_minute": 1800,
    "hourly": 3600,
    "six_hour": 21600,
    "daily": 86400,
}


def parse_string_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        raw = value
    else:
        try:
            raw = json.loads(str(value or "[]"))
        except (TypeError, json.JSONDecodeError):
            raw = []
    if not isinstance(raw, list):
        return ()
    return tuple(sorted({str(item).strip().lower() for item in raw if str(item).strip()}))


def parse_distribution(value: Any) -> dict[str, float]:
    if isinstance(value, dict):
        raw = value
    else:
        try:
            raw = json.loads(str(value or "{}"))
        except (TypeError, json.JSONDecodeError):
            raw = {}
    if not isinstance(raw, dict):
        raw = {}
    cleaned: dict[str, float] = {}
    for key in PERSONALITY_PROFILES:
        try:
            cleaned[key] = max(0.0, min(100.0, float(raw.get(key, DEFAULT_DISTRIBUTION.get(key, 0)))))
        except (TypeError, ValueError):
            cleaned[key] = DEFAULT_DISTRIBUTION.get(key, 0.0)
    total = sum(cleaned.values())
    if total <= 0:
        return dict(DEFAULT_DISTRIBUTION)
    return {key: round(number / total * 100.0, 4) for key, number in cleaned.items()}


def _blocked(*_args: Any, **_kwargs: Any) -> NoReturn:
    raise RuntimeError(LOCAL_FCX_FORBIDDEN_MESSAGE)


admin_snapshot = _blocked
apply_dividend = _blocked
apply_stock_split = _blocked
ensure_schema = _blocked
index_constituent_counts = _blocked
run_due_cycles = _blocked
run_manual_cycle = _blocked
run_sandbox = _blocked
seed_investors = _blocked
