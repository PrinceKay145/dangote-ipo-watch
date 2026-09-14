"""Daily markdown report.

Describes the state of the inputs. Does not recommend anything, and must not be
edited to. The point of the exercise is to watch one assumption - that H1 2026
refining margins persist - either hold or break, in public, with dates on it.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

import config
import metrics

ROOT = Path(__file__).parent


def _fmt(v, nd=2, dash="n/a"):
    try:
        if pd.isna(v):
            return dash
        return f"{float(v):,.{nd}f}"
    except (TypeError, ValueError):
        return dash


def write_report(today: str, com: pd.DataFrame | None,
                 usdngn: float, parallel: float | None = None) -> Path:
    days_left = (pd.to_datetime(config.OFFER_CLOSE).date() - date.fromisoformat(today)).days
    L = []
    L.append(f"# Dangote Refinery IPO watch - {today}\n")
    L.append(f"**Offer window:** {config.OFFER_OPEN} to {config.OFFER_CLOSE} "
             f"({days_left} days left)\n")
    L.append("_Research log. Describes inputs; recommends nothing._\n")

    last = None
    if com is not None and len(com):
        last = com.iloc[-1]
        L.append("## Spot prices and refining margins\n")
        L.append(f"Latest EIA observation: **{last['date']}**\n")
        L.append("| Series | Level |")
        L.append("|---|---:|")
        L.append(f"| Brent | ${_fmt(last.get('brent_usd_bbl'))}/bbl |")
        L.append(f"| WTI | ${_fmt(last.get('wti_usd_bbl'))}/bbl |")
        L.append(f"| Brent-WTI spread | ${_fmt(last.get('brent_wti_spread'))}/bbl |")
        L.append(f"| Gasoline, US Gulf Coast | ${_fmt(last.get('gasoline_usgc_usd_gal'), 4)}/gal |")
        L.append(f"| ULSD, US Gulf Coast | ${_fmt(last.get('ulsd_usgc_usd_gal'), 4)}/gal |")
        L.append(f"| **3:2:1 crack vs Brent** | **${_fmt(last.get('crack_321_brent'))}/bbl** |")
        L.append(f"| 3:2:1 crack vs WTI | ${_fmt(last.get('crack_321_wti'))}/bbl |")
        L.append(f"| Gasoline crack vs Brent | ${_fmt(last.get('gasoline_crack_brent'))}/bbl |")
        L.append(f"| Diesel crack vs Brent | ${_fmt(last.get('diesel_crack_brent'))}/bbl |")
        L.append("")

        # 30-day context
        if len(com) > 30:
            m30 = com["crack_321_brent"].tail(30).mean()
            L.append(f"30-day mean 3:2:1 crack vs Brent: **${_fmt(m30)}/bbl**. "
                     f"H1 2026 realised gross margin was ${config.H1_2026_GROSS_MARGIN_USD_BBL}/bbl "
                     "(Renaissance Capital).\n")

    L.append("## FX\n")
    L.append(f"- USD/NGN official: **{_fmt(usdngn)}**")
    if parallel:
        prem = (parallel / usdngn - 1) * 100
        L.append(f"- USD/NGN parallel: **{_fmt(parallel)}** ({_fmt(prem)}% premium)")
    else:
        L.append("- USD/NGN parallel: not captured this run (pass `--parallel`)")
    L.append("")

    L.append("## What ₦525 implies at these margins\n")
    mc = metrics.market_cap_usd(usdngn) / 1e9
    ev = metrics.enterprise_value_usd(usdngn) / 1e9
    L.append(f"At USD/NGN {_fmt(usdngn)}, {config.SHARES_POST_OFFER/1e9:.2f}bn shares "
             f"× ₦{config.OFFER_PRICE_NGN:.0f} = **${_fmt(mc)}bn** market cap; "
             f"adding ${config.SECURED_DEBT_USD/1e9:.2f}bn secured debt gives "
             f"**${_fmt(ev)}bn** enterprise value (cash not disclosed, so EV is overstated).\n")

    if last is not None and not pd.isna(last.get("crack_321_brent", float("nan"))):
        spot = float(last["crack_321_brent"])
        spot_mult = metrics.ev_ebitda(spot, usdngn)
        h1_mult = metrics.ev_ebitda(config.H1_2026_GROSS_MARGIN_USD_BBL, usdngn)
        L.append(f"- At **today's** crack (${_fmt(spot)}/bbl): EV/EBITDA ≈ "
                 f"**{_fmt(spot_mult, 1)}×**")
        L.append(f"- At the **H1 2026 realised** margin (${config.H1_2026_GROSS_MARGIN_USD_BBL}/bbl): "
                 f"EV/EBITDA ≈ **{_fmt(h1_mult, 1)}×**")
        L.append("")

    L.append("### Margin sensitivity\n")
    t = metrics.sensitivity_table(usdngn)
    L.append("| Gross margin $/bbl | Implied annual EBITDA $bn | EV/EBITDA |")
    L.append("|---:|---:|---:|")
    for _, r in t.iterrows():
        L.append(f"| {r['gross_margin_usd_bbl']:.1f} | "
                 f"{r['implied_annual_ebitda_usd_bn']:.2f} | "
                 f"{r['ev_ebitda_x']:.1f}× |")
    L.append("")
    L.append(f"_Model: {config.NAMEPLATE_BPD:,} bpd nameplate × {config.UTILISATION:.0%} "
             f"utilisation × 365 days × (margin − ${config.OPEX_USD_BBL:.0f}/bbl opex). "
             "Calibrated so the H1 inputs reproduce RenCap's $2.6bn H1 EBITDA. "
             "An order of magnitude, not a valuation._\n")

    yg = metrics.yield_gap()
    L.append("## The naira hurdle\n")
    L.append(f"- Earnings yield at ₦525: **{_fmt(yg['earnings_yield_pct'])}%** "
             "(annualised H1 EPS, peak-cycle)")
    L.append(f"- 364-day treasury bill: **{_fmt(yg['tbill_364d_pct'])}%**")
    L.append(f"- Best money market fund: **{_fmt(yg['best_mmf_pct'])}%** "
             f"({_fmt(yg['real_mmf_pct'])}% real)")
    L.append(f"- Gap to close through price appreciation: "
             f"**{_fmt(yg['gap_vs_tbill_pp'])} percentage points**\n")

    nd = ROOT / "data" / "news_daily.csv"
    if nd.exists():
        d = pd.read_csv(nd).tail(10)
        L.append("## Coverage volume\n")
        L.append("| Date | Articles |")
        L.append("|---|---:|")
        for _, r in d.iterrows():
            L.append(f"| {r['date']} | {int(r['mention_count'])} |")
        L.append("\n_Google News, Nigeria edition. Volume only - no sentiment scoring, "
                 "because a headline count is evidence of attention, not of quality._\n")

    out = ROOT / "reports" / f"{today}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    (ROOT / "reports" / "latest.md").write_text("\n".join(L), encoding="utf-8")
    return out
