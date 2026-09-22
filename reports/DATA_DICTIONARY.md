# Data Dictionary

## `data/processed/lcr_disclosure_lines.csv`

One row per (bank, quarter, disclosure line) — 230 rows: 2 banks × 5 quarters
× 23 rows of the RBI's standard public LCR disclosure template.

| Column | Type | Meaning |
|---|---|---|
| bank | str | `HDFC Bank` or `IndusInd Bank` |
| quarter | date (ISO) | Quarter-end date the figures are as of |
| row_id | str | The disclosure template's own row numbering (`1`–`15`, with `2i`/`2ii`, `3i`–`3iii`, `5i`–`5iii` for lettered sub-items) |
| label | str | Short row description |
| unweighted | float | The raw balance, before any run-off/inflow factor is applied. `NaN` where the bank's own template doesn't disclose an unweighted figure for that row (see LIMITATIONS.md — this is consistently true for row 4, Secured wholesale funding, in both banks) |
| weighted | float | The value after the RBI's prescribed run-off or inflow factor — this is the figure that actually feeds the LCR calculation |
| source_file | str | Which PDF in `data/raw/` this row came from |
| unit | str | `million` (HDFC) or `crore` (IndusInd) — **the two banks disclose in different units**; see below |
| unweighted_inr_crore, weighted_inr_crore | float | The same two value columns, converted to a common Rs crore basis (1 crore = 10 million). Use these, not the raw `unweighted`/`weighted` columns, for any comparison of absolute rupee figures across the two banks |

**Units.** HDFC Bank's disclosures state "₹ in million"; IndusInd Bank's state
"Rs in Crores" — read directly off each PDF's own header, not assumed. Every
ratio in this project (LCR%, funding-mix %, deposit-stability %) is computed
within one bank's own figures, so the unit difference never touched a
reconciliation or a comparison here. It only matters the moment someone
reaches for an absolute rupee number across banks — which is exactly why the
`_inr_crore` columns exist, rather than leaving that conversion to be done
correctly (or not) by whoever opens the CSV next.

## `data/final/hqla_validation.csv`

One row per bank-quarter. Confirms the disclosure's two copies of Total HQLA
(row 1 at the top, row 13 restated just above the ratio) agree with each
other, and recomputes LCR% from HQLA and the disclosed Net Cash Outflows as a
cross-check against the bank's own printed ratio.

| Column | Meaning |
|---|---|
| hqla_row1, hqla_row13 | The two disclosed copies of Total HQLA |
| hqla_internally_consistent | `True` if they match |
| net_cash_outflows_row14 | Disclosed Total Net Cash Outflows |
| lcr_disclosed_pct | The bank's own printed LCR% |
| lcr_recomputed_from_hqla_pct | HQLA ÷ Net Cash Outflows × 100 |
| lcr_gap_pct_points | Difference between the two |

## `data/final/lcr_reconciliation.csv`

One row per bank-quarter — the core reconstruction. Rebuilds Total Outflows,
Total Inflows, the 75% inflow cap, and Net Cash Outflows independently from
the row-level weighted figures (rows 2–7 for outflows, 9–11 for inflows), then
compares each to the bank's own printed subtotal.

| Column | Meaning |
|---|---|
| total_outflows_computed / _disclosed / outflows_gap | Sum of weighted rows 2–7, vs. the bank's own row 8, and the difference |
| total_inflows_computed / _disclosed / inflows_gap | Sum of weighted rows 9–11, vs. row 12 |
| inflow_cap_75pct | 75% of total_outflows_computed |
| inflow_cap_binding | Whether inflows exceeded the cap (`True`/`False`) — never true in this dataset; see LIMITATIONS.md |
| net_outflows_computed / _disclosed / net_outflows_gap | Outflows minus capped inflows, vs. row 14 |
| lcr_computed_pct / lcr_disclosed_pct / lcr_gap_pct_points | HQLA ÷ net_outflows_computed × 100, vs. row 15, and the gap |

## `data/final/funding_concentration.csv`

One row per bank-quarter — funding mix and retail-deposit stability, all
computed from **unweighted** (raw balance) figures.

| Column | Meaning |
|---|---|
| retail_deposits, wholesale_unsecured_funding | Row 2 and row 3, unweighted |
| funding_base_ex_secured | Sum of the two above. Secured wholesale funding (row 4) is excluded — no bank in this dataset discloses its unweighted balance, in any quarter |
| retail_pct_of_funding_base, wholesale_pct_of_funding_base | Composition of that funding base |
| less_stable_pct_of_retail, stable_pct_of_retail | Row 2ii / 2i as a share of row 2 |
| non_operational_pct_of_wholesale, operational_pct_of_wholesale, unsecured_debt_pct_of_wholesale | Row 3ii / 3i / 3iii as a share of row 3 |

## `data/final/comparative_summary.csv` and `comparative_verdict.json`

One row per bank — trend and level summary across the 5 quarters (LCR level,
min, max, 5-quarter trend; wholesale-funding share and its trend;
less-stable-retail share and its trend; reconciliation pass rate). The JSON
adds the written comparative finding built from those numbers.

## Row IDs, in full

| row_id | Label |
|---|---|
| 1 | Total High Quality Liquid Assets (HQLA) |
| 2 / 2i / 2ii | Retail deposits — of which stable / less stable |
| 3 / 3i / 3ii / 3iii | Unsecured wholesale funding — of which operational / non-operational deposits / unsecured debt |
| 4 | Secured wholesale funding |
| 5 / 5i / 5ii / 5iii | Additional requirements — of which derivative/collateral outflows / loss of funding on debt products / credit & liquidity facilities |
| 6 | Other contractual funding obligations |
| 7 | Other contingent funding obligations |
| 8 | Total Cash Outflows |
| 9 | Secured lending |
| 10 | Inflows from fully performing exposures |
| 11 | Other cash inflows |
| 12 | Total Cash Inflows |
| 13 | Total HQLA (restated) |
| 14 | Total Net Cash Outflows |
| 15 | Liquidity Coverage Ratio (%) |
