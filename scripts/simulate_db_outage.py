"""Controlled failure for the demo: hold an exclusive lock on the history DB.

While this script runs, any `report --save` cannot write to SQLite
("database is locked"), so the run is queued and `status` reports DEGRADED.
When it exits, the lock is released and `recover` can flush the queue.

Usage (second terminal):
    python scripts/simulate_db_outage.py --seconds 30
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from growvest_economics import config, history  # noqa: E402
from growvest_economics.logjson import log      # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--seconds", type=float, default=30)
args = p.parse_args()

history.connect().close()                   # make sure the DB exists
conn = sqlite3.connect(config.DB_PATH, isolation_level=None)
conn.execute("BEGIN EXCLUSIVE")
log("WARN", "simulated_db_outage_started", seconds=args.seconds)
print(f"Database LOCKED for {args.seconds:.0f} s ({config.DB_PATH})", flush=True)
try:
    time.sleep(args.seconds)
finally:
    conn.execute("ROLLBACK")
    conn.close()
    log("INFO", "simulated_db_outage_ended")
    print("Database lock released.", flush=True)
