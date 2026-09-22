"""Pull the LCR disclosure table out of a bank's Basel III PDF.

The RBI's public LCR disclosure template is the same 15 numbered rows for
every scheduled commercial bank, but the two banks' PDFs render that grid
with different column counts, different padding-cell layouts, and — for
the multi-quarter history tables — a table that splits across a page break
with the header repeated on the far side. Chasing that by text position
turned out to be fragile (see git history if curious); this version reads
pdfplumber's own bordered-table extraction and classifies each *cell* by
what it contains — a row marker, label text, or a numeric value — rather
than by which column index it happens to land in. That's layout-agnostic:
it doesn't matter how many blank padding columns a given page inserts.
"""
import re
import pdfplumber

TABLE_SETTINGS = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}

MARKER_RE = re.compile(r"^\(?[ivx]{1,4}\)?$|^\d{1,2}$", re.IGNORECASE)
VALUE_RE = re.compile(r"^-?[\d,]+\.\d{1,2}%?$|^-$")

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}
_MONTH_ALT = "|".join(MONTHS)
DATE_WITH_DAY_RE = re.compile(rf"({_MONTH_ALT})\.?,?\s+(\d{{1,2}}),?\s*,?\s*(\d{{4}})")
DATE_MONTH_ONLY_RE = re.compile(rf"^({_MONTH_ALT})\s+(\d{{4}})$")
QUARTER_END_DAY = {3: 31, 6: 30, 9: 30, 12: 31}

# row_id -> (label substring for a human-readable check, values disclosed per quarter)
ROW_SCHEMA = {
    "1": ("Total High Quality Liquid Assets", 1),
    "2": ("Retail deposits", 2),
    "2i": ("Stable deposits", 2),
    "2ii": ("Less stable deposits", 2),
    "3": ("Unsecured wholesale funding", 2),
    "3i": ("Operational deposits", 2),
    "3ii": ("Non-operational deposits", 2),
    "3iii": ("Unsecured debt", 2),
    "4": ("Secured wholesale funding", 1),
    "5": ("Additional requirements", 2),
    "5i": ("collateral", 2),
    "5ii": ("loss of funding", 2),
    "5iii": ("Credit and liquidity facilities", 2),
    "6": ("Other contractual funding", 2),
    "7": ("Other contingent funding", 2),
    "8": ("Total Cash Outflows", 1),
    "9": ("Secured lending", 2),
    "10": ("Inflows from fully performing", 2),
    "11": ("Other cash inflows", 2),
    "12": ("Total Cash Inflows", 2),
    "13": ("TOTAL HQLA", 1),
    "14": ("Total Net Cash Outflows", 1),
    "15": ("Liquidity Coverage Ratio", 1),
}
# Bare digits that open a numbered sub-item section; every (i)/(ii)/(iii)
# row that follows belongs to whichever of these was seen most recently.
SUB_ITEM_PARENTS = {"2", "3", "5"}


def _cell_kind(cell: str) -> str:
    if MARKER_RE.match(cell):
        return "marker"
    if VALUE_RE.match(cell):
        return "value"
    return "label"


def _parse_value(tok: str) -> float:
    tok = tok.strip().rstrip("%")
    return 0.0 if tok == "-" else float(tok.replace(",", ""))


def _quarters_in_table(table: list[list]) -> list[str]:
    """Read the quarter-end dates off the table's own first two rows."""
    header_text = " | ".join(
        c for row in table[:2] for c in row if c and c.strip()
    )
    quarters, seen = [], set()
    for m in DATE_WITH_DAY_RE.finditer(header_text):
        month, day, year = m.group(1), int(m.group(2)), int(m.group(3))
        iso = f"{year:04d}-{MONTHS[month]:02d}-{day:02d}"
        if iso not in seen:
            seen.add(iso)
            quarters.append(iso)
    if quarters:
        return quarters
    # Bare "Month YYYY" column headers (no day-of-month) — RBI quarters
    # always end on a fixed date, so the day is inferable from the month.
    for cell in header_text.split(" | "):
        m = DATE_MONTH_ONLY_RE.match(cell.strip())
        if m:
            month, year = m.group(1), int(m.group(2))
            month_num = MONTHS[month]
            if month_num in QUARTER_END_DAY:
                iso = f"{year:04d}-{month_num:02d}-{QUARTER_END_DAY[month_num]:02d}"
                if iso not in seen:
                    seen.add(iso)
                    quarters.append(iso)
    return quarters


def _parse_row(row: list) -> tuple[str | None, str, list[str]]:
    marker, label_parts, values = None, [], []
    for cell in row:
        if cell is None:
            continue
        cell = " ".join(cell.split())  # collapse embedded newlines/whitespace
        if not cell:
            continue
        kind = _cell_kind(cell)
        if kind == "marker" and marker is None:
            marker = cell.strip("()").lower()
        elif kind == "value":
            values.append(cell)
        else:
            label_parts.append(cell)
    return marker, " ".join(label_parts), values


