"""Strict identity boundary for the second ThunderLink CAD community."""
from __future__ import annotations

import os
from dataclasses import dataclass

from database_connections import probe_environment, required_url


def _required(name: str) -> str:
    value = str(os.environ.get(name) or "").strip()
    if not value:
        raise RuntimeError(f"{name} is required for CAD 2")
    return value


def _bool(name: str, default: bool = False) -> bool:
    raw = str(os.environ.get(name, "1" if default else "0")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class CommunityConfig:
    community_id: str
    arma_server_id: str
    arma_bridge_api_key: str
    fcx_api_url: str
    fcx_api_key: str
    fcx_community_id: str
    fcx_remote_market_enabled: bool
    fcx_global_admin_enabled: bool

    @classmethod
    def load(cls) -> "CommunityConfig":
        role = str(os.environ.get("APP_DATABASE_ROLE") or "").strip().lower()
        if role != "cad2":
            raise RuntimeError("APP_DATABASE_ROLE must be cad2")

        community_id = _required("COMMUNITY_ID").lower()
        forbidden = {"default", "faircroft", "cad1", "community_1"}
        if community_id in forbidden:
            raise RuntimeError("CAD 2 COMMUNITY_ID cannot identify the Faircroft/CAD 1 community")

        arma_server_id = _required("ARMA_SERVER_ID")
        if arma_server_id.strip().lower() in forbidden:
            raise RuntimeError("CAD 2 ARMA_SERVER_ID cannot use a CAD 1/default server identity")

        fcx_community_id = _required("FCX_COMMUNITY_ID").lower()
        if fcx_community_id != community_id:
            raise RuntimeError("FCX_COMMUNITY_ID must exactly match COMMUNITY_ID")

        remote_market_enabled = _bool("FCX_REMOTE_MARKET_ENABLED", True)
        if not remote_market_enabled:
            raise RuntimeError(
                "FCX_REMOTE_MARKET_ENABLED must remain enabled for the isolated CAD 2 service"
            )
        if _bool("FCX_GLOBAL_ADMIN_ENABLED", False):
            raise RuntimeError(
                "FCX_GLOBAL_ADMIN_ENABLED cannot be enabled in CAD 2; use FCX-Control"
            )
        if _bool("FCX_RUN_INTEGRATED_ENGINE", False):
            raise RuntimeError(
                "FCX_RUN_INTEGRATED_ENGINE cannot run inside the isolated CAD 2 service"
            )

        owner_email = _required("OWNER_EMAIL").lower()
        owner_password = _required("OWNER_PASSWORD")
        owner_name = _required("OWNER_NAME")
        placeholders = [name for name, value in (
            ("OWNER_EMAIL", owner_email),
            ("OWNER_PASSWORD", owner_password),
            ("OWNER_NAME", owner_name),
        ) if value.upper().startswith("CHANGE_ME")]
        if placeholders:
            raise RuntimeError(
                f"Replace placeholder CAD 2 owner variables: {', '.join(placeholders)}"
            )
        if "@" not in owner_email or owner_email.startswith("@") or owner_email.endswith("@"):
            raise RuntimeError("OWNER_EMAIL must be a valid email address")

        required_url("DATABASE_URL")
        return cls(
            community_id=community_id,
            arma_server_id=arma_server_id,
            arma_bridge_api_key=_required("ARMA_BRIDGE_API_KEY"),
            fcx_api_url=_required("FCX_API_URL").rstrip("/"),
            fcx_api_key=_required("FCX_API_KEY"),
            fcx_community_id=fcx_community_id,
            fcx_remote_market_enabled=remote_market_enabled,
            fcx_global_admin_enabled=False,
        )

    def verify_database_connection(self) -> None:
        probe = probe_environment(
            "DATABASE_URL",
            application_name=f"thunderlink-{self.community_id}-startup",
        )
        if not probe.connected:
            raise RuntimeError(
                f"CAD 2 database preflight failed: {probe.error_type or 'connection_failed'}"
            )


def preflight() -> CommunityConfig:
    config = CommunityConfig.load()
    config.verify_database_connection()
    from fcx_client import FcxClient

    bootstrap = FcxClient(config).bootstrap()
    community = bootstrap.get("community") if isinstance(bootstrap.get("community"), dict) else {}
    remote_community = str(bootstrap.get("community_id") or community.get("community_id") or "").strip().lower()
    if remote_community != config.community_id:
        raise RuntimeError("FCX credential is not assigned to this CAD 2 community")
    return config
