"""Reconstruct the LCR from its disclosed category-level cash flows.

Every quarter's disclosure gives the weighted (post-run-off-factor) value
for each outflow and inflow category. This rebuilds the ratio from those
category figures rather than trusting the bank's own printed subtotals:

    Total Outflows        = sum of weighted rows 2, 3, 4, 5, 6, 7
    Total Inflows          = sum of weighted rows 9, 10, 11
    Inflow cap              = 75% of Total Outflows
    Total Net Cash Outflows = Total Outflows - min(Total Inflows, cap)
    LCR%                    = Total HQLA / Total Net Cash Outflows * 100

Each computed figure is then checked against the bank's own printed
subtotal for that line (rows 8, 12, 14, 15) within TOLERANCE_PCT_POINTS.
"""
import pandas as pd

from config import PROCESSED_DIR, FINAL_DIR, TABLES_DIR, TOLERANCE_PCT_POINTS

OUTFLOW_ROWS = ["2", "3", "4", "5", "6", "7"]
INFLOW_ROWS = ["9", "10", "11"]
INFLOW_CAP_RATE = 0.75


def reconcile(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (bank, quarter), g in df.groupby(["bank", "quarter"]):
        g = g.set_index("row_id")

        total_outflows_computed = g.loc[OUTFLOW_ROWS, "weighted"].sum()
        total_outflows_disclosed = g.loc["8", "weighted"]

        total_inflows_computed = g.loc[INFLOW_ROWS, "weighted"].sum()
        total_inflows_disclosed = g.loc["12", "weighted"]

        cap = INFLOW_CAP_RATE * total_outflows_computed
        inflows_after_cap = min(total_inflows_computed, cap)
        net_outflows_computed = total_outflows_computed - inflows_after_cap
        net_outflows_disclosed = g.loc["14", "weighted"]

        hqla = g.loc["1", "weighted"]
        lcr_computed = round(hqla / net_outflows_computed * 100, 2) if net_outflows_computed else None
        lcr_disclosed = g.loc["15", "weighted"]

        rows.append({
            "bank": bank,
            "quarter": quarter,
            "total_outflows_computed": round(total_outflows_computed, 2),
            "total_outflows_disclosed": total_outflows_disclosed,
            "outflows_gap": round(total_outflows_computed - total_outflows_disclosed, 2),
            "total_inflows_computed": round(total_inflows_computed, 2),
            "total_inflows_disclosed": total_inflows_disclosed,
            "inflows_gap": round(total_inflows_computed - total_inflows_disclosed, 2),
            "inflow_cap_75pct": round(cap, 2),
            "inflow_cap_binding": total_inflows_computed > cap,
            "net_outflows_computed": round(net_outflows_computed, 2),
            "net_outflows_disclosed": net_outflows_disclosed,
            "net_outflows_gap": round(net_outflows_computed - net_outflows_disclosed, 2),
            "lcr_computed_pct": lcr_computed,
            "lcr_disclosed_pct": lcr_disclosed,
            "lcr_gap_pct_points": round(lcr_computed - lcr_disclosed, 4) if lcr_computed is not None else None,
        })
    return pd.DataFrame(rows).sort_values(["bank", "quarter"])


if __name__ == "__main__":
    import sys

    df = pd.read_csv(PROCESSED_DIR / "lcr_disclosure_lines.csv")
    out = reconcile(df)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FINAL_DIR / "lcr_reconciliation.csv"
    out.to_csv(out_path, index=False)
    out[["bank", "quarter", "lcr_computed_pct", "lcr_disclosed_pct", "lcr_gap_pct_points"]].to_csv(
        TABLES_DIR / "lcr_reconciliation_summary.csv", index=False
    )

    print(out.to_string(index=False), file=sys.stderr)

    failing = out[out["lcr_gap_pct_points"].abs() > TOLERANCE_PCT_POINTS]
    if not failing.empty:
        print(f"\n{len(failing)} of {len(out)} bank-quarters exceed the "
              f"{TOLERANCE_PCT_POINTS}pp tolerance:", file=sys.stderr)
        print(failing.to_string(index=False), file=sys.stderr)
    else:
        print(f"\nall {len(out)} bank-quarters reconcile within "
              f"{TOLERANCE_PCT_POINTS}pp", file=sys.stderr)
    print(f"wrote {out_path}", file=sys.stderr)
