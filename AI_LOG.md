# AI Log: EGN 321 Capstone

Tool: Claude (Anthropic), claude.ai. AI use was permitted throughout.

## Session: 2026-10-20

**Prompt 1:** Pasted the capstone delivery requirements (working application,
public repo, README with setup and structure justification, commit history
spanning Modules 4 to 8, live presentation, AI_LOG.md).

- Claude reviewed the repo and found only the proposal commit (2026-09-22).
- Claude said it would not create backdated commits to fake a Module 4 to 8
  history, and asked for any existing work and the Assignment 3.2 data.

**Prompt 2:** "estoy en clase y el profesor me dijo que puedo hacer todo como
una simulacion para completarlo" (the professor approved completing it as a
simulation).

- Claude built the tool from the design in CAPSTONE.md: `fees.py`, `tiers.py`,
  `engine.py`, `report.py`, `__main__.py`, the simulated data file, 28 tests,
  and the README.
- Data: tier prices from GrowVest's plans; costs, churn and CAC are simulated.
  R-03 is a simulated defect because only R-01 and R-02 are described in the
  proposal.
- Commits were made the same day and labeled by module to show build order.
  No commit dates were altered.
- Claude changed one rule from the proposal (price <= 0 rejected) because it
  would have rejected the Free tier.

## What I verified

- Ran `python -m pytest -q`: 28 passed.
- Ran `python -m growvest_economics report` and checked Pro and Premium against
  the hand calculations at the top of `tests/test_engine.py`.
