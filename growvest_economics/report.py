"""Turn TierEconomics results into a readable table or JSON."""

import json
from dataclasses import asdict


def _money(x):
    return f"-${-x:,.2f}" if x < 0 else f"${x:,.2f}"


def _maybe(x, fmt):
    return "n/a" if x is None else fmt(x)


def format_table(results: dict) -> str:
    header = (f"{'Tier':<9}{'Price':>9}{'Fee':>8}{'Margin':>10}{'Margin %':>10}"
              f"{'LTV':>11}{'Payback':>10}{'LTV:CAC':>9}")
    lines = [header, "-" * len(header)]
    for r in results.values():
        lines.append(
            f"{r.name:<9}"
            f"{_money(r.price_usd):>9}"
            f"{_money(r.payment_fee_usd):>8}"
            f"{_money(r.gross_margin_usd):>10}"
            f"{_maybe(r.margin_pct, lambda v: f'{v:.1%}'):>10}"
            f"{_money(r.ltv_usd):>11}"
            f"{_maybe(r.cac_payback_months, lambda v: f'{v:.1f} mo'):>10}"
            f"{_maybe(r.ltv_to_cac, lambda v: f'{v:.1f}x'):>9}"
        )
    lines.append("")
    lines.append("Simulated assumptions. Payback n/a = tier never recovers its CAC.")
    return "\n".join(lines)


def format_json(results: dict) -> str:
    return json.dumps({k: asdict(v) for k, v in results.items()}, indent=2)
