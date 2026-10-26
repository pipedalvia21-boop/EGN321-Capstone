"""Command line: python -m growvest_economics <command> [options]

Commands:
    report    print per-tier unit economics (add --save to store it in history)
    history   show saved runs for one tier from SQLite
    status    health state (OK / STALE / DEGRADED / FAILED) and business alerts
    recover   write queued runs into the database after an outage
    log       show the last structured log lines

Examples:
    python -m growvest_economics report
    python -m growvest_economics report --save
    python -m growvest_economics report --tier pro --json
    python -m growvest_economics report --data my_tiers.json
    python -m growvest_economics history --tier premium
    python -m growvest_economics status
    python -m growvest_economics recover
"""

import argparse
import json
import sys

from . import history, monitor
from .engine import calculate_all
from .logjson import log, read_log
from .report import format_json, format_table
from .tiers import DEFAULT_DATA, load_tiers


def cmd_report(args) -> int:
    try:
        tiers = load_tiers(args.data)
    except json.JSONDecodeError as e:
        log("WARN", "input_refused", data_file=str(args.data), reason=f"malformed JSON: {e}")
        print(f"REFUSED - data file is not valid JSON: {e}", file=sys.stderr)
        return 2
    except (ValueError, TypeError) as e:
        # Refusal: show the reason, never a wrong number.
        log("WARN", "input_refused", data_file=str(args.data), reason=str(e))
        print(f"REFUSED - invalid assumptions: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        log("WARN", "input_refused", data_file=str(args.data), reason="file not found")
        print(f"REFUSED - data file not found: {args.data}", file=sys.stderr)
        return 2

    if args.tier:
        if args.tier not in tiers:
            print(f"Unknown tier {args.tier!r}. Options: {', '.join(tiers)}", file=sys.stderr)
            return 2
        tiers = {args.tier: tiers[args.tier]}

    results = calculate_all(tiers)
    log("INFO", "report_calculated", data_file=str(args.data), tiers=list(results))
    print(format_json(results) if args.json else format_table(results))

    for a in monitor.check_alerts(results):
        log("WARN", "business_alert", alert=a)
        print(f"ALERT: {a}", file=sys.stderr)

    if args.save:
        outcome = history.save_run(results, args.data)
        if outcome["saved"]:
            print(f"Saved to history as run #{outcome['run_id']}.", file=sys.stderr)
        else:
            print(f"WARNING: history database unavailable ({outcome['error']}). "
                  f"Run queued; use `recover` when the database is back.", file=sys.stderr)
    return 0


def cmd_history(args) -> int:
    rows = history.list_runs(args.tier, args.limit)
    if not rows:
        print(f"No saved runs for tier {args.tier!r}. Use `report --save` first.")
        return 0
    print(f"History for {args.tier} (newest first)")
    print(f"{'Run':>4}  {'Saved (UTC)':<21}{'Source':<10}{'Margin':>9}{'Margin %':>9}"
          f"{'LTV':>11}{'Payback':>9}{'LTV:CAC':>8}")
    for rid, ts, src, gm, mp, ltv, pb, lc in rows:
        print(f"{rid:>4}  {ts:<21}{src:<10}{gm:>9.2f}"
              f"{'n/a' if mp is None else f'{mp:.1%}':>9}{ltv:>11.2f}"
              f"{'n/a' if pb is None else f'{pb:.1f}':>9}"
              f"{'n/a' if lc is None else f'{lc:.1f}x':>8}")
    return 0


def cmd_status(args) -> int:
    h = monitor.health(args.data)
    if args.json:
        print(json.dumps(h, indent=2))
    else:
        print(f"STATE: {h['state']}")
        for k, v in h["checks"].items():
            print(f"  {k:<13} {v}")
        print("ALERTS:" if h["alerts"] else "ALERTS: none")
        for a in h["alerts"]:
            print(f"  - {a}")
    log("INFO", "status_checked", state=h["state"])
    return 0 if h["state"] in ("OK", "STALE") else 1


def cmd_recover(args) -> int:
    try:
        out = history.recover()
    except Exception as e:  # noqa: BLE001 - reported to the operator
        print(f"Recovery failed, runs still queued: {e}", file=sys.stderr)
        return 1
    if out["recovered"] == 0:
        print("Nothing to recover.")
    else:
        print(f"Recovered {out['recovered']} run(s) into history: {out['run_ids']}")
    return 0


def cmd_log(args) -> int:
    for rec in read_log(args.last):
        print(json.dumps(rec))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="growvest_economics")
    sub = parser.add_subparsers(dest="command", required=True)

    rep = sub.add_parser("report", help="print per-tier unit economics")
    rep.add_argument("--data", default=DEFAULT_DATA, help="tier assumptions JSON")
    rep.add_argument("--tier", help="only show one tier (free, pro, premium)")
    rep.add_argument("--json", action="store_true", help="output JSON instead of a table")
    rep.add_argument("--save", action="store_true", help="store this run in SQLite history")
    rep.set_defaults(func=cmd_report)

    his = sub.add_parser("history", help="show saved runs for one tier")
    his.add_argument("--tier", default="pro")
    his.add_argument("--limit", type=int, default=20)
    his.set_defaults(func=cmd_history)

    st = sub.add_parser("status", help="health state and alerts")
    st.add_argument("--data", default=None)
    st.add_argument("--json", action="store_true")
    st.set_defaults(func=cmd_status)

    rec = sub.add_parser("recover", help="write queued runs into the database")
    rec.set_defaults(func=cmd_recover)

    lg = sub.add_parser("log", help="show the last structured log lines")
    lg.add_argument("--last", type=int, default=20)
    lg.set_defaults(func=cmd_log)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
