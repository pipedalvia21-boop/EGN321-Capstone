EGN 321 Capstone Proposal — GrowVest Unit Economics Tool
The Problem

GrowVest (my SaaS paper-trading platform, in closed beta) prices three tiers — Free, Pro ($29/mo), Premium ($79/mo) — and I decide pricing and paid-acquisition spend based on a spreadsheet model of per-tier gross margin, LTV, and CAC payback (built and audited in Assignment 3.2). That audit already found two verified formula defects: Premium's payment-processing fee formula references Pro's price cell instead of its own, and the Stripe fee is typed as a literal in two separate formulas instead of one source of truth. Both are silent — Excel never flags a formula that references the "wrong but plausible" cell — and as the sole founder/engineer, I am currently the only person who would ever notice. That is exactly the kind of mistake that should be structurally impossible, not just "checked more carefully next time."

The Structure My Solution Depends On

The core structure is a dictionary of small, named tier records ({"free": TierAssumptions(...), "pro": TierAssumptions(...), ...}), each holding validated, unit-labeled fields (price_usd, hosting_cost_usd, stripe_pct, churn_monthly, etc.). Exactly one shared calculate_tier_economics(tier) function consumes one record at a time and produces its margin/LTV/CAC-payback result — there is no per-tier copy of the formula to fall out of sync, and no formula can reach into a different tier's data because each record only exposes its own fields.

Why This Structure, Not the Obvious Alternative

The obvious alternative is a pandas DataFrame with tiers as rows and costs as columns — natural for financial modeling, and a tool I already know. I'm rejecting it for this capstone specifically because it reproduces the same failure category it's meant to fix: a DataFrame formula/computation that slices the wrong column (df["pro_price"] where df["premium_price"] was intended) is the exact same silent, plausible-looking mistake as the Excel bug I already found — it just moves the risk from a cell reference to a column-name string. A dict of named, per-tier dataclasses instead makes each tier's data a self-contained object: there is no shared row/column index for a typo or copy-paste to misalign, every field carries its unit in its name, and a linter/type-checker can catch a misspelled field name in a way neither Excel nor a DataFrame's string-keyed columns support. Given the dataset is only three tiers with about a dozen fields each, I also don't need DataFrame's vectorized-operation performance — the readability and mistake-resistance of explicit records wins at this scale, the same lesson Module 3's LOOKUP_TABLES pattern already taught me.

Four Features by Module 8
Validated tier data structure + single calculation engine — the TierAssumptions records and the one shared calculate_tier_economics() function described above, replacing all per-tier spreadsheet formulas.
Input validation layer — rejects nonsensical assumptions (negative costs, a price ≤ 0, churn outside 0–100%) with clear, field-naming error messages, so the tool refuses bad input instead of silently computing a wrong result.
Regression test suite — tests pinned specifically to the three defects found in Assignment 3.2 (R-01, R-02, R-03), plus known-correct reference values recomputed by hand, so this exact class of mistake cannot be silently reintroduced later.
Command-line report (python -m growvest_economics report) that prints a per-tier margin/LTV/CAC-payback summary — the actual day-to-day replacement for opening the spreadsheet.
