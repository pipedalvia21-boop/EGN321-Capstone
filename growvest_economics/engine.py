"""The one shared calculation engine.

calculate_tier_economics() is the ONLY place the unit-economics math lives.
It receives one tier record at a time, so it can only ever use that tier's
own price. There is no per-tier copy of the formula to fall out of sync.

Formulas (all per user, per month unless noted):
    payment_fee     = price * fee.pct + fee.fixed        (0 if price is 0)
    gross_margin    = price - hosting - support - payment_fee
    margin_pct      = gross_margin / price               (None for free tier)
    ltv             = gross_margin / churn               (lifetime, in USD)
    cac_payback     = cac / gross_margin                 (months; None if margin <= 0)
    ltv_to_cac      = ltv / cac                          (None if cac is 0)
"""

from dataclasses import dataclass
from typing import Optional

from .fees import STRIPE, FeeSchedule
from .tiers import TierAssumptions


@dataclass(frozen=True)
class TierEconomics:
    name: str
    price_usd: float
    payment_fee_usd: float
    gross_margin_usd: float
    margin_pct: Optional[float]
    ltv_usd: float
    cac_payback_months: Optional[float]
    ltv_to_cac: Optional[float]


def calculate_tier_economics(tier: TierAssumptions,
                             fees: FeeSchedule = STRIPE) -> TierEconomics:
    payment_fee = fees.fee_for(tier.price_usd)  # R-01: this tier's own price
    gross_margin = (tier.price_usd - tier.hosting_cost_usd
                    - tier.support_cost_usd - payment_fee)

    margin_pct = None if tier.is_free else gross_margin / tier.price_usd
    ltv = gross_margin / tier.churn_monthly
    payback = tier.cac_usd / gross_margin if gross_margin > 0 else None
    ltv_to_cac = ltv / tier.cac_usd if tier.cac_usd > 0 else None

    return TierEconomics(
        name=tier.name,
        price_usd=tier.price_usd,
        payment_fee_usd=payment_fee,
        gross_margin_usd=gross_margin,
        margin_pct=margin_pct,
        ltv_usd=ltv,
        cac_payback_months=payback,
        ltv_to_cac=ltv_to_cac,
    )


def calculate_all(tiers: dict, fees: FeeSchedule = STRIPE) -> dict:
    """Run the same function over every tier: {"pro": TierEconomics, ...}."""
    return {key: calculate_tier_economics(t, fees) for key, t in tiers.items()}
