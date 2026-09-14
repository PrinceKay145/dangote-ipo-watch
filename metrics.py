"""Derived metrics.

The crack-spread model is a back-of-envelope proxy, not a refinery model. It is
calibrated against one published figure: Renaissance Capital put H1 2026 EBITDA
at $2.60bn on a gross refining margin of $24.5/bbl. Feeding those inputs through
`annual_ebitda_usd` reproduces roughly $2.5bn, so the shape is right. Treat the
output as an order of magnitude, never as a valuation.
"""

from __future__ import annotations

import pandas as pd

import config

G = config.GALLONS_PER_BARREL


def add_cracks(df: pd.DataFrame) -> pd.DataFrame:
    """3:2:1 crack spreads and single-product cracks, all in $/bbl."""
    d = df.copy()
    gaso = d.get("gasoline_usgc_usd_gal")
    ulsd = d.get("ulsd_usgc_usd_gal")

    if gaso is not None and ulsd is not None:
        product_bbl = (2 * gaso + ulsd) * G / 3
        if "wti_usd_bbl" in d:
            d["crack_321_wti"] = product_bbl - d["wti_usd_bbl"]
        if "brent_usd_bbl" in d:
            # Dangote runs Nigerian grades, which price off Brent - this is the
            # crack that actually bears on the refinery's economics.
            d["crack_321_brent"] = product_bbl - d["brent_usd_bbl"]
            d["gasoline_crack_brent"] = gaso * G - d["brent_usd_bbl"]
            d["diesel_crack_brent"] = ulsd * G - d["brent_usd_bbl"]

    if "brent_usd_bbl" in d and "wti_usd_bbl" in d:
        d["brent_wti_spread"] = d["brent_usd_bbl"] - d["wti_usd_bbl"]

    return d


def annual_ebitda_usd(margin_usd_bbl: float,
                      utilisation: float = config.UTILISATION,
                      nameplate_bpd: int = config.NAMEPLATE_BPD,
                      opex_usd_bbl: float = config.OPEX_USD_BBL) -> float:
    """Annualised EBITDA implied by a given gross refining margin."""
    throughput = nameplate_bpd * utilisation * 365
    return throughput * (margin_usd_bbl - opex_usd_bbl)


def market_cap_usd(usdngn: float) -> float:
    return config.SHARES_POST_OFFER * config.OFFER_PRICE_NGN / usdngn


def enterprise_value_usd(usdngn: float) -> float:
    """Cash is not disclosed in the reporting, so this overstates EV."""
    return market_cap_usd(usdngn) + config.SECURED_DEBT_USD


def ev_ebitda(margin_usd_bbl: float, usdngn: float, **kw) -> float:
    e = annual_ebitda_usd(margin_usd_bbl, **kw)
    return float("inf") if e <= 0 else enterprise_value_usd(usdngn) / e


def sensitivity_table(usdngn: float,
                      margins=(8, 12, 16, 20, 24.5, 30, 40, 50)) -> pd.DataFrame:
    """What multiple is ₦525 paying, across the plausible margin range?

    $8/bbl is the compression case flagged in Bamboo's risk note. $24.5 is the
    H1 2026 realised margin. The top of the range is roughly where spot cracks
    have been sitting during the offer window.
    """
    rows = []
    for m in margins:
        e = annual_ebitda_usd(m)
        rows.append({
            "gross_margin_usd_bbl": m,
            "implied_annual_ebitda_usd_bn": e / 1e9,
            "ev_ebitda_x": enterprise_value_usd(usdngn) / e if e > 0 else float("nan"),
        })
    return pd.DataFrame(rows)


def yield_gap() -> dict:
    """The hurdle: what the shares must do to match risk-free naira."""
    earnings_yield = config.EPS_ANNUALISED_NGN / config.OFFER_PRICE_NGN * 100
    return {
        "earnings_yield_pct": earnings_yield,
        "tbill_364d_pct": config.TBILL_364D,
        "best_mmf_pct": config.BEST_MMF_YIELD,
        "inflation_pct": config.INFLATION_HEADLINE,
        "gap_vs_tbill_pp": config.TBILL_364D - earnings_yield,
        "real_mmf_pct": config.BEST_MMF_YIELD - config.INFLATION_HEADLINE,
    }
