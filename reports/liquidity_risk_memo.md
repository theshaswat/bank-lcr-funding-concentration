# HDFC Bank vs IndusInd Bank: reconciled LCR and funding quality, Jun 2025–Jun 2026

**Shaswat Sharma**

## The finding

IndusInd Bank's disclosed LCR has beaten HDFC Bank's in every one of the
last five quarters — 126.66% vs 115.00% as of June 2026, and the gap hasn't
closed. Read on its own, that ranks IndusInd as the more liquid of the two.
Underneath the ratio, IndusInd's funding base looks the other way: 40.9% of
it is wholesale funding against HDFC's 33.1%, and of the retail deposits it
does hold, 95.3% are classified less-stable under the RBI's own run-off
rules, against 77.6% at HDFC. Both gaps have held across all five quarters —
this isn't one noisy reading. A bank can post a stronger LCR by holding more
HQLA against a thinner, less sticky funding base and still be carrying more
funding risk than a bank with a lower ratio and a deeper retail base. That's
the case here.

## What was reconciled, and how

Both banks' LCR was rebuilt from their own disclosed category-level cash
flows — not taken on faith from the printed ratio. Total Cash Outflows
(rows 2–7 of the RBI's public template) and Total Cash Inflows (rows 9–11)
were summed independently, the 75% inflow cap applied, and the resulting Net
Cash Outflows and LCR% checked against each bank's own printed figures. 9 of
10 bank-quarters land within 0.05 percentage points — most at an exact 0.00
gap. Source: each bank's own quarterly Basel III Pillar 3 LCR disclosure PDF,
five quarters each (Jun 2025 through Jun 2026), 230 individual disclosure
lines in total.

## The one that didn't reconcile

HDFC's September 2025 quarter doesn't reconcile. Total Outflows and Total
Inflows both match the PDF's printed figures exactly; Net Cash Outflows
doesn't follow from them — it's about ₹4,195 crore lower than the standard
formula implies. This is the September 2025 column as it appears *restated*
inside HDFC's March 2026 filing, not the originally-filed quarter. I checked
the raw extracted table cells directly before accepting this as real rather
than a parsing artifact, and it holds. I don't have a confirmed explanation
for it — a restatement that updated the outflow and inflow lines without
carrying the update through to the net figure, and a rounding or averaging
convention that changed between the original Sep-2025 filing and its later
reprint, are both consistent with what the PDF shows, and public disclosure
alone doesn't let me tell which. It's reported as a break, not folded into
the other nine.

## One thing that doesn't fit the story above

Both banks' LCR has been declining across these five quarters — HDFC down
8.8 points from its Jun-2025 level, IndusInd down 14.6. Whatever is driving
that (loan growth outpacing HQLA growth, a change in deposit mix, something
sector-wide) isn't something this dataset can isolate, and it isn't
particular to the wholesale-funding story above — HDFC's wholesale share
actually rose slightly over the same period while its LCR fell. Worth
flagging as a separate question rather than folding it into the funding-
quality finding, which it doesn't actually explain.

## What this doesn't establish

The inflow cap never binds for either bank in any of the 10 quarters here,
so the cap logic in this reconstruction is validated on the case where it
doesn't matter, not the case where it does. And the RBI's public template
gives Total HQLA as one number — there's no Level 1/2A/2B split to check the
composition of *what* either bank is holding as HQLA, only how much. Two
banks, five quarters, is a comparison of these two funding profiles, not a
system-wide read on Indian bank liquidity. Full detail in
[`LIMITATIONS.md`](LIMITATIONS.md).

## Sources

- HDFC Bank, Consolidated Liquidity Coverage Ratio disclosures, quarters
  ended Jun 30 2026 and Mar 31 2026 (the latter carrying Dec-2025, Sep-2025
  and Jun-2025 as comparative columns) — hdfc.bank.in
- IndusInd Bank, Basel III Disclosure – Liquidity Coverage Ratio, quarters
  ended Jun 30 2026 and Mar 31 2026 (same comparative-column structure) —
  indusind.bank.in
