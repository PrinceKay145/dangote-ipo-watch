#!/usr/bin/env python3
"""Daily collector for the Dangote Refinery IPO event study.

    python run.py                                   # collect everything automatic
    python run.py --ngx-asi 157537.24 --parallel 1392   # add the assisted fields
    python run.py --no-news                         # skip the RSS pull

Safe to run twice in one day, and safe to miss days: the market series are
rebuilt from full upstream history on every run.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import collect
import config
import metrics
import report

ROOT = Path(__file__).parent
DATA = ROOT / "data"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ngx-asi", type=float, help="NGX All-Share Index close")
    ap.add_argument("--ngx-oilgas", type=float, help="NGX Oil & Gas index close")
    ap.add_argument("--parallel", type=float, help="USD/NGN parallel market rate")
    ap.add_argument("--subscription-note", type=str,
                    help="free-text note on reported subscription levels")
    ap.add_argument("--no-news", action="store_true")
    ap.add_argument("--no-report", action="store_true")
    args = ap.parse_args()

    DATA.mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()
    print(f"dangote-ipo-watch - run for {today}\n")

    # -- commodities (full rebuild) -----------------------------------------
    print("commodities (EIA daily spot):")
    com = collect.collect_commodities()
    if com is not None:
        com = metrics.add_cracks(com)
        com.to_csv(DATA / "commodities.csv", index=False)
        print(f"  -> data/commodities.csv ({len(com)} rows)\n")
    else:
        print("  -> no commodity data this run; keeping existing file\n")
        com = (pd.read_csv(DATA / "commodities.csv")
               if (DATA / "commodities.csv").exists() else None)

    # -- fx (append one row per day, replacing today's) ----------------------
    print("fx:")
    fx_row = collect.collect_fx()
    fx_path = DATA / "fx.csv"
    if fx_row:
        prev = pd.read_csv(fx_path) if fx_path.exists() else pd.DataFrame()
        if not prev.empty:
            prev = prev[prev["date"] != fx_row["date"]]
        pd.concat([prev, pd.DataFrame([fx_row])], ignore_index=True) \
          .sort_values("date").to_csv(fx_path, index=False)
        print(f"  -> data/fx.csv\n")
    else:
        print("  -> fx unavailable this run\n")

    # -- news (append + dedupe by url) --------------------------------------
    if not args.no_news:
        print("news:")
        news = collect.collect_news()
        news_path = DATA / "news.csv"
        if news is not None:
            news["first_seen"] = today
            if news_path.exists():
                prev = pd.read_csv(news_path)
                merged = pd.concat([prev, news], ignore_index=True)
                merged = merged.drop_duplicates(subset=["url"], keep="first")
            else:
                merged = news
            merged.sort_values("published").to_csv(news_path, index=False)

            daily = (merged.groupby("published").size()
                     .reset_index(name="mention_count")
                     .rename(columns={"published": "date"}))
            daily.to_csv(DATA / "news_daily.csv", index=False)
            print(f"  -> data/news.csv ({len(merged)} unique articles)\n")
        else:
            print("  -> news unavailable this run\n")

    # -- assisted fields -----------------------------------------------------
    if any([args.ngx_asi, args.ngx_oilgas, args.parallel, args.subscription_note]):
        print("manual / assisted:")
        collect.record_manual(today,
                              ngx_asi=args.ngx_asi,
                              ngx_oilgas=args.ngx_oilgas,
                              usdngn_parallel=args.parallel,
                              subscription_note=args.subscription_note)
        print()

    # -- report --------------------------------------------------------------
    if not args.no_report:
        usdngn = fx_row["usdngn_official"] if fx_row else None
        if usdngn is None and fx_path.exists():
            usdngn = float(pd.read_csv(fx_path)["usdngn_official"].iloc[-1])
        path = report.write_report(today, com, usdngn or 1327.10, args.parallel)
        print(f"report -> {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
