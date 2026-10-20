"""Reference values recomputed by hand + regression tests for R-01..R-03.

Hand calculation for Pro (simulated data):
    fee     = 29 * 0.029 + 0.30           = 1.141
    margin  = 29 - 3.20 - 1.50 - 1.141    = 23.159
    margin% = 23.159 / 29                 = 0.7986
    LTV     = 23.159 / 0.06               = 385.98
    payback = 85 / 23.159                 = 3.67 months
    LTV:CAC = 385.98 / 85                 = 4.54

Premium:
    fee     = 79 * 0.029 + 0.30           = 2.591
    margin  = 79 - 6.50 - 4.00 - 2.591    = 65.909
    LTV     = 65.909 / 0.04               = 1647.73
    payback = 160 / 65.909                = 2.43 months
"""

import pytest

from growvest_economics.engine import calculate_all, calculate_tier_economics
from growvest_economics.fees import STRIPE, FeeSchedule
from growvest_economics.tiers import TierAssumptions, load_tiers

approx = pytest.approx


@pytest.fixture
def results():
    return calculate_all(load_tiers())


def test_pro_reference_values(results):
    pro = results["pro"]
    assert pro.payment_fee_usd == approx(1.141)
    assert pro.gross_margin_usd == approx(23.159)
    assert pro.margin_pct == approx(0.7986, abs=1e-4)
    assert pro.ltv_usd == approx(385.98, abs=0.01)
    assert pro.cac_payback_months == approx(3.67, abs=0.01)
    assert pro.ltv_to_cac == approx(4.54, abs=0.01)


def test_premium_reference_values(results):
    prem = results["premium"]
    assert prem.payment_fee_usd == approx(2.591)
    assert prem.gross_margin_usd == approx(65.909)
    assert prem.ltv_usd == approx(1647.73, abs=0.01)
    assert prem.cac_payback_months == approx(2.43, abs=0.01)


def test_free_tier_never_pays_back(results):
    free = results["free"]
    assert free.payment_fee_usd == 0
    assert free.gross_margin_usd == approx(-0.70)
    assert free.margin_pct is None
    assert free.cac_payback_months is None


# ---- Regression tests for the Assignment 3.2 defects --------------------

def test_R01_premium_fee_uses_premium_price_not_pro(results):
    """R-01: spreadsheet computed Premium's fee from Pro's price cell."""
    wrong_fee_from_pro_price = 29 * STRIPE.pct + STRIPE.fixed_usd
    assert results["premium"].payment_fee_usd == approx(79 * STRIPE.pct + STRIPE.fixed_usd)
    assert results["premium"].payment_fee_usd != approx(wrong_fee_from_pro_price)


def test_R02_one_fee_schedule_updates_every_tier():
    """R-02: Stripe fee was a literal in two formulas. Changing it must move all tiers."""
    tiers = load_tiers()
    new_fees = FeeSchedule(pct=0.035, fixed_usd=0.30)
    before = calculate_all(tiers)
    after = calculate_all(tiers, new_fees)
    for key in ("pro", "premium"):
        assert after[key].payment_fee_usd == approx(tiers[key].price_usd * 0.035 + 0.30)
        assert after[key].payment_fee_usd > before[key].payment_fee_usd


def test_R03_churn_typed_as_percent_is_refused():
    """R-03 (simulated): churn typed as 6 instead of 0.06 made LTV 100x too small.
    The tool must refuse it rather than print a plausible wrong LTV."""
    with pytest.raises(ValueError, match="0.06"):
        TierAssumptions(name="Pro", price_usd=29, hosting_cost_usd=3.2,
                        support_cost_usd=1.5, churn_monthly=6, cac_usd=85)


def test_same_function_for_every_tier(results):
    tiers = load_tiers()
    for key, tier in tiers.items():
        assert calculate_tier_economics(tier) == results[key]
