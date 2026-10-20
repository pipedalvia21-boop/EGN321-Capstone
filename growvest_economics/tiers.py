"""Tier data structure: a dict of small, named, validated records.

{"free": TierAssumptions(...), "pro": TierAssumptions(...), ...}

Each record holds only its own tier's numbers, and every field name carries
its unit (_usd, _monthly). A calculation that receives one record cannot
reach into another tier's data, which is what made defect R-01 possible in
the spreadsheet.
"""

import json
from dataclasses import dataclass, fields
from pathlib import Path

DEFAULT_DATA = Path(__file__).parent / "data" / "tiers_simulated.json"


@dataclass(frozen=True)
class TierAssumptions:
    name: str
    price_usd: float          # monthly subscription price
    hosting_cost_usd: float   # infra cost per user per month
    support_cost_usd: float   # support cost per user per month
    churn_monthly: float      # fraction of users lost per month, e.g. 0.06 = 6%
    cac_usd: float            # cost to acquire one user

    def __post_init__(self):
        # Input validation: refuse bad assumptions instead of computing
        # a wrong answer. Every message names the field and the value.
        if not self.name or not self.name.strip():
            raise ValueError("name cannot be empty")

        for f in fields(self):
            if f.name == "name":
                continue
            value = getattr(self, f.name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{self.name}: {f.name} must be a number, got {value!r}")

        if self.price_usd < 0:
            raise ValueError(f"{self.name}: price_usd cannot be negative, got {self.price_usd!r}")
        for cost in ("hosting_cost_usd", "support_cost_usd", "cac_usd"):
            if getattr(self, cost) < 0:
                raise ValueError(f"{self.name}: {cost} cannot be negative, got {getattr(self, cost)!r}")

        # Defect R-03 guard: churn must be a fraction, never a whole percent.
        # 6 (meaning 6%) would make LTV 100x too small without any error.
        if not 0 < self.churn_monthly <= 1:
            raise ValueError(
                f"{self.name}: churn_monthly must be a fraction in (0, 1], "
                f"got {self.churn_monthly!r} (write 6% as 0.06)"
            )

    @property
    def is_free(self) -> bool:
        return self.price_usd == 0


def load_tiers(path=DEFAULT_DATA) -> dict:
    """Load tier records from JSON into {"key": TierAssumptions}."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    allowed = {f.name for f in fields(TierAssumptions)}
    tiers = {}
    for key, values in raw["tiers"].items():
        unknown = set(values) - allowed
        if unknown:
            # Catches typos like "hostng_cost_usd" in the data file.
            raise ValueError(f"{key}: unknown field(s) {sorted(unknown)}")
        tiers[key] = TierAssumptions(**values)
    return tiers
