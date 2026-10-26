# AI Log: EGN 321 Capstone

Tool: Claude (Anthropic), claude.ai. AI use was permitted during development.
AI is **not** used during the live code challenge or code defense.

## Session: 2026-10-20 (Module 4–8 build)

**Prompt 1:** Pasted the capstone delivery requirements.
- Claude found only the proposal commit and said it would not create backdated
  commits; asked for existing work and the Assignment 3.2 data.

**Prompt 2:** The professor approved completing it as a simulation.
- Claude built `fees.py`, `tiers.py`, `engine.py`, `report.py`, `__main__.py`,
  the simulated data, 28 tests and the README from the design in CAPSTONE.md.
- Prices from GrowVest's plans; costs, churn and CAC simulated; R-03 simulated.
- Rejected/changed: the proposal rule "price <= 0 is invalid" (would reject Free).

## Session: 2026-10-25 (Assignment 8.2 final delivery)

**Prompt:** Pasted the 8.2 requirements and asked Claude to complete everything.

Accepted from AI:
- `original_workbook/` rebuilt from the Assignment 3.2 design with R-01, R-02,
  R-03 left in, plus `scripts/build_original_workbook.py`.
- `tests/test_workbook_verification.py` (Tests 1–4 read the workbook directly).
- `config.py`, `logjson.py`, `history.py`, `monitor.py`; commands `history`,
  `status`, `recover`, `log`; `scripts/simulate_db_outage.py`; `scripts/demo.sh`.
- `tests/test_history_and_recovery.py`, `tests/conftest.py`, `samples/`,
  `evidence/`, README Operating Guide, HANDOFF.md, DEFENSE_GUIDE.md.

Changed after review:
- First version reported malformed JSON as "invalid assumptions" because
  `JSONDecodeError` is a `ValueError`; reordered the handlers so it says
  "not valid JSON".
- Business alerts skip the Free tier; otherwise status would always alert.

Not accepted / left for me:
- HANDOFF.md partner results: AI cannot know what my partner did, so those
  lines are left for me to fill in from the real 8.1 session.

## How I verified
- `python -m pytest -q`: 40 passed.
- Workbook recalculated in LibreOffice; Pro values in the workbook equal the
  tool's (Test 1); Premium fee differs exactly by the R-01 amount (Test 2).
- Ran `bash scripts/demo.sh`; full output in `evidence/demo_run_2026-10-25.txt`
  (refusals exit 2, outage detected, `recover` restored run #2, status back to OK).
