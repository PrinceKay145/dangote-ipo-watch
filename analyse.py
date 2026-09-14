#!/usr/bin/env python3
"""The event study itself.

Answers one question with data rather than opinion: how much of the benchmark
refining margin does Dangote actually capture, and what does that imply at
today's spreads?

Method: Renaissance Capital put Dangote's realised H1 2026 gross refining margin
at $24.5/bbl. Comparing that with the mean benchmark 3:2:1 crack over the same
period gives a capture rate. Applying that rate to current cracks gives a
current-margin estimate that is grounded in one published number and one
observable series, instead of in a narrative.

    python analyse.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import config
import metrics

ROOT = Path(__file__).parent


def load() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "commodities.csv", parse_dates=["date"])


def capture_rate(d: pd.DataFrame) -> dict:
    h1 = d[(d.date >= "2026-01-01") & (d.date <= "2026-06-30")]
    recent = d[d.date >= "2026-07-01"]
    bench_h1 = h1.crack_321_brent.mean()
    bench_now = recent.crack_321_brent.mean()
    rate = config.H1_2026_GROSS_MARGIN_USD_BBL / bench_h1
    implied = bench_now * rate
    return {
        "benchmark_h1": bench_h1,
        "realised_h1": config.H1_2026_GROSS_MARGIN_USD_BBL,
        "capture_rate": rate,
        "benchmark_recent": bench_now,
        "implied_recent_margin": implied,
        "implied_annual_ebitda_usd": metrics.annual_ebitda_usd(implied),
    }


def chart(d: pd.DataFrame, out: Path) -> Path | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping chart")
        return None

    TEAL, AMBER, INK, MUTED, GRID = "#008571", "#b0651b", "#13201d", "#6c7a76", "#e0e7e4"
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plot(d.date, d.crack_321_brent, color=TEAL, lw=2, zorder=3)

    h1 = d[(d.date >= "2026-01-01") & (d.date <= "2026-06-30")]
    ax.axhline(h1.crack_321_brent.mean(), color=MUTED, lw=1.2, ls="--", zorder=2)
    ax.annotate(f"H1 mean ${h1.crack_321_brent.mean():.0f}",
                xy=(d.date.iloc[3], h1.crack_321_brent.mean()),
                xytext=(0, 6), textcoords="offset points",
                color=MUTED, fontsize=9)

    open_d = pd.to_datetime(config.OFFER_OPEN)
    ax.axvspan(open_d, pd.to_datetime(config.OFFER_CLOSE), color=AMBER, alpha=.10, zorder=1)
    ax.annotate("offer window", xy=(open_d, ax.get_ylim()[1]), xytext=(4, -14),
                textcoords="offset points", color=AMBER, fontsize=9)

    last = d.iloc[-1]
    ax.scatter([last.date], [last.crack_321_brent], s=42, color=TEAL, zorder=4,
               edgecolor="white", linewidth=1.6)
    ax.annotate(f"${last.crack_321_brent:.0f}", xy=(last.date, last.crack_321_brent),
                xytext=(8, -3), textcoords="offset points",
                color=INK, fontsize=10, fontweight="bold")

    ax.set_title("Benchmark 3:2:1 crack spread vs Brent, 2026", color=INK,
                 fontsize=12, loc="left", pad=12)
    ax.set_ylabel("$ / barrel", color=MUTED, fontsize=9)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    fig.tight_layout()
    fig.savefig(out, facecolor="white")
    return out


def main() -> int:
    d = load()
    c = capture_rate(d)
    usdngn = 1327.10
    fx = ROOT / "data" / "fx.csv"
    if fx.exists():
        usdngn = float(pd.read_csv(fx)["usdngn_official"].iloc[-1])

    print("Capture-rate analysis")
    print("=" * 58)
    print(f"  Benchmark 3:2:1 crack, H1 2026 mean : ${c['benchmark_h1']:6.2f}/bbl")
    print(f"  Dangote realised margin, H1 2026    : ${c['realised_h1']:6.2f}/bbl  (RenCap)")
    print(f"  Implied capture rate                : {c['capture_rate']:6.1%}")
    print()
    print(f"  Benchmark crack since 1 July        : ${c['benchmark_recent']:6.2f}/bbl")
    print(f"  Implied realised margin at that     : ${c['implied_recent_margin']:6.2f}/bbl")
    print(f"  Implied annualised EBITDA           : ${c['implied_annual_ebitda_usd']/1e9:6.2f}bn")
    print(f"  EV/EBITDA at ₦525                   : {metrics.ev_ebitda(c['implied_recent_margin'], usdngn):6.1f}x")
    print()
    print("  Monthly mean benchmark crack, $/bbl:")
    m = d.assign(m=d.date.dt.to_period("M")).groupby("m").crack_321_brent.mean()
    for k, v in m.items():
        print(f"    {k}  {v:5.1f}  {'#' * int(v / 2)}")
    print()
    print("  Reading it: the capture rate is the only estimated quantity here, and it")
    print("  rests on a single sell-side figure. If RenCap's $24.5/bbl is wrong, every")
    print("  number below it moves. The monthly series is observed, not estimated.")

    p = chart(d, ROOT / "docs" / "crack_spread.png")
    if p:
        print(f"\n  chart -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
