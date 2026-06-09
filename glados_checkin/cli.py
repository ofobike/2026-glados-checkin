"""Command-line entrypoints for check-in and Bark automation tasks."""

import os

from glados_checkin.utils import log


def run():
    """Run the configured mode."""
    run_mode = (
        os.environ.get("RUN_MODE")
        or os.environ.get("GLADOS_RUN_MODE")
        or "checkin"
    ).strip().lower().replace("-", "_")
    log(f"🚦 RUN_MODE={run_mode}")

    if run_mode in ("checkin", "glados", "glados_checkin"):
        from .app import main

        main()
    elif run_mode in ("heartbeat", "check_heartbeat"):
        from .app import send_heartbeat_check

        send_heartbeat_check()
    elif run_mode in ("morning", "morning_report", "daily_report", "bark_morning"):
        from .morning import send_morning_report

        send_morning_report()
    elif run_mode in ("reminder", "important_day", "important_days", "day_reminder"):
        from .app import send_important_day_reminders

        send_important_day_reminders()
    elif run_mode in ("actions_monitor", "action_monitor", "github_actions", "actions"):
        from .app import send_actions_monitor

        send_actions_monitor()
    elif run_mode in ("habit", "habit_reminder", "bark_habit"):
        from .habit import send_habit_reminder

        send_habit_reminder()
    else:
        raise SystemExit(f"Unknown RUN_MODE: {run_mode}")
