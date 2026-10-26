"""Structured logging: one JSON object per line in runtime/growvest.log.

Example line:
{"ts": "2026-10-25T21:40:02Z", "level": "ERROR", "event": "history_save_failed",
 "error": "database is locked", "queued_to": "runtime/pending_runs.jsonl"}
"""

import json
from datetime import datetime, timezone

from . import config


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(level: str, event: str, **fields) -> dict:
    record = {"ts": now_iso(), "level": level, "event": event, **fields}
    try:
        config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(config.LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except OSError:
        # Logging must never crash the calculation.
        pass
    return record


def read_log(last: int = 20) -> list:
    if not config.LOG_PATH.exists():
        return []
    with open(config.LOG_PATH, encoding="utf-8") as f:
        lines = f.readlines()[-last:]
    return [json.loads(line) for line in lines if line.strip()]
