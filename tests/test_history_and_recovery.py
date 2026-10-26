"""SQLite history, structured logs, health states and failure recovery."""

import json
import sqlite3

import pytest

from growvest_economics import config, history, monitor
from growvest_economics.__main__ import main
from growvest_economics.engine import calculate_all
from growvest_economics.logjson import read_log
from growvest_economics.tiers import load_tiers


def lock_db():
    history.connect().close()
    conn = sqlite3.connect(config.DB_PATH, isolation_level=None)
    conn.execute("BEGIN EXCLUSIVE")
    return conn


def test_save_and_read_history():
    out = history.save_run(calculate_all(load_tiers()), "sim.json")
    assert out == {"saved": True, "run_id": 1}
    rows = history.list_runs("pro")
    assert len(rows) == 1
    assert rows[0][3] == pytest.approx(23.159)


def test_status_is_stale_before_any_run_then_ok():
    assert monitor.health()["state"] == "STALE"
    history.save_run(calculate_all(load_tiers()), "sim.json")
    assert monitor.health()["state"] == "OK"


def test_failure_detection_and_recovery():
    """Failure -> detection -> evidence -> recovery -> verification."""
    lock = lock_db()
    # Failure: DB locked, save cannot complete, but nothing is lost.
    out = history.save_run(calculate_all(load_tiers()), "sim.json")
    assert out["saved"] is False and out["queued"] is True
    # Detection: health shows DEGRADED with one pending run.
    assert history.pending_count() == 1
    assert monitor.health()["state"] in ("DEGRADED", "FAILED")
    # Evidence: an ERROR line in the structured log.
    assert any(r["event"] == "history_save_failed" for r in read_log())
    # Recovery: lock released, queue flushed.
    lock.execute("ROLLBACK")
    lock.close()
    assert history.recover()["recovered"] == 1
    # Verification: queue empty, run in DB marked 'recovered', state OK.
    assert history.pending_count() == 0
    assert history.list_runs("pro")[0][2] == "recovered"
    assert monitor.health()["state"] == "OK"
    assert any(r["event"] == "recover_succeeded" for r in read_log())


def test_recover_keeps_queue_if_db_still_down():
    lock = lock_db()
    history.save_run(calculate_all(load_tiers()), "sim.json")
    with pytest.raises(sqlite3.Error):
        history.recover()
    assert history.pending_count() == 1     # nothing thrown away
    lock.execute("ROLLBACK")
    lock.close()


def test_alert_fires_when_threshold_raised(monkeypatch):
    results = calculate_all(load_tiers())
    assert monitor.check_alerts(results) == []          # default thresholds pass
    monkeypatch.setattr(config, "MIN_MARGIN_PCT", 0.85)
    alerts = monitor.check_alerts(results)
    assert any(a.startswith("pro: margin") for a in alerts)
    assert any(a.startswith("premium: margin") for a in alerts)
    assert not any(a.startswith("free") for a in alerts)  # free tier exempt


def test_cli_save_history_status(capsys):
    assert main(["report", "--save"]) == 0
    assert "run #1" in capsys.readouterr().err
    assert main(["history", "--tier", "premium"]) == 0
    assert "65.91" in capsys.readouterr().out
    assert main(["status", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "OK"


def test_cli_malformed_json_refused(tmp_path, capsys):
    bad = tmp_path / "broken.json"
    bad.write_text('{"tiers": {"pro": ')
    assert main(["report", "--data", str(bad)]) == 2
    assert "REFUSED" in capsys.readouterr().err
    assert read_log()[-1]["event"] == "input_refused"
