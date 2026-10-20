"""Command line: python -m growvest_economics report [options]

Examples:
    python -m growvest_economics report
    python -m growvest_economics report --tier pro
    python -m growvest_economics report --json
    python -m growvest_economics report --data my_tiers.json
"""

import argparse
import sys

from .engine import calculate_all
from .report import format_json, format_table
from .tiers import DEFAULT_DATA, load_tiers


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="growvest_economics")
    sub = parser.add_subparsers(dest="command", required=True)

    rep = sub.add_parser("report", help="print per-tier unit economics")
    rep.add_argument("--data", default=DEFAULT_DATA, help="tier assumptions JSON")
    rep.add_argument("--tier", help="only show one tier (free, pro, premium)")
    rep.add_argument("--json", action="store_true", help="output JSON instead of a table")

    args = parser.parse_args(argv)

    try:
        tiers = load_tiers(args.data)
    except (ValueError, TypeError) as e:
        # Validation errors are shown cleanly, never as a wrong number.
        print(f"Invalid assumptions: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"Data file not found: {args.data}", file=sys.stderr)
        return 2

    if args.tier:
        if args.tier not in tiers:
            print(f"Unknown tier {args.tier!r}. Options: {', '.join(tiers)}", file=sys.stderr)
            return 2
        tiers = {args.tier: tiers[args.tier]}

    results = calculate_all(tiers)
    print(format_json(results) if args.json else format_table(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
