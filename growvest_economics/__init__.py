"""GrowVest unit economics tool (EGN 321 capstone).

Replaces the per-tier spreadsheet model with one data structure
(a dict of TierAssumptions records) and one shared calculation.

Modules:
    fees.py    FeeSchedule + STRIPE, the single source of truth for fees
    tiers.py   TierAssumptions records, validation, JSON loader
    engine.py  calculate_tier_economics(), the one shared formula
    report.py  text/JSON report used by the command line
"""
