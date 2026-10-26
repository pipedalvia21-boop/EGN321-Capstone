# GrowVest Unit Economics Tool — Final Operating Guide

EGN 321 Capstone (Assignment 8.2) · Felipe D'Alvia

**What did I inherit, what did I build, and why should someone trust the result?**

- **Inherited:** a spreadsheet (`original_workbook/GrowVest_Unit_Economics_v1.xlsx`)
  that computes per-tier margin, LTV and CAC payback for GrowVest's Free, Pro
  and Premium plans. It contains three silent defects (R-01, R-02, R-03).
- **Built:** a Python tool with one validated data structure, one shared
  calculation, refusal of bad input, SQLite history, structured logs, health
  status, business alerts and recovery from a database outage.
- **Why trust it:** 40 automated tests, including 5 that read the original
  workbook and prove the tool matches it where it was right and corrects it
  where it was wrong.

> **Simulation edition.** As agreed with the professor, this is delivered as a
> simulation. Tier prices match GrowVest's published plans ($0 / $29 / $79);
> hosting, support, churn and CAC figures are illustrative, not company data.

---

## 1. Quick start

Requires Python 3.10+.

```bash
git clone https://github.com/pipedalvia21-boop/EGN321-Capstone.git
cd EGN321-Capstone
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt    # pytest + openpyxl (tests only; the tool itself needs nothing)
python -m pytest -q                # expect: 40 passed
python -m growvest_economics report --save
```

On Windows use `python`; on Mac/Linux use `python3` if `python` is not found.

## 2. Commands

| Command | What it does |
|---|---|
| `python -m growvest_economics report` | Per-tier table (Free, Pro, Premium) |
| `... report --save` | Same, and stores the run in SQLite history |
| `... report --tier pro --json` | One tier, machine-readable |
| `... report --data FILE.json` | Use your own assumptions file |
| `... history --tier premium` | Saved runs for one tier (newest first) |
| `... status` | Health state + business alerts |
| `... recover` | Writes queued runs into the database after an outage |
| `... log --last 10` | Last structured log lines |
| `bash scripts/demo.sh` | Runs all five presentation demos in order |

Normal output:

```
Tier         Price     Fee    Margin  Margin %        LTV   Payback  LTV:CAC
----------------------------------------------------------------------------
Free         $0.00   $0.00    -$0.70       n/a     -$4.67       n/a    -0.4x
Pro         $29.00   $1.14    $23.16     79.9%    $385.98    3.7 mo     4.5x
Premium     $79.00   $2.59    $65.91     83.4%  $1,647.73    2.4 mo    10.3x
Saved to history as run #1.
```

Exit codes: `0` success, `1` status DEGRADED/FAILED or recovery failed,
`2` input refused.

## 3. Architecture

```
tiers_simulated.json ─► load_tiers() ─► TierAssumptions (validation) ─► REFUSED + log
                                              │ valid
                                              ▼
                              calculate_tier_economics()  (one formula, STRIPE fee)
                                              │
               ┌──────────────────────────────┼─────────────────────────────┐
               ▼                              ▼                             ▼
        report table/JSON            check_alerts() ─► ALERT        save_run() ─► SQLite
                                                                         │ DB down
                                                                         ▼
                                                          pending_runs.jsonl ─► recover
                       every step writes JSON lines to runtime/growvest.log
```

| File | Responsibility |
|---|---|
| `growvest_economics/tiers.py` | `TierAssumptions` record, all input validation, JSON loader |
| `growvest_economics/fees.py` | `STRIPE` fee schedule — the only place the fee exists |
| `growvest_economics/engine.py` | `calculate_tier_economics()` — the only place the math lives |
| `growvest_economics/config.py` | Every threshold, timeout and path (env-var overridable) |
| `growvest_economics/history.py` | SQLite storage, recovery queue, `recover()` |
| `growvest_economics/monitor.py` | Health states and business alerts |
| `growvest_economics/logjson.py` | Structured JSON-line logging |
| `growvest_economics/report.py` | Table and JSON formatting |
| `growvest_economics/__main__.py` | Command line |
| `original_workbook/` | The inherited spreadsheet and how it was rebuilt |
| `samples/` | Valid and deliberately invalid input files for demos |
| `evidence/` | Captured demo run, log, DB dump, status after recovery |
| `scripts/demo.sh` | The five live demos; `scripts/simulate_db_outage.py` the controlled failure |

### Why this structure (from the proposal)

A dict of small, frozen dataclass records consumed one at a time by a single
function. Each record only holds its own tier, so a formula cannot read another
tier's price (R-01). The fee is one object passed in, so it cannot be typed
twice (R-02). Validation runs in `__post_init__`, so an invalid record cannot
exist (R-03). A pandas DataFrame was rejected because `df["pro_price"]` vs
`df["premium_price"]` brings back the same wrong-but-plausible failure as a
string. Change from the proposal: price `0` is allowed (the Free tier); only a
negative price is refused.

