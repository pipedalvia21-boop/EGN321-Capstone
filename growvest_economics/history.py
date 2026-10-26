"""SQLite history of every saved report run, with a recovery queue.

Tables:
    runs(id, ts, data_file, source)                     one row per saved run
    tier_results(run_id, tier, price_usd, payment_fee_usd, gross_margin_usd,
                 margin_pct, ltv_usd, cac_payback_months, ltv_to_cac)

If the database cannot be written (locked, missing, read-only), the run is not
lost: it is appended to runtime/pending_runs.jsonl and an ERROR is logged.
`recover` later writes every pending run into the database and empties the queue.
"""

import json
import sqlite3
from dataclasses import asdict

from . import config
from .logjson import log, now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    data_file TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'live'
);
CREATE TABLE IF NOT EXISTS tier_results (
    run_id INTEGER NOT NULL REFERENCES runs(id),
    tier TEXT NOT NULL,
    price_usd REAL, payment_fee_usd REAL, gross_margin_usd REAL,
    margin_pct REAL, ltv_usd REAL, cac_payback_months REAL, ltv_to_cac REAL
);
"""

FIELDS = ("price_usd", "payment_fee_usd", "gross_margin_usd", "margin_pct",
          "ltv_usd", "cac_payback_months", "ltv_to_cac")


def connect():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=config.DB_TIMEOUT_S)
    conn.executescript(SCHEMA)
    return conn


def _write(conn, ts, data_file, results, source):
    cur = conn.execute("INSERT INTO runs (ts, data_file, source) VALUES (?, ?, ?)",
                       (ts, data_file, source))
    run_id = cur.lastrowid
    for key, r in results.items():
        conn.execute(
            f"INSERT INTO tier_results (run_id, tier, {', '.join(FIELDS)}) "
            f"VALUES (?, ?, {', '.join('?' * len(FIELDS))})",
            (run_id, key, *(r[f] for f in FIELDS)))
    return run_id


def _as_dicts(results: dict) -> dict:
    return {k: (v if isinstance(v, dict) else asdict(v)) for k, v in results.items()}


def save_run(results: dict, data_file: str) -> dict:
    """Save one run. Returns {"saved": True, "run_id": n} or {"saved": False, "queued": True}."""
    ts = now_iso()
    rows = _as_dicts(results)
    try:
        conn = connect()
        with conn:
            run_id = _write(conn, ts, str(data_file), rows, "live")
        conn.close()
        log("INFO", "history_saved", run_id=run_id, tiers=list(rows))
        return {"saved": True, "run_id": run_id}
    except (sqlite3.Error, OSError) as e:
        _queue(ts, str(data_file), rows)
        log("ERROR", "history_save_failed", error=str(e), queued_to=str(config.PENDING_PATH))
        return {"saved": False, "queued": True, "error": str(e)}


def _queue(ts, data_file, rows):
    config.PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.PENDING_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts, "data_file": data_file, "results": rows}) + "\n")


def pending_count() -> int:
    if not config.PENDING_PATH.exists():
        return 0
    with open(config.PENDING_PATH, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def recover() -> dict:
    """Write every queued run into the database, then empty the queue."""
    n = pending_count()
    if n == 0:
        log("INFO", "recover_nothing_pending")
        return {"recovered": 0, "run_ids": []}
    with open(config.PENDING_PATH, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    try:
        conn = connect()
        with conn:  # all or nothing
            ids = [_write(conn, it["ts"], it["data_file"], it["results"], "recovered")
                   for it in items]
        conn.close()
    except (sqlite3.Error, OSError) as e:
        log("ERROR", "recover_failed", error=str(e), pending=n)
        raise
    config.PENDING_PATH.unlink()
    log("INFO", "recover_succeeded", recovered=len(ids), run_ids=ids)
    return {"recovered": len(ids), "run_ids": ids}


def list_runs(tier: str = "pro", limit: int = 20) -> list:
    conn = connect()
    rows = conn.execute(
        "SELECT r.id, r.ts, r.source, t.gross_margin_usd, t.margin_pct, t.ltv_usd, "
        "t.cac_payback_months, t.ltv_to_cac FROM runs r JOIN tier_results t "
        "ON t.run_id = r.id WHERE t.tier = ? ORDER BY r.id DESC LIMIT ?",
        (tier, limit)).fetchall()
    conn.close()
    return rows


def last_run_ts():
    conn = connect()
    row = conn.execute("SELECT ts FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return row[0] if row else None
