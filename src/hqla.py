"""Validate Total HQLA as disclosed.

The RBI's public LCR template gives a single Total HQLA figure (rows 1 and
13 of the disclosure — the same number, stated twice: once as the input to
the ratio, once as the summary line above it). It does not publish the
Level 1 / Level 2A / Level 2B split or the haircuts applied to reach that
total — that breakdown exists only in supervisory (non-public) reporting.
So there is nothing to rebuild here from components; what this module does
is confirm the two disclosed copies of Total HQLA agree with each other and
with what the bank used to compute its own published ratio, for every
bank-quarter in the dataset.
"""
import pandas as pd

from config import PROCESSED_DIR, FINAL_DIR


def validate_hqla(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (bank, quarter), g in df.groupby(["bank", "quarter"]):
        g = g.set_index("row_id")
        hqla_top = g.loc["1", "weighted"]
        hqla_restated = g.loc["13", "weighted"]
        net_outflows = g.loc["14", "weighted"]
        lcr_disclosed = g.loc["15", "weighted"]
        lcr_from_hqla = round(hqla_restated / net_outflows * 100, 2) if net_outflows else None
        rows.append({
            "bank": bank,
            "quarter": quarter,
            "hqla_row1": hqla_top,
            "hqla_row13": hqla_restated,
            "hqla_internally_consistent": hqla_top == hqla_restated,
            "net_cash_outflows_row14": net_outflows,
            "lcr_disclosed_pct": lcr_disclosed,
            "lcr_recomputed_from_hqla_pct": lcr_from_hqla,
            "lcr_gap_pct_points": round(lcr_from_hqla - lcr_disclosed, 4) if lcr_from_hqla is not None else None,
        })
    return pd.DataFrame(rows).sort_values(["bank", "quarter"])


if __name__ == "__main__":
    import sys

    df = pd.read_csv(PROCESSED_DIR / "lcr_disclosure_lines.csv")
    out = validate_hqla(df)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FINAL_DIR / "hqla_validation.csv"
    out.to_csv(out_path, index=False)
    print(out.to_string(index=False), file=sys.stderr)
    if not out["hqla_internally_consistent"].all():
        bad = out[~out["hqla_internally_consistent"]]
        raise ValueError(f"HQLA rows 1 and 13 disagree for:\n{bad}")
    print(f"\nwrote {out_path}", file=sys.stderr)
