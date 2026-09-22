# Bank LCR & Funding Concentration

> Reconstructing two Indian banks' Basel III Liquidity Coverage Ratio from
> their own Pillar 3 disclosures, checked line by line against what each
> bank actually printed — and asking whether the ratio alone tells you which
> bank is really more liquid.

## Core Question

HDFC Bank and IndusInd Bank both clear the RBI's 100% LCR minimum by a
comfortable margin, every quarter. Does the ratio itself say which bank's
funding is more resilient, or does that require looking underneath it at
what the funding is actually made of?

## Glossary

| Term | Meaning |
|---|---|
| LCR | Liquidity Coverage Ratio — Total HQLA ÷ Total Net Cash Outflows over a 30-day stress window, RBI's minimum is 100% |
| HQLA | High Quality Liquid Assets — the buffer a bank holds to meet that 30-day outflow |
| Run-off factor | The stress weight RBI assigns each funding category — e.g. 5% of stable retail deposits are assumed to run off in 30 days, 10% of less-stable deposits |
| Inflow cap | Cash inflows can only offset up to 75% of cash outflows when computing Net Cash Outflows — a bank can't claim its way to a high ratio purely through inflows |
| Less-stable deposit | RBI's classification for retail deposits assumed more likely to be withdrawn under stress (larger balances, non-relationship accounts, etc.) — carries a higher run-off factor than "stable" deposits |
| Wholesale funding | Funding from other financial institutions, corporates, and sovereigns, as opposed to retail/small-business deposits — assumed less sticky under stress |

## Key Findings

| Finding | HDFC Bank | IndusInd Bank |
|---|---|---|
| LCR, latest quarter (Jun 2026) | 115.00% | 126.66% |
| LCR range, 5 quarters | 113.5%–123.8% | 118.0%–141.3% |
| LCR trend, 5 quarters | −8.8 pts | −14.6 pts |
| Wholesale funding, % of funding base | 33.1% | 40.9% |
| Less-stable deposits, % of retail base | 77.6% | 95.3% |
| Reconciled cleanly (of 5 quarters) | 4/5 | 5/5 |

The bank with the lower LCR has the more retail-anchored, less wholesale-
dependent funding base. Full finding, with the reasoning and what it doesn't
prove: [`reports/liquidity_risk_memo.md`](reports/liquidity_risk_memo.md).

