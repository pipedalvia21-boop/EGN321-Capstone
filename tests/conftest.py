import pytest

from growvest_economics import config


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    """Every test gets its own database, log and recovery queue."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "history.db")
    monkeypatch.setattr(config, "LOG_PATH", tmp_path / "growvest.log")
    monkeypatch.setattr(config, "PENDING_PATH", tmp_path / "pending.jsonl")
    monkeypatch.setattr(config, "DB_TIMEOUT_S", 0.1)
