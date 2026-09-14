# dangote-ipo-watch

A daily data pipeline and event study around the Dangote Petroleum Refinery IPO
(offer window 14 September – 13 October 2026, ₦525/share, listing on the NGX).

**This repository models and describes. It does not recommend.** No file here
should ever contain a buy, sell or hold judgement, a price target, or a
suggested allocation. The output is a set of observed series and one explicitly
labelled estimate, so that a reader can reach their own conclusion and see
exactly which number to argue with.

---

## Why this exists

Almost every public argument about this offer reduces to a single disagreement:
whether the refining margins that produced H1 2026's ₦2.50 trillion profit are
the new normal or a temporary spike. That is an empirical question with a daily
observable proxy — the benchmark crack spread — and nobody appears to be
recording it through the offer window.

Thirty days of daily collection makes the disagreement testable after the fact.

## What it collects

| Series | Source | Cadence | Automatic |
|---|---|---|:--:|
| Brent, WTI spot | US EIA daily spot `.xls` | daily | yes |
| US Gulf Coast gasoline, ULSD, jet spot | US EIA | daily | yes |
| 3:2:1 crack spreads vs both Brent and WTI | derived | daily | yes |
| USD/NGN official window | open.er-api.com | daily | yes |
| Coverage volume (article counts) | Google News RSS, Nigeria edition | daily | yes |
| NGX All-Share / Oil & Gas index | — | daily | **no** |
| USD/NGN parallel market | — | daily | **no** |
| Reported subscription levels | — | ad hoc | **no** |

The last three have no stable free feed that survives a scraper, so they are
passed in by hand rather than guessed at:

```bash
python run.py --ngx-asi 157537.24 --parallel 1392 \
              --subscription-note "retail tranche reported 2x covered"
```

They land in `data/manual.csv`, kept separate from the automated series so the
provenance of every number stays obvious.

## Design rules

1. **Idempotent.** Market series are rebuilt from full upstream history on every
   run. Running twice in a day changes nothing; missing a week repairs itself on
   the next run. There is no fragile append-only state to corrupt.
2. **Fail soft.** Each collector is isolated. A dead source logs `FAIL` and the
   run continues.
3. **Observed and estimated are never mixed.** `data/` holds what was measured.
   The one estimated quantity in the project — the capture rate — lives in
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
averaged $31.06/bbl. The ratio — about **79%** — is the refinery's implied
capture of the benchmark, and it is the only estimated number in the project.

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
config.py     offer terms, balance sheet, benchmarks - every input in one place
collect.py    the collectors, one per source, each failing soft
metrics.py    crack spreads, EBITDA proxy, sensitivity, the naira hurdle
analyse.py    the capture-rate event study + chart
report.py     daily markdown report
run.py        CLI entry point
data/         observed series (csv)
reports/      one markdown report per day, plus latest.md
docs/         generated charts
```

## Sources

Offer terms and financials are taken from press reporting on the prospectus, not
from the prospectus document itself — see `config.py` for every figure and
`docs/` for the dossier this grew out of. Anyone relying on these numbers should
check them against the filed prospectus.

Spot prices: U.S. Energy Information Administration. FX: open.er-api.com.
Coverage counts: Google News (Nigeria edition).

## Licence

Do what you like with it. If you publish anything derived from it, keep the
first sentence of this README attached.
