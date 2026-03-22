"""
figure6.py — Roy et al. (2026), Communications Earth & Environment

Generates Figure 6: a two-panel plot for the curated Palaeoproterozoic
mafic magmatism dataset (1900–2500 Ma).

  Panel A (top):  Histogram + KDE of crystallisation ages, overlaid with
                  the igneous zircon age-frequency KDE from Puetz & Condie (2019).

  Panel B (bottom): Stacked proportions of normative basalt types in 25 Ma bins.

Input
-----
Supplementary Data 1 (Figshare: https://doi.org/10.6084/m9.figshare.30386002)
  Sheet: Palaeoproterozoic - Curated

  Required columns: Confidence, Crystallisation_age_Ma, Normative_Name

Igneous zircon overlay (Puetz & Condie 2019 — obtain from the original publication):
  Required column: Best Age (Ma)

Notes
-----
  - Only samples with Confidence = "high" are retained.
  - Ages are filtered to 1900–2500 Ma.

References
----------
  Puetz, S. J. & Condie, K. C. (2019). Time series analysis of mantle cycles
  Part I: Periodicities and correlations among seven global isotopic databases.
  Geoscience Frontiers, 10, 1305–1326.
  https://doi.org/10.1016/j.gsf.2019.04.002

Citation
--------
  Roy, S., Kamber, B. S., Hayman, P. C. & Murphy, D. T. (2026).
  Tectonic setting and mantle source evolution reconstructed from deep time
  analysis of basalt geochemistry. Communications Earth & Environment.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

# ---------------------------------------------------------------------------
# USER CONFIGURATION — update these paths before running
# ---------------------------------------------------------------------------
INPUT_FILE          = Path(r"C:\path\to\Supplementary Data 1.xlsx")
IGNEOUS_ZIRCON_FILE = Path(r"C:\path\to\Puetz and Condie 2019.xlsx")
OUTPUT_DIR          = Path(r"C:\path\to\output\figure6")

SHEET_NAME            = "Palaeoproterozoic - Curated"
IGNEOUS_ZIRCON_COLUMN = "Best Age (Ma)"

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
BIN_WIDTH = 25          # Ma
AGE_MIN   = 1900        # Ma
AGE_MAX   = 2500        # Ma

_TARGET_NORMS = ["nepheline_normative", "olivine_normative", "quartz_normative"]

_COLORS = {
    "quartz_normative":    "#d7191c",
    "nepheline_normative": "#2c7fb8",
    "olivine_normative":   "#1a9850",
    "other":               "#bdbdbd",
}

# Vertical lines and shading for known magmatic lulls
_VERTICAL_LINES    = [2266, 2214]
_SHADED_INTERVAL   = (2235, 2365)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _clean_age(series: pd.Series, lo: float, hi: float) -> np.ndarray:
    """Coerce to numeric and retain only values within [lo, hi]."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    return s[(s >= lo) & (s <= hi)].to_numpy()


