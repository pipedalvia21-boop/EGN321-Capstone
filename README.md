# GrowVest Unit Economics Tool

EGN 321 Capstone · Felipe D'Alvia

A command-line tool that computes per-tier gross margin, LTV and CAC payback
for GrowVest's Free, Pro and Premium plans. It replaces the spreadsheet model
audited in Assignment 3.2 and makes the defects found there structurally
impossible. See [CAPSTONE.md](CAPSTONE.md) for the original proposal.

> **Simulation edition.** As agreed with the professor, this is delivered as a
> simulation. Tier prices match GrowVest's published plans; hosting, support,
> churn and CAC figures are illustrative and are not real company data. Defect
> R-03 is a simulated example (see below).

## Setup

Requires Python 3.10 or newer. No third-party packages are needed to run the
tool; `pytest` is only needed for the tests.

```bash
git clone https://github.com/pipedalvia21-boop/EGN321-Capstone.git
cd EGN321-Capstone
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python -m growvest_economics report                  # all tiers, table
python -m growvest_economics report --tier premium   # one tier
python -m growvest_economics report --json           # machine-readable
python -m growvest_economics report --data my.json   # your own assumptions
python -m pytest -q                                  # 28 tests
```

Example output:

```
Tier         Price     Fee    Margin  Margin %        LTV   Payback  LTV:CAC
----------------------------------------------------------------------------
Free         $0.00   $0.00    -$0.70       n/a     -$4.67       n/a    -0.4x
Pro         $29.00   $1.14    $23.16     79.9%    $385.98    3.7 mo     4.5x
Premium     $79.00   $2.59    $65.91     83.4%  $1,647.73    2.4 mo    10.3x
```

To change an assumption, edit `growvest_economics/data/tiers_simulated.json`.
To change the payment fee for every tier at once, edit `STRIPE` in
`growvest_economics/fees.py`.

## Project structure

```
growvest_economics/
  fees.py         FeeSchedule + STRIPE: the only place the payment fee is defined
  tiers.py        TierAssumptions record, validation, JSON loader
  engine.py       calculate_tier_economics(): the only place the math lives
  report.py       table / JSON formatting
  __main__.py     command line (python -m growvest_economics report)
  data/tiers_simulated.json
tests/
  test_validation.py   bad input is refused with the field named
  test_engine.py       hand-computed reference values + R-01, R-02, R-03 regressions
  test_cli.py          command-line behaviour
```

## Structure justification

**The core structure is a dict of small, frozen dataclass records**,
`{"free": TierAssumptions, "pro": TierAssumptions, "premium": TierAssumptions}`,
consumed one at a time by a single function, `calculate_tier_economics(tier)`.

Why this and not the alternatives:

- **Versus the spreadsheet.** Each spreadsheet tier had its own copy of the
  formulas, so a formula could point at another tier's cell and still produce
  a plausible number. That is defect **R-01** (Premium's fee used Pro's price).
  Here there is one formula, and it receives one record. It has no way to read
  another tier's price.
- **Versus a pandas DataFrame.** Tiers as rows and costs as columns would bring
  the same failure back as a string: `df["pro_price"]` where
  `df["premium_price"]` was meant. Dataclass fields are attributes, so a typo is
  an `AttributeError`, an editor can autocomplete them, and the JSON loader
  rejects unknown field names. With three tiers and six fields, vectorized
  performance buys nothing.
- **One fee object.** The payment fee lives only in `STRIPE` (`fees.py`) and is
  passed into the engine. Defect **R-02** (the Stripe fee typed as a literal in
  two formulas) cannot recur because there is nowhere else to type it.
- **Validation in the record itself.** `TierAssumptions.__post_init__` runs on
  every record, so an invalid one can never exist. Units are in the field
  names (`_usd`, `_monthly`), and churn must be a fraction. Defect **R-03**
  (simulated: churn typed as `6` instead of `0.06`, making LTV 100x too small)
  is refused with a message showing the right format.
- **Frozen records.** `frozen=True` means no code can change an assumption
  halfway through a calculation.

**One change from the proposal:** the proposal said to reject a price of 0 or
less. That would reject the Free tier, so the rule is now *price cannot be
negative*. A $0 tier pays no processing fee and reports margin % and payback
as "n/a" instead of dividing by zero.

## Development history

Built as a simulation. Commits are labeled by module (Module 4 to Module 8) to
show the order the features were built, matching the four features in the
proposal. AI use is documented in [AI_LOG.md](AI_LOG.md).
