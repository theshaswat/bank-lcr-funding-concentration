"""Paths and the two-bank, multi-quarter universe this project runs on."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
FINAL_DIR = ROOT / "data" / "final"
TABLES_DIR = ROOT / "outputs" / "tables"
CHARTS_DIR = ROOT / "outputs" / "charts"
REPORTS_DIR = ROOT / "reports"

# One entry per source PDF. Some PDFs carry more than one quarter's columns
# (the banks republish trailing history alongside the current quarter), so a
# single file can seed several rows in the processed dataset.
#
# "unit" matters: HDFC's disclosures are denominated in Rs million; IndusInd's
# are denominated in Rs crore (1 crore = 10 million) — confirmed by reading
# each PDF's own unit label, not assumed. Every ratio computed downstream
# (LCR%, funding-mix %, deposit-stability %) is scale-invariant within a
# bank's own figures, so this never affected any reconciliation or comparison
# in this project. It matters only if raw figures are ever compared in
# absolute Rs terms across the two banks — see "inr_crore" in extract.py.
SOURCE_FILES = [
    {"bank": "HDFC Bank", "file": "hdfc_bank_q1fy26_jun2026.pdf", "unit": "million"},
    {"bank": "HDFC Bank", "file": "hdfc_bank_q4fy26_mar2026.pdf", "unit": "million"},
    {"bank": "IndusInd Bank", "file": "indusind_bank_q1fy27_jun2026.pdf", "unit": "crore"},
    {"bank": "IndusInd Bank", "file": "indusind_bank_q4fy26_mar2026.pdf", "unit": "crore"},
]

UNIT_TO_CRORE = {"million": 0.1, "crore": 1.0}

# The quarter pair the reconciliation gate is scored on. Both banks disclose
# a longer trailing history (used for the funding-concentration trend), but
# the tolerance check in Section 5 of the build only has to hold for these.
GATE_QUARTERS = ["2026-06-30", "2026-03-31"]

TOLERANCE_PCT_POINTS = 0.05  # LCR reconstruction must land within +/-0.05pp
