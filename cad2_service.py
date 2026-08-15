"""Diagnostic boundary for the isolated CAD 2 Railway service.

CAD 2 probes its own PostgreSQL service directly. FCX is intentionally checked
only through the authenticated FCX-Control API; this process never receives or
uses an FCX database URL.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from community_config import CommunityConfig
from database_connections import probe_environment
from fcx_client import FcxClient


app = FastAPI(title="Faircroft CAD 2 Connection Boundary", version="1.0.0")


def _health() -> dict[str, Any]:
    try:
        config = CommunityConfig.load()
    except Exception as exc:
        return {
            "ok": False,
            "service": "cad2",
            "role_guard": False,
            "error_type": type(exc).__name__,
        }
    cad2_database = probe_environment(
        "DATABASE_URL",
        application_name=f"thunderlink-{config.community_id}-health",
    )
    fcx_connected = False
    fcx_error_type = ""
    try:
        bootstrap = FcxClient(config).bootstrap()
        community = bootstrap.get("community") if isinstance(bootstrap.get("community"), dict) else {}
        remote_id = str(
            bootstrap.get("community_id") or community.get("community_id") or ""
        ).strip().lower()
        fcx_connected = remote_id == config.community_id
        if not fcx_connected:
            fcx_error_type = "community_mismatch"
    except Exception as exc:
        fcx_error_type = type(exc).__name__
    return {
        "ok": bool(cad2_database.connected and fcx_connected),
        "service": "cad2",
        "role_guard": True,
        "community_id": config.community_id,
        "cad2_database": cad2_database.public_payload(),
        "fcx_api": {
            "configured": bool(config.fcx_api_url and config.fcx_api_key),
            "connected": fcx_connected,
            "error_type": fcx_error_type,
        },
        "boundaries": {
            "cad1_database_access": False,
            "direct_fcx_database_access": False,
            "fcx_transport": "authenticated_api",
        },
    }


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Faircroft CAD 2",
        "state": "connection-boundary",
    }


@app.get("/api/health")
def health() -> JSONResponse:
    payload = _health()
    return JSONResponse(payload, status_code=200 if payload.get("ok") else 503)
