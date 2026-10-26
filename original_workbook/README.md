# The inherited artifact

`GrowVest_Unit_Economics_v1.xlsx` is the spreadsheet audited in Assignment 3.2,
rebuilt by `scripts/build_original_workbook.py` with its defects left in.

## What it was designed to do
Tell the founder, per pricing tier, whether a paying user is profitable and how
fast the cost of acquiring them is recovered.

## Inputs (sheet *Assumptions*, yellow cells)
Price, hosting cost, support cost (USD per user per month), monthly churn,
CAC (USD per user), plus a Stripe % and fixed fee.

## Outputs (sheet *Unit Economics*)
Payment fee, gross margin, margin %, LTV, CAC payback (months), LTV:CAC.

## Assumptions it made (unstated in the file)
Churn typed as a fraction; one charge per month; Stripe fee the same for every
tier; Free tier has no payback (typed "n/a" by hand).

## Problems found

| ID | Cell | Problem | Effect |
|---|---|---|---|
| R-01 | `Unit Economics!D2` | `=Assumptions!C2*0.029+0.3` uses **Pro's** price for Premium | Premium fee $1.14 instead of $2.59; margin overstated $1.45/user/month; LTV overstated $36 |
| R-02 | `C2`, `D2` | Stripe 2.9% + $0.30 typed inside formulas; the `Stripe %` input cell is ignored by Pro and Premium | Changing the fee input only changes Free |
| R-03 (simulated) | `Scenario!B4` | Churn typed `6` (meant 6%) is accepted | LTV shows $3.86 instead of $385.98, no warning |
| — | `B4`, `B6` | "n/a" typed by hand to avoid #DIV/0! | Hides the rule; breaks if price changes |

The verification tests open this file directly and compare it with the tool.