## 4. Proving the calculation (`tests/test_workbook_verification.py`)

Expected values are read from the original workbook file, not retyped.

| Test | Case | Workbook | Application |
|---|---|---|---|
| 1 Known-correct | Pro tier | fee 1.141, margin 23.159, LTV 385.98 | identical |
| 2 Problem case (R-01) | Premium fee | $1.141 (used Pro's $29) | $2.591 (uses $79); workbook overstated margin by $1.45 |
| 3 Invalid input (R-03) | churn typed `6` | silently shows LTV $3.86 | **REFUSED**: "write 6% as 0.06" |
| 4 Student test | Free tier | payback hand-typed "n/a" | rule-based: margin ≤ 0 never pays back |

Other suites: `test_validation.py` (every refusal names the field),
`test_engine.py` (hand-computed reference values, R-01/R-02/R-03 regressions),
`test_cli.py`, `test_history_and_recovery.py` (SQLite, alerts, failure→recovery).

## 5. Refusal behaviour

The tool refuses instead of guessing when: a number is negative, churn is not a
fraction in (0, 1], a value is not a number, a field name is misspelled, the
name is empty, or the file is missing or not valid JSON. Try:

```bash
python -m growvest_economics report --data samples/invalid_churn_percent.json
# REFUSED - invalid assumptions: Pro: churn_monthly must be a fraction in (0, 1], got 6 (write 6% as 0.06)
```

**Why refuse?** A spreadsheet that receives `6` instead of `0.06` prints a
plausible LTV of $3.86. Nobody notices, and pricing or ad-spend decisions are
made on a number that is 100x wrong. A refusal costs the user ten seconds; a
silent wrong number can cost real money.

## 6. Monitoring, failure and recovery

Health states from `status` (worst wins): **OK**, **STALE** (no saved run in
24 h), **DEGRADED** (runs waiting in the recovery queue), **FAILED** (data
invalid or database unreachable).

Business alerts (paid tiers only): margin below 70%, LTV:CAC below 3.0x,
payback above 12 months. `samples/whatif_pro_19.json` triggers one.

Controlled failure (two terminals):

```bash
python scripts/simulate_db_outage.py --seconds 30     # terminal 2: locks the DB
python -m growvest_economics report --save            # result printed, run queued, ERROR logged
python -m growvest_economics status                   # FAILED / DEGRADED, pending_runs 1
# after the lock is released:
python -m growvest_economics recover                  # Recovered 1 run(s) into history: [n]
python -m growvest_economics status                   # OK, pending_runs 0
python -m growvest_economics history --tier pro       # run n, source = recovered
```

Captured run: `evidence/demo_run_2026-10-25.txt`, log `evidence/sample_growvest.log`.

## 7. Configuration

All settings are in `growvest_economics/config.py` and can be overridden by
environment variables without editing code:

| Setting | Default | Env var |
|---|---|---|
| Minimum margin alert | 0.70 | `GROWVEST_MIN_MARGIN_PCT` |
| Minimum LTV:CAC alert | 3.0 | `GROWVEST_MIN_LTV_TO_CAC` |
| Maximum payback alert | 12 months | `GROWVEST_MAX_PAYBACK_MONTHS` |
| Stale after | 24 hours | `GROWVEST_STALE_AFTER_HOURS` |
| DB wait before giving up | 1.0 s | `GROWVEST_DB_TIMEOUT_S` |
| Runtime folder | `runtime/` | `GROWVEST_HOME` |

To change an assumption, edit `growvest_economics/data/tiers_simulated.json`.
To change the Stripe fee for every tier, edit `STRIPE` in `fees.py`.

## 8. Assumptions

- All money is USD; costs are **per user per month**; CAC is per acquired user.
- Churn is a monthly **fraction** (0.06 = 6%), constant over the customer lifetime.
- LTV = gross margin ÷ churn (no discounting, no expansion revenue).
- One payment per user per month; Stripe 2.9% + $0.30; no fee on a $0 charge.
- Input is a JSON file with the six fields in `TierAssumptions`; no other fields allowed.
- SQLite is local and single-user; Python 3.10+ on Windows, macOS or Linux.

## 9. Limitations

1. **Simulated inputs.** The tool proves the math is right, not that the
   cost, churn and CAC estimates are realistic. Garbage-but-valid input
   (e.g. churn 0.01 when it is really 0.10) still produces a confident answer.
2. **Simple LTV model.** No discount rate, cohort decay, annual plans,
   refunds or upgrades between tiers.
3. **Single-user local storage.** SQLite and the recovery queue are on one
   machine; there is no backup or multi-user locking beyond SQLite's own.
4. **No live data feed.** Assumptions are typed into a file; the tool does not
   pull real churn or Stripe data from GrowVest's systems.

## 10. Handoff and AI use

Handoff results and changes: [HANDOFF.md](HANDOFF.md).
AI use: [AI_LOG.md](AI_LOG.md). Original proposal: [CAPSTONE.md](CAPSTONE.md).
