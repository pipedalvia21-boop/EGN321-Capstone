# Live Code Challenge — where every change goes

Study this **before** the presentation. AI is not allowed during the defense,
so practise each change once yourself, run the test, then `git checkout .` to undo.

## The 8 likely requests

| Request | File | What to edit | How to prove it |
|---|---|---|---|
| Change an alert threshold | `growvest_economics/config.py` | `MIN_MARGIN_PCT = ... "0.70"` → `"0.85"` | `python -m growvest_economics status` now lists margin alerts for pro and premium |
| Change stale-data timeout | `config.py` | `STALE_AFTER_HOURS` `"24"` → `"1"` | `status` shows STALE if the last run is older than 1 h |
| Add a validation rule | `growvest_economics/tiers.py`, inside `__post_init__` | e.g. `if self.price_usd > 1000: raise ValueError(f"{self.name}: price_usd above 1000, got {self.price_usd!r}")` | Add a test in `tests/test_validation.py` with `pytest.raises(ValueError, match="price_usd")` |
| Change a UI label | `growvest_economics/report.py`, `format_table` header | e.g. `'Payback'` → `'Payback mo'` | `python -m growvest_economics report` |
| Add a log field | `growvest_economics/__main__.py`, `cmd_report` | `log("INFO", "report_calculated", ..., tier_count=len(results))` | `python -m growvest_economics report` then `... log --last 1` |
| Modify a test | `tests/test_engine.py` | change an expected value; run; see it fail; restore | `python -m pytest -q tests/test_engine.py` |
| Change a config value | `growvest_economics/fees.py` | `STRIPE = FeeSchedule(pct=0.029, fixed_usd=0.30)` → `0.035` | `report`: every paid tier's fee changes (this is R-02 fixed) |
| Add a unit / range | `tiers.py` | e.g. accept churn as `churn_pct` (0–100) and convert to fraction | new test + `report --data` with a file using the new field |

Without editing code you can also show a threshold change with an env var:

```bash
GROWVEST_MIN_MARGIN_PCT=0.85 python -m growvest_economics status        # Mac/Linux
$env:GROWVEST_MIN_MARGIN_PCT="0.85"; python -m growvest_economics status # PowerShell
```

## How data flows (say this in one breath)

JSON file → `load_tiers()` → `TierAssumptions.__post_init__` validates →
`calculate_tier_economics(tier, STRIPE)` → table / JSON → `check_alerts()` →
`save_run()` to SQLite, or to `pending_runs.jsonl` if the DB is down →
`recover()` flushes the queue. Every step logs one JSON line.

## Formulas you must know by heart

```
fee      = price × 0.029 + 0.30        (0 if price is 0)
margin   = price − hosting − support − fee
margin % = margin ÷ price
LTV      = margin ÷ churn
payback  = CAC ÷ margin                (n/a if margin ≤ 0)
LTV:CAC  = LTV ÷ CAC
```

Pro by hand: 29×0.029+0.30 = 1.141 → 29−3.20−1.50−1.141 = 23.159 →
23.159÷0.06 = 385.98 → 85÷23.159 = 3.67 months.

## Questions the instructor will probably ask

- **Why dataclasses and not pandas?** Column-name strings recreate R-01;
  attributes fail loudly on typos; three tiers need no vectorization.
- **Why is the record frozen?** No code can change an assumption mid-calculation.
- **Why is Free allowed price 0 when the proposal said > 0?** Otherwise the
  Free tier itself is rejected; division by price is guarded instead.
- **What happens if SQLite is down?** The report still prints, the run goes to
  `pending_runs.jsonl`, an ERROR is logged, status shows DEGRADED/FAILED,
  `recover` writes it back in one transaction (all or nothing).
- **How do you know recovery worked?** `pending_runs 0`, status OK, and the run
  appears in `history` with source `recovered`; `recover_succeeded` in the log.
- **Why read the workbook in the test instead of typing the numbers?** If the
  workbook is recalculated or changed, the test follows it; typed numbers could
  drift from the artifact we claim to match.
- **Biggest limitation?** Valid but unrealistic inputs still give a confident
  answer; the tool checks format and range, not truth.
