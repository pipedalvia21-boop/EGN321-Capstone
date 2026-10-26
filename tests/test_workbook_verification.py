"""Capstone Part 3: prove the calculation against the ORIGINAL workbook.

Expected values are read straight from original_workbook/GrowVest_Unit_Economics_v1.xlsx
(cached values from the last recalculation), not typed into the test.

    Test 1  Known-correct case   Pro tier: workbook == application
    Test 2  Problem / edge case  Premium fee (R-01): workbook is wrong, app is right
    Test 3  Invalid input        Scenario churn = 6 (R-03): workbook prints an LTV, app refuses
    Test 4  Student-created      Free tier: workbook divides by price 0 and hides it as "n/a"
                                 by hand; app reports n/a by rule and never pays back
"""

from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from growvest_economics.engine import calculate_all          # noqa: E402
from growvest_economics.fees import STRIPE                   # noqa: E402
from growvest_economics.tiers import TierAssumptions, load_tiers  # noqa: E402

WORKBOOK = Path(__file__).resolve().parent.parent / "original_workbook" / "GrowVest_Unit_Economics_v1.xlsx"
approx = pytest.approx


@pytest.fixture(scope="module")
def wb():
    return openpyxl.load_workbook(WORKBOOK, data_only=True)


@pytest.fixture(scope="module")
def app():
    return calculate_all(load_tiers())


def ue(wb, row, col):
    return wb["Unit Economics"][f"{col}{row}"].value


def test_workbook_inputs_match_application_inputs(wb):
    """Both systems start from the same assumptions, so differences come from logic only."""
    a = wb["Assumptions"]
    tiers = load_tiers()
    for col, key in (("B", "free"), ("C", "pro"), ("D", "premium")):
        t = tiers[key]
        assert a[f"{col}2"].value == t.price_usd
        assert a[f"{col}3"].value == t.hosting_cost_usd
        assert a[f"{col}4"].value == t.support_cost_usd
        assert a[f"{col}5"].value == t.churn_monthly
        assert a[f"{col}6"].value == t.cac_usd


# Test 1: known-correct case ---------------------------------------------
def test_1_known_correct_pro_matches_workbook(wb, app):
    pro = app["pro"]
    assert pro.payment_fee_usd == approx(ue(wb, 2, "C"))
    assert pro.gross_margin_usd == approx(ue(wb, 3, "C"))
    assert pro.margin_pct == approx(ue(wb, 4, "C"))
    assert pro.ltv_usd == approx(ue(wb, 5, "C"))
    assert pro.cac_payback_months == approx(ue(wb, 6, "C"))
    assert pro.ltv_to_cac == approx(ue(wb, 7, "C"))


# Test 2: problem case (R-01) --------------------------------------------
def test_2_premium_fee_workbook_wrong_app_correct(wb, app):
    workbook_fee = ue(wb, 2, "D")
    correct_fee = 79 * STRIPE.pct + STRIPE.fixed_usd           # 2.591
    assert workbook_fee == approx(29 * 0.029 + 0.30)           # used Pro's $29
    assert app["premium"].payment_fee_usd == approx(correct_fee)
    # The workbook overstated Premium margin and LTV:
    assert ue(wb, 3, "D") - app["premium"].gross_margin_usd == approx(1.45)
    assert ue(wb, 5, "D") > app["premium"].ltv_usd


# Test 3: invalid input (R-03) -------------------------------------------
def test_3_churn_as_whole_percent_workbook_silent_app_refuses(wb):
    scenario = wb["Scenario"]
    assert scenario["B4"].value == 6                           # analyst meant 6%
    assert scenario["B5"].value == approx(3.86, abs=0.01)      # silently 100x too small
    with pytest.raises(ValueError, match="0.06"):
        TierAssumptions(name="Pro", price_usd=29, hosting_cost_usd=3.2,
                        support_cost_usd=1.5, churn_monthly=scenario["B4"].value,
                        cac_usd=85)


# Test 4: student-created -------------------------------------------------
def test_4_free_tier_agrees_and_never_pays_back(wb, app):
    free = app["free"]
    assert free.gross_margin_usd == approx(ue(wb, 3, "B"))
    assert free.ltv_usd == approx(ue(wb, 5, "B"))
    assert ue(wb, 6, "B") == "n/a"          # hand-typed text in the workbook
    assert free.cac_payback_months is None  # rule in engine: margin <= 0 never pays back
