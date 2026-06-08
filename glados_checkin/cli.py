"""Command-line entrypoints for check-in and Bark automation tasks."""

import os


def run():
    """Run the configured mode."""
    run_mode = (
        os.environ.get("RUN_MODE")
        or os.environ.get("GLADOS_RUN_MODE")
        or "checkin"
    ).strip().lower().replace("-", "_")

    if run_mode in ("checkin", "glados", "glados_checkin"):
        from .app import main

        main()
    elif run_mode in ("heartbeat", "check_heartbeat"):
        from .app import send_heartbeat_check

        send_heartbeat_check()
    elif run_mode in ("morning", "morning_report", "daily_report", "bark_morning"):
        from .morning import send_morning_report

        send_morning_report()
    else:
        raise SystemExit(f"Unknown RUN_MODE: {run_mode}")