def _row_id_for(marker: str, current_parent: str | None) -> str | None:
    if marker.isdigit():
        return marker
    if current_parent is not None:
        return f"{current_parent}{marker}"
    return None


def extract_pdf(pdf_path) -> list[dict]:
    """Return one row per (quarter, disclosure row) as a flat list of dicts.

    A single PDF's table can straddle a page break (the trailing-history
    disclosures do), so every page is scanned and results are merged by
    row_id + quarter; the same cell reappearing on both sides of the split
    (a repeated header) is naturally deduplicated at that point.
    """
    records: dict[tuple[str, str], dict] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables(TABLE_SETTINGS)
            for table in tables:
                if len(table) < 10:
                    continue  # the run-off-factor / trailing-LCR reference tables
                quarters = _quarters_in_table(table)
                if not quarters:
                    continue
                current_parent = None
                for row in table:
                    marker, label, values = _parse_row(row)
                    if marker is None:
                        continue
                    row_id = _row_id_for(marker, current_parent)
                    if marker in SUB_ITEM_PARENTS:
                        current_parent = marker
                    if row_id is None or row_id not in ROW_SCHEMA:
                        continue
                    if not quarters:
                        continue
                    # A stray extra ruling line in the source PDF can split
                    # one column into two identical ones for a single row
                    # (observed on IndusInd's row 7) — every value shows up
                    # twice in a row. Collapse exact adjacent duplicate
                    # pairs before sizing the row; genuinely distinct
                    # quarters reporting the same figure by coincidence
                    # would not pair up across the *whole* row this way.
                    if len(values) == 4 * len(quarters) and all(
                        values[i] == values[i + 1] for i in range(0, len(values), 2)
                    ):
                        values = values[0::2]
                    # Whether a "Total ..." row discloses both the
                    # unweighted and weighted figure, or the weighted
                    # figure only, isn't fixed by the row — HDFC gives both
                    # for row 12 (Total Cash Inflows), IndusInd gives only
                    # the weighted total for the same row. Infer the count
                    # from what's actually present rather than assuming it.
                    if len(values) % len(quarters) != 0:
                        # A row that is genuinely nil across every quarter is
                        # sometimes rendered with blank cells rather than a
                        # written "-" for some of its columns (seen on
                        # IndusInd's 4-quarter file, rows 3iii/4/5iii) — a
                        # blank cell in that spot carries the same meaning as
                        # a written dash. Only pad when every value actually
                        # present is already a dash; a genuinely incomplete
                        # copy of a row with real numbers still gets skipped.
                        if values and all(v.strip() == "-" for v in values):
                            declared_n = ROW_SCHEMA[row_id][1]
                            values = ["-"] * (declared_n * len(quarters))
                        else:
                            continue  # incomplete copy of this row; the other page's isn't
                    n_per_quarter = len(values) // len(quarters)
                    if n_per_quarter not in (1, 2):
                        continue
                    for qi, q in enumerate(quarters):
                        chunk = values[qi * n_per_quarter:(qi + 1) * n_per_quarter]
                        if n_per_quarter == 1:
                            unweighted, weighted = None, _parse_value(chunk[0])
                        else:
                            unweighted, weighted = _parse_value(chunk[0]), _parse_value(chunk[1])
                        records[(q, row_id)] = {
                            "quarter": q,
                            "row_id": row_id,
                            "label": ROW_SCHEMA[row_id][0],
                            "unweighted": unweighted,
                            "weighted": weighted,
                        }

    missing = {
        (q, rid)
        for q in {r["quarter"] for r in records.values()}
        for rid in ROW_SCHEMA
    } - set(records)
    if missing:
        raise ValueError(f"{pdf_path}: missing rows {sorted(missing)}")
    return list(records.values())


if __name__ == "__main__":
    import sys
    import pandas as pd
    from config import RAW_DIR, PROCESSED_DIR, SOURCE_FILES, UNIT_TO_CRORE

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for src in SOURCE_FILES:
        path = RAW_DIR / src["file"]
        rows = extract_pdf(path)
        for r in rows:
            r["bank"] = src["bank"]
            r["source_file"] = src["file"]
            r["unit"] = src["unit"]
        all_rows.extend(rows)
        print(f"extracted {len(rows)} row-quarter records from {src['file']}", file=sys.stderr)

    df = pd.DataFrame(all_rows)
    df = df.drop_duplicates(subset=["bank", "quarter", "row_id"], keep="first")
    # Rs crore-equivalent columns, for any downstream use that compares raw
    # figures across banks rather than within one bank's own ratios.
    factor = df["unit"].map(UNIT_TO_CRORE)
    df["unweighted_inr_crore"] = df["unweighted"] * factor
    df["weighted_inr_crore"] = df["weighted"] * factor
    out_path = PROCESSED_DIR / "lcr_disclosure_lines.csv"
    df.to_csv(out_path, index=False)
    print(f"wrote {len(df)} rows to {out_path}", file=sys.stderr)
