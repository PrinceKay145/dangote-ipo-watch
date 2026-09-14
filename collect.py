"""Collectors.

Design rule: every collector rebuilds its series from the full upstream history
on each run rather than appending one row. A missed day therefore repairs itself
on the next run, and running twice in a day changes nothing. The only append-only
store is the news log, which is deduplicated by URL.

Every collector fails soft. One dead source must not take the run down.
"""

from __future__ import annotations

import io
import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import config

UA = "Mozilla/5.0 (compatible; dangote-ipo-watch/1.0; research)"
DATA = Path(__file__).parent / "data"


def _get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _log(ok: bool, what: str, detail: str = "") -> None:
    print(f"  [{'ok ' if ok else 'FAIL'}] {what}{(' - ' + detail) if detail else ''}")


# --------------------------------------------------------------- commodities
def collect_commodities() -> pd.DataFrame | None:
    """Daily spot prices from the US EIA. Authoritative, free, no API key."""
    frames = {}
    for name, fname in config.EIA_SERIES.items():
        try:
            raw = _get(config.EIA_BASE + fname)
            x = pd.read_excel(io.BytesIO(raw), sheet_name="Data 1", skiprows=2)
            x.columns = ["date", name]
            x = x.dropna()
            x["date"] = pd.to_datetime(x["date"]).dt.date
            frames[name] = x.set_index("date")[name]
            _log(True, name, f"{len(x)} rows to {x['date'].iloc[-1]}")
        except Exception as e:  # noqa: BLE001
            _log(False, name, f"{type(e).__name__}: {e}")

    if not frames:
        return None

    df = pd.DataFrame(frames).sort_index()
    df = df[df.index >= pd.to_datetime(config.BACKFILL_FROM).date()]
    return df.reset_index().rename(columns={"index": "date"})


# ------------------------------------------------------------------------ fx
def collect_fx() -> dict | None:
    """USD/NGN. This API tracks the official window, not the parallel market."""
    try:
        j = json.loads(_get(config.FX_URL, timeout=45))
        rate = float(j["rates"]["NGN"])
        stamp = j.get("time_last_update_utc", "")
        _log(True, "usdngn_official", f"{rate:,.2f}")
        return {"date": datetime.now(timezone.utc).date().isoformat(),
                "usdngn_official": rate, "source_stamp": stamp}
    except Exception as e:  # noqa: BLE001
        _log(False, "usdngn_official", f"{type(e).__name__}: {e}")
        return None


# ---------------------------------------------------------------------- news
def collect_news() -> pd.DataFrame | None:
    """Nigerian-edition Google News RSS. Counts coverage volume, not sentiment."""
    rows = []
    for q in config.NEWS_QUERIES:
        url = config.NEWS_RSS.format(q=urllib.parse.quote(q))
        try:
            root = ET.fromstring(_get(url, timeout=45))
            for item in root.iter("item"):
                link = (item.findtext("link") or "").strip()
                if not link:
                    continue
                pub = (item.findtext("pubDate") or "").strip()
                try:
                    d = datetime.strptime(pub[:16], "%a, %d %b %Y").date().isoformat()
                except ValueError:
                    d = datetime.now(timezone.utc).date().isoformat()
                title = (item.findtext("title") or "").strip()
                src_el = item.find("source")
                rows.append({
                    "published": d,
                    "source": (src_el.text or "").strip() if src_el is not None else "",
                    "title": title,
                    "url": link,
                    "query": q,
                })
            _log(True, f"news {q}", f"{len(rows)} cumulative")
        except Exception as e:  # noqa: BLE001
            _log(False, f"news {q}", f"{type(e).__name__}: {e}")

    if not rows:
        return None
    return pd.DataFrame(rows).drop_duplicates(subset=["url"])


# -------------------------------------------------------- assisted / manual
def record_manual(date: str, **fields) -> None:
    """NGX index levels and the parallel FX rate have no stable free feed.

    They are supplied by hand (or by an assistant using a web fetch) via
    `run.py --ngx-asi ... --parallel ...`. Recording them separately keeps the
    automated series clean and makes the provenance of every number obvious.
    """
    path = DATA / "manual.csv"
    row = {"date": date, **{k: v for k, v in fields.items() if v is not None}}
    if len(row) == 1:
        return
    if path.exists():
        df = pd.read_csv(path)
        df = df[df["date"] != date]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.sort_values("date").to_csv(path, index=False)
    _log(True, "manual entries", ", ".join(f"{k}={v}" for k, v in row.items() if k != "date"))
