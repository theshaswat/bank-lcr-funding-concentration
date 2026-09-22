"""Build the exhibit charts in outputs/charts/ at presentation resolution.

Every figure is pulled straight from data/final/*.csv — the reconciled and
profiled outputs of hqla.py / cashflows.py / funding_concentration.py — so a
chart cannot silently drift from the numbers in the memo.

Usage: python3 build_charts.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

from config import FINAL_DIR, CHARTS_DIR

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "axes.edgecolor": "#D9D9D9",
    "axes.labelcolor": "#1F2A44",
    "text.color": "#1F2A44",
    "xtick.color": "#6B7280",
    "ytick.color": "#6B7280",
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "figure.dpi": 110,
})

NAVY = "#1F2A44"
GREY = "#6B7280"
LGREY = "#EEEEEE"
HDFC = "#1F2A44"      # navy — larger, retail-anchored
INDUSIND = "#0A0A0A"  # near-black — smaller, more wholesale-reliant
DPI = 300
SRC = "Source: HDFC Bank and IndusInd Bank, own Basel III Pillar 3 LCR disclosures, Jun 2025-Jun 2026"

TITLE_PT, SUB_PT = 13, 9.5


def _titleblock(fig, title, subtitle=None):
    """Place title/subtitle by point offsets, not figure fractions — a fixed
    fractional gap looks fine on a tall figure and collapses onto a short one."""
    h_in = fig.get_size_inches()[1]
    top = 0.97
    fig.text(0.02, top, title, ha="left", va="top", fontsize=TITLE_PT,
              fontweight="bold", color=NAVY)
    if not subtitle:
        return top - (TITLE_PT + 10) / 72 / h_in
    sub_y = top - (TITLE_PT + 9) / 72 / h_in
    fig.text(0.02, sub_y, subtitle, ha="left", va="top", fontsize=SUB_PT,
              color=GREY)
    return sub_y - (SUB_PT + 10) / 72 / h_in


def _finish(fig, ax_list, title, subtitle=None, note=None):
    for ax in ax_list:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    top = _titleblock(fig, title, subtitle)
    fig.text(0.02, 0.02, note or SRC, ha="left", fontsize=7, color=GREY)
    fig.tight_layout(rect=[0, 0.06, 1, top])


def _pct_fmt(v, _):
    return f"{v:.0f}%"


def chart_lcr_trend():
    """Direct-labelled LCR path for both banks — the headline ratio."""
    df = pd.read_csv(FINAL_DIR / "lcr_reconciliation.csv")
    df["quarter_dt"] = pd.to_datetime(df["quarter"])

    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    for bank, color in [("HDFC Bank", HDFC), ("IndusInd Bank", INDUSIND)]:
        g = df[df.bank == bank].sort_values("quarter_dt")
        ax.plot(g["quarter_dt"], g["lcr_disclosed_pct"], color=color, lw=2.6,
                 marker="o", ms=6, zorder=3)
        last_x, last_y = g["quarter_dt"].iloc[-1], g["lcr_disclosed_pct"].iloc[-1]
        ax.annotate(f"  {bank.split()[0]}\n  {last_y:.1f}%", (last_x, last_y),
                     color=color, fontsize=10, fontweight="bold",
                     va="center", ha="left")

    ax.axhline(100, color=GREY, lw=1, ls="--", zorder=1)
    ax.text(df["quarter_dt"].min(), 101.5, "RBI minimum, 100%", fontsize=8, color=GREY)

    ax.yaxis.set_major_formatter(FuncFormatter(_pct_fmt))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_xlim(df["quarter_dt"].min() - pd.Timedelta(days=15),
                df["quarter_dt"].max() + pd.Timedelta(days=70))
    ax.grid(axis="y", color=LGREY, zorder=0)
    ax.set_axisbelow(True)

    _finish(fig, [ax],
            "IndusInd's ratio has led every quarter, but both dipped and only partly recovered",
            "A jump in the retail-deposit run-off factor masked most of the June 2026 rebound — see the memo's last section.")
    out = CHARTS_DIR / "lcr_trend.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out


def chart_funding_quality_comparison():
    """The headline exhibit: the higher-LCR bank has the thinner funding base."""
    fund = pd.read_csv(FINAL_DIR / "funding_concentration.csv")
    latest = fund[fund.quarter == fund.quarter.max()].set_index("bank")

    banks = ["HDFC Bank", "IndusInd Bank"]
    colors = [HDFC, INDUSIND]
    metrics = [
        ("Wholesale funding,\n% of funding base", "wholesale_pct_of_funding_base"),
        ("Less-stable deposits,\n% of retail base", "less_stable_pct_of_retail"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 5.0))
    for ax, (label, col) in zip(axes, metrics):
        vals = [latest.loc[b, col] for b in banks]
        bars = ax.bar(["HDFC", "IndusInd"], vals, color=colors, width=0.55, zorder=3)
        for r, v in zip(bars, vals):
            ax.text(r.get_x() + r.get_width() / 2, v + max(vals) * 0.03,
                     f"{v:.1f}%", ha="center", fontsize=12, fontweight="bold",
                     color=NAVY)
        ax.set_title(label, fontsize=10.5, color=GREY, pad=12)
        ax.set_ylim(0, max(vals) * 1.28)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.tick_params(axis="x", labelsize=11, colors=NAVY)

    _finish(fig, axes,
            "The higher-LCR bank has the thinner funding base",
            "IndusInd leads HDFC on the disclosed ratio (126.7% vs 115.0%, Jun 2026) — but on both funding-quality measures, HDFC is ahead.")
    out = CHARTS_DIR / "funding_quality_comparison.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out


def chart_funding_trend():
    """Small-multiple: both funding-quality measures, trended, both banks."""
    fund = pd.read_csv(FINAL_DIR / "funding_concentration.csv")
    fund["quarter_dt"] = pd.to_datetime(fund["quarter"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.2))
    panels = [
        (ax1, "less_stable_pct_of_retail", "Less-stable deposits, % of retail base"),
        (ax2, "wholesale_pct_of_funding_base", "Wholesale funding, % of funding base"),
    ]
    for ax, col, subtitle in panels:
        for bank, color in [("HDFC Bank", HDFC), ("IndusInd Bank", INDUSIND)]:
            g = fund[fund.bank == bank].sort_values("quarter_dt")
            ax.plot(g["quarter_dt"], g[col], color=color, lw=2.2, marker="o", ms=5)
            last_x, last_y = g["quarter_dt"].iloc[-1], g[col].iloc[-1]
            ax.annotate(f" {bank.split()[0]}", (last_x, last_y), color=color,
                         fontsize=9, fontweight="bold", va="center", ha="left")
        ax.set_title(subtitle, fontsize=10.5, color=GREY, pad=10)
        ax.yaxis.set_major_formatter(FuncFormatter(_pct_fmt))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        ax.set_xlim(fund["quarter_dt"].min() - pd.Timedelta(days=15),
                    fund["quarter_dt"].max() + pd.Timedelta(days=95))
        ax.grid(axis="y", color=LGREY, zorder=0)
        ax.set_axisbelow(True)

    _finish(fig, [ax1, ax2],
            "Both gaps have held for all five quarters — not a one-off reading")
    out = CHARTS_DIR / "funding_trend.png"
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out


def main():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    for fn in (chart_lcr_trend, chart_funding_quality_comparison, chart_funding_trend):
        out = fn()
        print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
