import json

from growvest_economics.__main__ import main


def test_report_table(capsys):
    assert main(["report"]) == 0
    out = capsys.readouterr().out
    for name in ("Free", "Pro", "Premium"):
        assert name in out


def test_report_single_tier_json(capsys):
    assert main(["report", "--tier", "pro", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert list(data) == ["pro"]
    assert round(data["pro"]["gross_margin_usd"], 3) == 23.159


def test_unknown_tier(capsys):
    assert main(["report", "--tier", "enterprise"]) == 2
    assert "enterprise" in capsys.readouterr().err


def test_invalid_data_file_shows_clean_error(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"tiers": {"pro": {
        "name": "Pro", "price_usd": 29, "hosting_cost_usd": -3,
        "support_cost_usd": 1.5, "churn_monthly": 0.06, "cac_usd": 85}}}))
    assert main(["report", "--data", str(bad)]) == 2
    assert "hosting_cost_usd" in capsys.readouterr().err