The "5 quarters" trend row is a first-to-last comparison, not a straight
line: both banks fell fairly steadily from Jun 2025 to Mar 2026, then turned
back up in Jun 2026 — an uptick partly masked by a jump in RBI's retail-
deposit run-off factors that quarter (see the memo's last section).

## Deliverables

- **Reconstruction engine:** `src/extract.py` (PDF table extraction),
  `src/hqla.py` (HQLA validation), `src/cashflows.py` (outflow/inflow/cap
  reconciliation), `src/funding_concentration.py` (funding-mix profiling),
  `src/synthesis.py` (comparative summary and finding)
- **Reconciled datasets:** `data/final/*.csv` — one row per bank-quarter at
  every stage, plus `comparative_verdict.json`
- **Charts:** `outputs/charts/` (`src/build_charts.py`, 300dpi) — LCR trend
  with the Jun-2026 factor callout, the headline funding-quality comparison,
  and the two-panel funding-mix trend
- **Memo:** [`reports/liquidity_risk_memo.md`](reports/liquidity_risk_memo.md)
  ([PDF](reports/liquidity_risk_memo.pdf))
- **Data dictionary:** [`reports/DATA_DICTIONARY.md`](reports/DATA_DICTIONARY.md)
- **Limitations:** [`reports/LIMITATIONS.md`](reports/LIMITATIONS.md)

## Methodology

1. Pull the RBI's standard 15-row (23 with sub-items) public LCR disclosure
   table out of each bank's PDF, per quarter — `extract.py` reads
   `pdfplumber`'s bordered-table grid and classifies each cell by content
   (row marker / label / numeric value) rather than by column position,
   since the two banks render the same template with different column
   layouts and padding.
2. Validate Total HQLA against its own restated copy in the same disclosure
   (`hqla.py`) — the public template gives one aggregate HQLA figure, not a
   Level 1/2A/2B breakdown, so validation is what's possible here, not a
   bottom-up rebuild.
3. Rebuild Total Outflows, Total Inflows, the 75% inflow cap, and Net Cash
   Outflows from the row-level weighted figures, and check each against the
   bank's own printed subtotal (`cashflows.py`).
4. Profile funding composition — retail vs. wholesale, and retail deposit
   stability — from the unweighted (raw balance) figures, trended across
   five quarters (`funding_concentration.py`).
5. Compare the two banks directly: ratio level and trend against funding
   quality, and state where they diverge (`synthesis.py`).

## Project Structure

```
bank-lcr-funding-concentration/
├── data/
│   ├── raw/            # 4 source PDFs, unmodified
│   ├── processed/      # lcr_disclosure_lines.csv — 230 extracted rows
│   └── final/           # validated + reconciled + comparative outputs
├── src/
│   ├── config.py
│   ├── extract.py
│   ├── hqla.py
│   ├── cashflows.py
│   ├── funding_concentration.py
│   ├── synthesis.py
│   ├── build_charts.py
│   └── build_pdf.py
├── outputs/
│   ├── tables/
│   └── charts/
├── reports/
│   ├── liquidity_risk_memo.md (+ .pdf)
│   ├── DATA_DICTIONARY.md
│   ├── LIMITATIONS.md
│   └── README.pdf
└── README.md
```

## Data / Sources

| Source | File | Quarters covered |
|---|---|---|
| HDFC Bank, Consolidated LCR disclosure | `hdfc_bank_q1fy26_jun2026.pdf` | Jun 2026, Mar 2026 |
| HDFC Bank, Consolidated LCR disclosure | `hdfc_bank_q4fy26_mar2026.pdf` | Mar 2026, Dec 2025, Sep 2025, Jun 2025 |
| IndusInd Bank, Basel III LCR disclosure | `indusind_bank_q1fy27_jun2026.pdf` | Jun 2026 |
| IndusInd Bank, Basel III LCR disclosure | `indusind_bank_q4fy26_mar2026.pdf` | Mar 2026, Dec 2025, Sep 2025, Jun 2025 |

All four downloaded directly from each bank's own regulatory-disclosures
page (hdfc.bank.in, indusind.bank.in). HDFC discloses in ₹ million,
IndusInd in ₹ crore — see `DATA_DICTIONARY.md` for how that's handled.

## How to Run

```bash
cd src
python3 extract.py                # -> data/processed/lcr_disclosure_lines.csv
python3 hqla.py                   # -> data/final/hqla_validation.csv
python3 cashflows.py              # -> data/final/lcr_reconciliation.csv
python3 funding_concentration.py  # -> data/final/funding_concentration.csv
python3 synthesis.py              # -> data/final/comparative_summary.csv, comparative_verdict.json
python3 build_charts.py           # -> outputs/charts/*.png
python3 build_pdf.py              # -> reports/*.pdf, README.pdf
```

Requires `pdfplumber`, `pandas`, `matplotlib`, `reportlab`.

## Results

See Key Findings above and the full memo. Every stage's output is a CSV in
`data/final/`, traceable back to the specific PDF row it came from.

## Limitations & Assumptions

Full detail in [`reports/LIMITATIONS.md`](reports/LIMITATIONS.md). Headline
items:
- HQLA is validated as disclosed, not rebuilt from Level 1/2A/2B components
  — the public template doesn't give that breakdown.
- One of the 10 bank-quarters (HDFC, Sep-2025, as restated in the Mar-2026
  filing) doesn't reconcile — confirmed as a real inconsistency in the
  bank's own printed figures, not an extraction error.
- The 75% inflow cap never binds in this dataset, for either bank, in any
  quarter — the cap logic here is untested against the case where it does.
- Two banks, five quarters — a comparison of these two funding profiles,
  not a system-wide claim about Indian bank liquidity.

## Author

**Shaswat Sharma** — [GitHub: theshaswat](https://github.com/theshaswat)

## License

MIT (see [`LICENSE`](LICENSE)).
