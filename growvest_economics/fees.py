"""Payment-processor fees: ONE source of truth.

Fixes defect R-02 from Assignment 3.2: the spreadsheet typed the Stripe
fee as a literal inside two separate formulas, so changing it in one place
left the other stale. Here the fee lives in exactly one object, STRIPE,
and every calculation receives it as an argument.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeeSchedule:
    pct: float        # fraction of the charge, e.g. 0.029 = 2.9%
    fixed_usd: float  # flat fee per successful charge

    def __post_init__(self):
        if not 0 <= self.pct < 1:
            raise ValueError(f"fee pct must be a fraction in [0, 1), got {self.pct!r}")
        if self.fixed_usd < 0:
            raise ValueError(f"fee fixed_usd cannot be negative, got {self.fixed_usd!r}")

    def fee_for(self, charge_usd: float) -> float:
        """Fee on one monthly charge. No charge (free tier) means no fee."""
        if charge_usd == 0:
            return 0.0
        return charge_usd * self.pct + self.fixed_usd


# Stripe standard US card pricing. Change it HERE and every tier updates.
STRIPE = FeeSchedule(pct=0.029, fixed_usd=0.30)