def _gaussian_kde(ages: np.ndarray, xgrid: np.ndarray,
                  bw_scale: float | None = None) -> np.ndarray | None:
    """Compute Gaussian KDE; returns None if fewer than 5 finite values."""
    ages = ages[np.isfinite(ages)]
    if ages.size < 5:
        return None
    kde = gaussian_kde(ages)
    if bw_scale is not None:
        kde.set_bandwidth(kde.factor * bw_scale)
    return kde(xgrid)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.is_file():
        raise FileNotFoundError(f"Input file not found:\n  {INPUT_FILE}")
    if not IGNEOUS_ZIRCON_FILE.is_file():
        raise FileNotFoundError(f"Igneous zircon file not found:\n  {IGNEOUS_ZIRCON_FILE}")

    # ------------------------------------------------------------------
    # Load primary dataset
    # ------------------------------------------------------------------
    print(f"Reading: {INPUT_FILE.name}  (sheet='{SHEET_NAME}')")
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
    print(f"  {len(df):,} rows loaded")

    required = ["Confidence", "Crystallisation_age_Ma", "Normative_Name"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    df["Confidence"] = df["Confidence"].astype(str).str.strip().str.lower()
    df = df[df["Confidence"] == "high"].copy()

    df["Crystallisation_age_Ma"] = pd.to_numeric(df["Crystallisation_age_Ma"], errors="coerce")
    df = df.dropna(subset=["Crystallisation_age_Ma"])
    df = df[(df["Crystallisation_age_Ma"] >= AGE_MIN) & (df["Crystallisation_age_Ma"] <= AGE_MAX)]

    df["Normative_Name"] = df["Normative_Name"].astype(str).str.strip().str.lower()
    df["normative_group"] = np.where(
        df["Normative_Name"].isin(_TARGET_NORMS), df["Normative_Name"], "other"
    )

    if df.empty:
        raise ValueError("No data remain after filtering. Check Confidence and age columns.")

    print(f"  {len(df):,} rows retained (Confidence=high, {AGE_MIN}–{AGE_MAX} Ma)")
    ages = df["Crystallisation_age_Ma"].to_numpy()

    # ------------------------------------------------------------------
    # Bin setup
    # ------------------------------------------------------------------
    bin_edges   = np.arange(AGE_MIN, AGE_MAX + BIN_WIDTH, BIN_WIDTH)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    df["age_bin"] = pd.cut(df["Crystallisation_age_Ma"], bins=bin_edges,
                           right=False, include_lowest=True)

    counts = (
        df.groupby(["age_bin", "normative_group"], observed=False)
        .size()
        .unstack(fill_value=0)
    )
    stack_order = [n for n in _TARGET_NORMS if n in counts.columns]
    if "other" in counts.columns:
        stack_order.append("other")
    counts = counts.reindex(columns=stack_order, fill_value=0)

    all_bins   = pd.CategoricalIndex(pd.IntervalIndex.from_breaks(bin_edges, closed="left"), ordered=True)
    counts     = counts.reindex(all_bins, fill_value=0)
    row_sums   = counts.sum(axis=1).astype(float)
    proportions = counts.div(row_sums.replace(0, np.nan), axis=0).fillna(0.0)

    # ------------------------------------------------------------------
    # Overlay KDEs
    # ------------------------------------------------------------------
    xgrid = np.linspace(AGE_MIN, AGE_MAX, 3000)

    # Igneous zircon KDE (Puetz & Condie 2019)
    overlay_x = overlay_y = None
    try:
        ig_df  = pd.read_excel(IGNEOUS_ZIRCON_FILE, engine="openpyxl")
        ig_ages = _clean_age(ig_df[IGNEOUS_ZIRCON_COLUMN], AGE_MIN, AGE_MAX)
        kde_y   = _gaussian_kde(ig_ages, xgrid, bw_scale=0.35)
        if kde_y is not None:
            overlay_x, overlay_y = xgrid, kde_y
    except Exception as exc:
        print(f"  [Warning] Could not compute igneous zircon KDE: {exc}")

    # Primary dataset KDE
    overlay2_x = overlay2_y = None
    xgrid2 = np.linspace(AGE_MIN, AGE_MAX, 1024)
    kde2_y = _gaussian_kde(_clean_age(df["Crystallisation_age_Ma"], AGE_MIN, AGE_MAX), xgrid2)
    if kde2_y is not None:
        overlay2_x, overlay2_y = xgrid2, kde2_y

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------
    plt.rcParams.update({
        "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
        "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
        "figure.dpi": 100, "axes.linewidth": 0.8,
    })

    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1,
        figsize=(89 / 25.4, 120 / 25.4),
        sharex=True,
        gridspec_kw={"height_ratios": [1, 1.2]},
    )

    # Top panel
    ax_top.hist(ages, bins=bin_edges, density=True, edgecolor="black", alpha=0.6)

    if overlay_x is not None:
        ax_top.plot(overlay_x, overlay_y, linewidth=1.8, color="darkorange",
                    alpha=0.9, label="Igneous zircon KDE (Puetz & Condie 2019)")
        ax_top.fill_between(overlay_x, overlay_y, alpha=0.2, color="darkorange")

    if overlay2_x is not None:
        ax_top.plot(overlay2_x, overlay2_y, linewidth=1.2, color="purple",
                    alpha=0.9, label="Palaeoproterozoic dataset KDE")

    for xv in _VERTICAL_LINES:
        ax_top.axvline(x=xv, color="red", linewidth=1)
    ax_top.axvspan(*_SHADED_INTERVAL, color="green", alpha=0.15, linewidth=0)

    ax_top.set_xlim(AGE_MIN, AGE_MAX)
    ax_top.set_ylabel("Frequency density")
    ax_top.legend(fontsize=7, frameon=False)
    ax_top.grid(alpha=0.3, linestyle="--", linewidth=0.5)

    # Bottom panel
    bottom = np.zeros(len(proportions), dtype=float)
    for cat in stack_order:
        vals = proportions[cat].to_numpy()
        ax_bot.bar(
            bin_centers, vals, width=BIN_WIDTH * 0.9, bottom=bottom,
            edgecolor="black", color=_COLORS.get(cat, "#bdbdbd"),
            align="center", linewidth=0.6,
        )
        bottom += vals

    for xv in _VERTICAL_LINES:
        ax_bot.axvline(x=xv, color="red", linewidth=1)
    ax_bot.axvspan(*_SHADED_INTERVAL, color="green", alpha=0.15, linewidth=0)

    for i in range(len(proportions)):
        y0 = 0.0
        for cat in stack_order:
            p = proportions.iloc[i][cat]
            if p >= 0.08:
                ax_bot.text(bin_centers[i], y0 + p / 2.0, f"{p * 100:.0f}%",
                            ha="center", va="center", fontsize=7)
            y0 += p
        n_val = int(row_sums.iloc[i])
        if n_val > 0:
            ax_bot.text(bin_centers[i], 1.02, f"n={n_val}",
                        ha="center", va="bottom", fontsize=5, fontweight="bold")

    ax_bot.set_ylim(0, 1.1)
    ax_bot.set_xlim(AGE_MIN, AGE_MAX)
    ax_bot.set_ylabel("Proportion")
    ax_bot.set_xlabel("Crystallisation age (Ma)")
    ax_bot.grid(alpha=0.3, linestyle="--", linewidth=0.5)

    step = max(1, len(bin_centers) // 9)
    ax_bot.set_xticks(bin_centers[::step])
    ax_bot.set_xticklabels([f"{int(v)}" for v in bin_centers[::step]])

    out_path = OUTPUT_DIR / "figure6_palaeoproterozoic_magmatism.pdf"
    plt.tight_layout(pad=0.6)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
