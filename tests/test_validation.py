import json

import pytest

from growvest_economics.fees import FeeSchedule
from growvest_economics.tiers import TierAssumptions, load_tiers

GOOD = dict(name="Pro", price_usd=29, hosting_cost_usd=3.2,
            support_cost_usd=1.5, churn_monthly=0.06, cac_usd=85)


def make(**overrides):
    return TierAssumptions(**{**GOOD, **overrides})


def test_valid_tier_loads():
    assert make().price_usd == 29


def test_free_tier_price_zero_is_allowed():
    assert make(price_usd=0).is_free


@pytest.mark.parametrize("field", ["price_usd", "hosting_cost_usd", "support_cost_usd", "cac_usd"])
def test_negative_values_rejected_and_named(field):
    with pytest.raises(ValueError, match=field):
        make(**{field: -1})


@pytest.mark.parametrize("churn", [0, -0.1, 1.5, 6])
def test_churn_outside_fraction_rejected(churn):
    with pytest.raises(ValueError, match="churn_monthly"):
        make(churn_monthly=churn)


@pytest.mark.parametrize("bad", ["29", None, True])
def test_non_numeric_rejected(bad):
    with pytest.raises(TypeError, match="price_usd"):
        make(price_usd=bad)


def test_empty_name_rejected():
    with pytest.raises(ValueError):
        make(name="  ")


def test_fee_schedule_validation():
    with pytest.raises(ValueError):
        FeeSchedule(pct=2.9, fixed_usd=0.30)   # percent typed as whole number
    with pytest.raises(ValueError):
        FeeSchedule(pct=0.029, fixed_usd=-1)


def test_loader_rejects_misspelled_field(tmp_path):
    bad = {"tiers": {"pro": {**GOOD, "hostng_cost_usd": 1}}}
    path = tmp_path / "t.json"
    path.write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="hostng_cost_usd"):
        load_tiers(path)


def test_default_data_file_loads_three_tiers():
    assert set(load_tiers()) == {"free", "pro", "premium"}
