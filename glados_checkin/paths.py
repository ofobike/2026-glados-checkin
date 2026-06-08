"""Filesystem paths used by the check-in app."""

import os
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_RUNTIME_DIR = PROJECT_ROOT if (PROJECT_ROOT / ".git").exists() else Path.cwd()


def _path_from_env(name, default):
    raw = os.environ.get(name)
    if raw and raw.strip():
        return Path(raw).expanduser().resolve()
    return default


DATA_FILE = _path_from_env("GLADOS_DATA_FILE", DEFAULT_RUNTIME_DIR / "glados_data.json")
EXPORT_FILE = _path_from_env("GLADOS_EXPORT_FILE", DEFAULT_RUNTIME_DIR / "glados_checkin_log.csv")
