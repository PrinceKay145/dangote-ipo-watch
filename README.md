# dangote-ipo-watch

A daily data pipeline and event study around the Dangote Petroleum Refinery IPO
(offer window 14 September to 13 October 2026, ₦525/share, listing on the NGX).

**This repository models and describes. It does not recommend.** No file here
should ever contain a buy, sell or hold judgement, a price target, or a
suggested allocation. The output is a set of observed series and one explicitly
labelled estimate, so that a reader can reach their own conclusion and see
exactly which number to argue with.

**Start at [`reports/latest.md`](reports/latest.md).** That is the current state
of every series, rewritten on each run.

---

## Why this exists

Most public argument about this offer reduces to one disagreement: whether the
refining margins that produced H1 2026's ₦2.50 trillion profit are the new
normal or a temporary spike. That is an empirical question with a daily
observable proxy, the benchmark crack spread, and the offer window is a fixed
thirty days. Recording the proxy across those thirty days makes the
disagreement testable afterwards instead of only arguable beforehand.

## What it collects

| Series | Source | Cadence | Automatic |
|---|---|---|:--:|
| Brent, WTI spot | US EIA daily spot `.xls` | daily | yes |
| US Gulf Coast gasoline, ULSD, jet spot | US EIA | daily | yes |
| 3:2:1 crack spreads vs both Brent and WTI | derived | daily | yes |
| USD/NGN official window | open.er-api.com | daily | yes |
| Coverage volume (article counts) | Google News RSS, Nigeria edition | daily | yes |
| NGX All-Share / Oil & Gas index | none found | daily | **no** |
| USD/NGN parallel market | none found | daily | **no** |
| Reported subscription levels | none found | ad hoc | **no** |

The last three have no free feed that survives a scraper, so they are passed in
by hand rather than guessed at:

```bash
python run.py --ngx-asi 157537.24 --ngx-oilgas 3421.55 --parallel 1392 \
              --subscription-note "retail tranche reported 2x covered"
```

They land in `data/manual.csv`, kept separate from the automated series so the
provenance of every number stays obvious.

Yahoo Finance, stooq and FRED were all tried first and are unusable here: Yahoo
and stooq sit behind bot challenges, and none of the three survived the network
restrictions this runs under. EIA publishes the same spot series as plain
spreadsheets with no key and no challenge, which is why it is the spine of the
whole thing.

## How it runs

A GitHub Actions workflow (`.github/workflows/daily.yml`) runs the collector at
06:10 UTC daily and commits whatever changed. EIA posts the previous session's
prices in the US morning, so that window reliably picks up the last close.

The workflow also accepts a manual run (Actions tab, "daily collect", "Run
workflow") with optional `ngx_asi`, `parallel` and `note` inputs, which is how
the three hand-fed fields get recorded.

If you fork this: the workflow commits back to the repository, so it needs
**Settings, Actions, General, Workflow permissions, Read and write**. New repos
default to read-only and the commit step fails with a 403.

## Design rules

1. **Idempotent where it matters.** The market series (`data/commodities.csv`)
   is rebuilt from full upstream history on every run, so running twice in a day
   changes nothing and missing a week repairs itself on the next run. The two
   accumulating files are handled explicitly rather than blindly appended:
   `data/news.csv` deduplicates on article URL, and `data/fx.csv` replaces the
   current day's row instead of adding a second one.
2. **Fail soft.** Each collector is isolated. A dead source logs `FAIL` and the
   run continues with the rest.
3. **Observed and estimated are never mixed.** `data/` holds what was measured.
   The one estimated quantity in the project, the capture rate, lives in
   `analyse.py` and is labelled everywhere it appears.

## Usage

```bash
pip install -r requirements.txt

python run.py        # collect, write data/, write reports/YYYY-MM-DD.md
python analyse.py    # capture-rate analysis + docs/crack_spread.png
```

## The one piece of modelling

Renaissance Capital put Dangote's *realised* H1 2026 gross refining margin at
$24.5/bbl. Over that same half-year the benchmark 3:2:1 crack against Brent
averaged $31.06/bbl. The ratio, about **79%**, is the refinery's implied capture
of the benchmark, and it is the only estimated number in the project.

Applying that capture rate to the current benchmark gives a current-margin
estimate grounded in one published figure and one observed series, rather than
in a narrative. `metrics.annual_ebitda_usd` then converts a margin into an
annualised EBITDA:

```
throughput = 650,000 bpd × 90% utilisation × 365 days
EBITDA     = throughput × (gross margin − $3/bbl opex)
```

Fed the H1 inputs, this reproduces roughly $2.5bn against RenCap's published
$2.6bn H1 EBITDA, which is the only reason to trust its shape at all.

**If RenCap's $24.5/bbl is wrong, every derived number moves.** That dependency
is the first thing to attack when reviewing this work.

## What the model is not

- Not a refinery model. It has no product slate, no yield curve, no turnaround
  schedule, no crude differential, no domestic price regulation.
- Not a valuation. Enterprise value here excludes cash, which is not disclosed
  in the reporting, so EV is overstated by an unknown amount.
- Not forward-looking. A margin observed today says nothing about next quarter.
- Not sentiment analysis. Article counts measure attention, not opinion. No
  sentiment score is computed, because a headline count is honest and a
  sentiment score derived from headlines is not.

## Layout

```
config.py     offer terms, balance sheet, benchmarks; every input in one place
collect.py    the collectors, one per source, each failing soft
metrics.py    crack spreads, EBITDA proxy, sensitivity, the naira hurdle
analyse.py    the capture-rate event study and chart
report.py     daily markdown report
run.py        CLI entry point
data/         observed series (csv)
reports/      one markdown report per day, plus latest.md
docs/         generated charts
```

## Sources

Offer terms and financials are taken from press reporting on the prospectus, not
from the prospectus document itself. Every one of those figures sits in
`config.py` with a comment saying where it came from. Anyone relying on them
should check them against the filed prospectus.

Spot prices: U.S. Energy Information Administration. FX: open.er-api.com.
Coverage counts: Google News (Nigeria edition).

## Licence

MIT, see [LICENSE](LICENSE). If you publish anything derived from this, please
keep the second paragraph of this README attached to it.
