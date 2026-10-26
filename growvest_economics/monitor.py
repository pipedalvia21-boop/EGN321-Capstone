"""Health checks and business alerts.

Health state (worst wins):
    OK        data valid, database reachable, nothing pending, last run recent
    STALE     no saved run within STALE_AFTER_HOURS
    DEGRADED  runs are waiting in the recovery queue
    FAILED    data file invalid or database unreachable

Alerts (paid tiers only):
    margin % below MIN_MARGIN_PCT, LTV:CAC below MIN_LTV_TO_CAC,
    CAC payback longer than MAX_PAYBACK_MONTHS.
"""

import sqlite3
from datetime import datetime, timezone

from . import config, history
from .engine import calculate_all
from .tiers import load_tiers

ORDER = ["OK", "STALE", "DEGRADED", "FAILED"]


def check_alerts(results: dict) -> list:
    alerts = []
    for key, r in results.items():
        if r.price_usd == 0:
            continue
        if r.margin_pct is not None and r.margin_pct < config.MIN_MARGIN_PCT:
            alerts.append(f"{key}: margin {r.margin_pct:.1%} below {config.MIN_MARGIN_PCT:.0%}")
        if r.ltv_to_cac is not None and r.ltv_to_cac < config.MIN_LTV_TO_CAC:
            alerts.append(f"{key}: LTV:CAC {r.ltv_to_cac:.1f}x below {config.MIN_LTV_TO_CAC:.1f}x")
        if r.cac_payback_months is None:
            alerts.append(f"{key}: never recovers its CAC")
        elif r.cac_payback_months > config.MAX_PAYBACK_MONTHS:
            alerts.append(f"{key}: payback {r.cac_payback_months:.1f} mo above "
                          f"{config.MAX_PAYBACK_MONTHS:.0f} mo")
    return alerts


def _age_hours(ts: str) -> float:
    then = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - then).total_seconds() / 3600


def health(data_file=None) -> dict:
    checks, state = {}, "OK"

    def worse(s):
        nonlocal state
        if ORDER.index(s) > ORDER.index(state):
            state = s

    alerts = []
    try:
        results = calculate_all(load_tiers(data_file) if data_file else load_tiers())
        checks["data"] = "OK"
        alerts = check_alerts(results)
    except (ValueError, TypeError, OSError) as e:
        checks["data"] = f"FAILED: {e}"
        worse("FAILED")

    try:
        ts = history.last_run_ts()
        checks["database"] = "OK"
        if ts is None:
            checks["last_run"] = "none saved yet"
            worse("STALE")
        else:
            age = _age_hours(ts)
            checks["last_run"] = f"{ts} ({age:.1f} h ago)"
            if age > config.STALE_AFTER_HOURS:
                worse("STALE")
    except (sqlite3.Error, OSError) as e:
        checks["database"] = f"FAILED: {e}"
        worse("FAILED")

    pending = history.pending_count()
    checks["pending_runs"] = pending
    if pending:
        worse("DEGRADED")

    return {"state": state, "checks": checks, "alerts": alerts}
