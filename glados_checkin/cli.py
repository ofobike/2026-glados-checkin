"""Command-line entrypoints for GLaDOS check-in."""

import os

from .app import main, send_heartbeat_check


def run():
    """Run the configured mode."""
    run_mode = (os.environ.get("RUN_MODE") or os.environ.get("GLADOS_RUN_MODE") or "checkin").lower()
    if run_mode in ("heartbeat", "check_heartbeat"):
        send_heartbeat_check()
    else:
        main()
