# Limitations & Assumptions

## What this project is, and isn't

This reconstructs the LCR from the category-level subtotals each bank
already discloses — it validates the aggregation logic (do the disclosed
outflow categories sum to the disclosed total, does the 75% inflow cap apply
correctly, does HQLA ÷ Net Cash Outflows land on the disclosed ratio) rather
than rebuilding HQLA from individual asset-level haircuts. That second thing
isn't possible from public data: RBI's disclosure template gives a single
Total HQLA figure, not the Level 1 / Level 2A / Level 2B breakdown that would
be needed to rebuild it bottom-up. That breakdown exists only in supervisory
reporting banks file with RBI directly, which isn't public. `hqla.py`
validates the one number that is public, rather than pretending to a
precision the source data doesn't support.

## The HDFC Sep-2025 reconciliation break

9 of the 10 bank-quarters in this dataset reconcile to the ±0.05 percentage
point tolerance exactly — most land at a 0.00 gap. One doesn't: HDFC's
September 2025 quarter, as restated in the comparative column of HDFC's own
March 2026 filing. Total Outflows and Total Inflows both match the PDF's
printed figures exactly; Net Cash Outflows doesn't follow from them by the
standard formula — it's about ₹41,955 crore lower than Outflows minus Inflows
implies. I checked this against the raw extracted table cells directly (not
just the downstream computation) to rule out a parsing bug before accepting
it as real, and it holds. I don't have a confirmed explanation. The two most
plausible ones — a restatement that updated the outflow/inflow lines without
updating the net figure in the same pass, or a rounding/averaging
methodology change between when Sep-2025 was originally filed and when it
was reprinted as a comparative column eight months later — are both
consistent with what's in the PDF, and I can't distinguish between them from
public disclosure alone. It's reported as a break, not smoothed into the
other nine.

## The 75% inflow cap never binds in this dataset

For both banks, in every quarter, computed Total Cash Inflows sit well below
75% of computed Total Outflows — nowhere close to binding. That's arguably
the expected case for well-capitalized retail-funded banks (a bank with a
large inflow base relative to its outflows would look aggressive on the LCR
formula's own terms), but it also means this project's cap logic is
validated on the "cap doesn't matter" case in every single observation.
Whether the aggregation would still hold under stress — a bank where the cap
actually binds — is untested here.

## Secured wholesale funding has no disclosed raw balance

Row 4 (Secured wholesale funding) never has an unweighted figure in either
bank's disclosure, in any of the 10 bank-quarters. Only its weighted
(post-haircut) value is given. The funding-concentration profile in
`funding_concentration.py` is built from retail deposits + unsecured
wholesale funding only, with secured wholesale funding excluded rather than
estimated. In practice this is a small omission next to the rest of the
funding base — row 4's weighted values run ₹4,877–11,046 crore across
HDFC's five quarters against a funding base of ₹23–27 lakh crore, and
IndusInd discloses ₹0 for this row in every quarter — but it's excluded
because there's no unweighted balance to include, not because it's been
checked and found negligible in unweighted terms (the weighted, post-haircut
figure isn't the same number).

## HDFC and IndusInd disclose in different currency units

HDFC's PDFs are denominated in ₹ million; IndusInd's are in ₹ crore. Every
ratio computed in this project is scale-invariant within one bank's own
figures, so this never affected a reconciliation or a cross-bank percentage
comparison. It does mean the raw `unweighted`/`weighted` columns in
`lcr_disclosure_lines.csv` are not directly comparable in absolute rupee
terms across the two banks without conversion — which is why
`unweighted_inr_crore` and `weighted_inr_crore` columns exist alongside them.

## Two banks, five quarters

This isn't a system-wide or sector-wide claim. HDFC and IndusInd were picked
for a genuine funding-profile contrast — one large and retail-deposit-heavy,
one smaller with a much higher less-stable-deposit share — not as a random
or representative sample of Indian banks. The comparative finding in
`reports/liquidity_risk_memo.md` is a finding about these two banks over
these five quarters, not a generalization to the banking system.

## Quarterly, average-balance, backward-looking

The disclosed figures are quarterly averages (both banks' templates say so),
not point-in-time or daily figures, and both intra-quarter volatility and any
subsequent quarter's numbers are outside this dataset. There's no attempt
here to model what either bank's LCR would do under a live stress scenario —
that's a different kind of project (scenario design), not a reconciliation
of what's already been disclosed.
