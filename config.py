"""Fixed parameters for the Dangote Refinery IPO event study.

Every figure here comes from press reporting on the prospectus (14 Sep 2026).
Verify against the prospectus itself before treating any of it as fact.
"""

# ---------------------------------------------------------------- offer terms
OFFER_PRICE_NGN = 525.0
SHARES_OFFERED = 4_100_000_000
SHARES_PRE_OFFER = 120_130_000_000
SHARES_POST_OFFER = SHARES_PRE_OFFER + SHARES_OFFERED  # 124.23bn
MIN_LOT_SHARES = 10
MIN_LOT_NGN = OFFER_PRICE_NGN * MIN_LOT_SHARES  # 5,250

OFFER_OPEN = "2026-09-14"
OFFER_CLOSE = "2026-10-13"
ALLOTMENT_RESULTS = "2026-10-27"
SEC_CLEARANCE = "2026-11-11"
LOCKUP_EXPIRY = "2027-07-01"  # approximate: 365 days from the July 2026 placement

# ------------------------------------------------------------ balance sheet
SECURED_DEBT_USD = 5.67e9        # at 30 June 2026
H1_2026_PAT_NGN = 2.50e12
H1_2026_REVENUE_NGN = 19.13e12
H1_2026_EBITDA_USD = 2.60e9      # Renaissance Capital Africa estimate
H1_2026_GROSS_MARGIN_USD_BBL = 24.5  # RenCap
FY2025_EBITDA_USD = 0.545e9
EPS_ANNUALISED_NGN = 38.74

# ---------------------------------------------------------------- operations
NAMEPLATE_BPD = 650_000          # sources quote 650k or 700k; 650k is the conservative read
UTILISATION = 0.90               # implied by H1 throughput
OPEX_USD_BBL = 3.0               # RenCap: "below $3/bbl"

# -------------------------------------------------- naira benchmarks (14 Sep 2026)
TBILL_364D = 16.62
TBILL_182D = 16.50
TBILL_91D = 16.30
MPR = 26.50
INFLATION_HEADLINE = 15.43       # July 2026 print
BEST_MMF_YIELD = 20.54

# ------------------------------------------------------------------- sources
EIA_SERIES = {
    "brent_usd_bbl": "RBRTEd.xls",
    "wti_usd_bbl": "RWTCd.xls",
    "gasoline_usgc_usd_gal": "EER_EPMRU_PF4_RGC_DPGd.xls",
    "ulsd_usgc_usd_gal": "EER_EPD2DXL0_PF4_RGC_DPGd.xls",
    "jet_usgc_usd_gal": "EER_EPJK_PF4_RGC_DPGd.xls",
}
EIA_BASE = "https://www.eia.gov/dnav/pet/hist_xls/"
FX_URL = "https://open.er-api.com/v6/latest/USD"
NEWS_QUERIES = ["\"Dangote refinery\"", "\"Dangote refinery\" IPO", "Dangote refinery shares"]
NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-NG&gl=NG&ceid=NG:en"

BACKFILL_FROM = "2026-01-01"
GALLONS_PER_BARREL = 42.0
