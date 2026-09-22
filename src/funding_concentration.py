"""Profile each bank's funding mix and its stability, trended by quarter.

Reconciling the ratio (extract.py / hqla.py / cashflows.py) answers whether
a bank clears 100% LCR. It says nothing about how it clears it — two banks
can both print a comfortable LCR while resting on very different funding
bases. This module builds that comparison from the same disclosed rows:

    Retail deposits (row 2)                — split stable (2i) / less
                                              stable (2ii)
    Unsecured wholesale funding (row 3)    — split operational (3i) /
                                              non-operational (3ii) /
                                              unsecured debt (3iii)

Secured wholesale funding (row 4) is deliberately left out of the funding
base: the public template never discloses its raw (unweighted) balance for
either bank in any of the 10 bank-quarters here, only the post-haircut
weighted figure — there's no unweighted number to add in without inventing
one.

All ratios use unweighted (raw balance) figures, not the run-off-weighted
ones — the weighting reflects assumed stress behaviour, which is exactly
the thing this profile is trying to characterise, not something to bake
into the denominator.
"""
import pandas as pd

from config import PROCESSED_DIR, FINAL_DIR, TABLES_DIR, CHARTS_DIR


def profile_funding(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (bank, quarter), g in df.groupby(["bank", "quarter"]):
        g = g.set_index("row_id")

        retail = g.loc["2", "unweighted"]
        retail_stable = g.loc["2i", "unweighted"]
        retail_less_stable = g.loc["2ii", "unweighted"]

        wholesale = g.loc["3", "unweighted"]
        wholesale_operational = g.loc["3i", "unweighted"]
        wholesale_non_operational = g.loc["3ii", "unweighted"]
        wholesale_unsecured_debt = g.loc["3iii", "unweighted"]

        funding_base = retail + wholesale

        rows.append({
            "bank": bank,
            "quarter": quarter,
            "retail_deposits": retail,
            "wholesale_unsecured_funding": wholesale,
            "funding_base_ex_secured": funding_base,
            "retail_pct_of_funding_base": round(100 * retail / funding_base, 2),
            "wholesale_pct_of_funding_base": round(100 * wholesale / funding_base, 2),
            "less_stable_pct_of_retail": round(100 * retail_less_stable / retail, 2),
            "stable_pct_of_retail": round(100 * retail_stable / retail, 2),
            "non_operational_pct_of_wholesale": round(100 * wholesale_non_operational / wholesale, 2),
            "operational_pct_of_wholesale": round(100 * wholesale_operational / wholesale, 2) if wholesale else None,
            "unsecured_debt_pct_of_wholesale": round(100 * wholesale_unsecured_debt / wholesale, 2),
        })
    return pd.DataFrame(rows).sort_values(["bank", "quarter"])


def _plot(out: pd.DataFrame, charts_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    charts_dir.mkdir(parents=True, exist_ok=True)
    out = out.copy()
    out["quarter_dt"] = pd.to_datetime(out["quarter"])

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for bank, g in out.groupby("bank"):
        g = g.sort_values("quarter_dt")
        ax.plot(g["quarter_dt"], g["less_stable_pct_of_retail"], marker="o", linewidth=2, label=bank)
    ax.set_title("Less-stable share of retail deposits, by quarter")
    ax.set_ylabel("% of retail deposits classified less-stable")
    ax.set_xlabel("Quarter end")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.legend()
    ax.grid(alpha=0.3)
    ax.annotate("Source: each bank's own Basel III Pillar 3 LCR disclosure",
                xy=(0.0, -0.16), xycoords="axes fraction", fontsize=8, color="grey")
    fig.tight_layout()
    fig.savefig(charts_dir / "less_stable_deposit_share_trend.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for bank, g in out.groupby("bank"):
        g = g.sort_values("quarter_dt")
        ax.plot(g["quarter_dt"], g["wholesale_pct_of_funding_base"], marker="o", linewidth=2, label=bank)
    ax.set_title("Wholesale funding as % of retail + unsecured-wholesale funding base")
    ax.set_ylabel("% of funding base")
    ax.set_xlabel("Quarter end")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.legend()
    ax.grid(alpha=0.3)
    ax.annotate("Source: each bank's own Basel III Pillar 3 LCR disclosure. "
                "Secured wholesale funding excluded — raw balance not disclosed.",
                xy=(0.0, -0.16), xycoords="axes fraction", fontsize=8, color="grey")
    fig.tight_layout()
    fig.savefig(charts_dir / "wholesale_funding_share_trend.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    import sys

    df = pd.read_csv(PROCESSED_DIR / "lcr_disclosure_lines.csv")
    out = profile_funding(df)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(FINAL_DIR / "funding_concentration.csv", index=False)
    out.to_csv(TABLES_DIR / "funding_concentration_summary.csv", index=False)
    _plot(out, CHARTS_DIR)

    print(out.to_string(index=False), file=sys.stderr)
    print(f"\nwrote {FINAL_DIR / 'funding_concentration.csv'}", file=sys.stderr)
    print(f"wrote {CHARTS_DIR / 'less_stable_deposit_share_trend.png'}", file=sys.stderr)
    print(f"wrote {CHARTS_DIR / 'wholesale_funding_share_trend.png'}", file=sys.stderr)
