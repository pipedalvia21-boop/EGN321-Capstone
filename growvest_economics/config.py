"""All tunable settings in one place.

Every value can be overridden with an environment variable, so a setting can
be changed without editing code (e.g. GROWVEST_MIN_MARGIN_PCT=0.75).
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Where runtime files live (database, logs, pending queue). Not committed.
RUNTIME_DIR = Path(os.environ.get("GROWVEST_HOME", PROJECT_ROOT / "runtime"))

DB_PATH = Path(os.environ.get("GROWVEST_DB", RUNTIME_DIR / "history.db"))
LOG_PATH = Path(os.environ.get("GROWVEST_LOG", RUNTIME_DIR / "growvest.log"))
PENDING_PATH = Path(os.environ.get("GROWVEST_PENDING", RUNTIME_DIR / "pending_runs.jsonl"))

# How long (seconds) to wait for the database before giving up on a save.
DB_TIMEOUT_S = float(os.environ.get("GROWVEST_DB_TIMEOUT_S", "1.0"))

# A saved run older than this makes `status` report STALE.
STALE_AFTER_HOURS = float(os.environ.get("GROWVEST_STALE_AFTER_HOURS", "24"))

# Business alerts, checked on paid tiers only (the Free tier is expected to lose money).
MIN_MARGIN_PCT = float(os.environ.get("GROWVEST_MIN_MARGIN_PCT", "0.70"))   # 70%
MIN_LTV_TO_CAC = float(os.environ.get("GROWVEST_MIN_LTV_TO_CAC", "3.0"))    # 3x
MAX_PAYBACK_MONTHS = float(os.environ.get("GROWVEST_MAX_PAYBACK_MONTHS", "12"))
