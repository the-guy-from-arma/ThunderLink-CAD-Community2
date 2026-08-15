"""Railway entry point for the isolated, full CAD 2 application."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from community_config import preflight

    config = preflight()
    print(
        f"CAD 2 isolation preflight passed for community={config.community_id} "
        f"arma_server={config.arma_server_id}",
        flush=True,
    )
    command = [sys.executable, "app.py"]

    os.execv(sys.executable, command)


if __name__ == "__main__":
    main()
