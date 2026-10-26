# Handoff (Assignment 8.1) — results and changes

## Partner results

> **Fill in from your real Assignment 8.1 session before submitting.**
> Write what actually happened; do not invent it.

- Partner: _name_
- Where my partner struggled: _e.g. which step of setup or which command_
- What they asked me: _…_
- How long setup took: _…_

## What I changed for the final delivery

These changes target the friction points a new operator usually hits. Keep the
ones that match what your partner reported and say so in the presentation.

| Friction | Change |
|---|---|
| `python` vs `python3`, Windows activation | Quick start lists both, plus the expected result (`40 passed`) |
| Unclear error when the data file was broken | Malformed JSON now says "REFUSED - data file is not valid JSON" instead of a traceback-style message |
| No way to see what the tool did earlier | `history`, `status` and `log` commands |
| "Did it save?" | `report --save` prints `Saved to history as run #n` or a clear WARNING |
| Thresholds hidden in code | All settings in `config.py` with a table in the README and env-var overrides |
| Demo order hard to remember | `scripts/demo.sh` runs the five demos in sequence |
| No sample bad inputs | `samples/` has invalid churn, negative cost, malformed JSON and a valid what-if |

## What I learned about designing for someone else
- An error message is part of the interface: it must name the field, the bad
  value and the fix.
- The README has to state the expected result of each step, otherwise the
  operator cannot tell success from silent failure.
- Anything a person might need to change (thresholds, paths) should not
  require reading the calculation code.
