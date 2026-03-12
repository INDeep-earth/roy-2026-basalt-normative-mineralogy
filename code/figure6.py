"""
Figure 6 plotting script for Roy et al. (2026)

Purpose
-------
Generates the two-panel Figure 6 plot showing:

1. Histogram + KDE comparison of curated Palaeoproterozoic mafic magmatism
   against igneous zircon age frequencies.
2. Stacked proportions of normative basalt types through time in 25 Ma bins.

Input
-----
Primary dataset:
    Supplementary File 1
    Sheet: Palaeoproterozoic - Curated

Overlay dataset:
    Puetz and Condie (2019) igneous zircon age compilation

    Citation: Puetz, S. J. & Condie, K. C. Time series analysis of mantle cycles Part I: Periodicities and correlations among seven global isotopic databases. Geoscience Frontiers 10, 1305-1326 (2019). https://doi.org/10.1016/j.gsf.2019.04.002

Expected columns in primary dataset
-----------------------------------
Required:
- Confidence
- Crystallisation_age_Ma
- Normative_Name

Expected columns in zircon overlay dataset
------------------------------------------
Required:
- Best Age (Ma)

Output
------
Displays the figure and saves a PDF to the output directory.

Notes
-----
- Only samples with Confidence = "high" are retained.
- Ages are filtered to 1900–2500 Ma.
- Normative groups are reduced to:
      nepheline_normative
      olivine_normative
      quartz_normative
  with any remaining categories grouped as "other".
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# ---------------------------------------------------------------------
# USER INPUTS
# ---------------------------------------------------------------------
INPUT_FILE = Path(r"C:\add\your\path\Supplementary File 1.xlsx")
SHEET_NAME = "Palaeoproterozoic - Curated"

IGNEOUS_ZIRCON_FILE = Path(r"C:\add\your\path\Puetz and Condie 2019.xlsx")
IGNEOUS_ZIRCON_COLUMN = "Best Age (Ma)"

OUTPUT_DIR = Path(r"C:\add\your\output-path\test")
OUTPUT_FILE = OUTPUT_DIR / "figure6_palaeoproterozoic_magmatism.pdf"


# ---------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------
BIN_WIDTH = 25
AGE_MIN = 1900
AGE_MAX = 2500

TARGET_NORMS = [
    "nepheline_normative",
    "olivine_normative",
    "quartz_normative",
]

COLORS = {
    "quartz_normative": "#d7191c",
    "nepheline_normative": "#2c7fb8",
    "olivine_normative": "#1a9850",
    "other": "#bdbdbd",
}

VERTICAL_LINES = [2266, 2214]
SHADED_INTERVAL = (2235, 2365)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def read_excel_safely(path: Path, sheet: str) -> pd.DataFrame:
    """Read an Excel sheet safely with helpful error messages."""
    try:
        xl = pd.ExcelFile(path, engine="openpyxl")
        if sheet not in xl.sheet_names:
            raise KeyError(
                f"Sheet '{sheet}' not found. Available sheets: {', '.join(xl.sheet_names)}"
            )
        df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
        print(
            f"Loaded: {path.name} | sheet='{sheet}' | rows={len(df):,}, cols={len(df.columns)}"
        )
        return df
    except Exception as exc:
        raise RuntimeError(f"Failed to read Excel file '{path}' sheet '{sheet}': {exc}") from exc


def clean_numeric_age(series: pd.Series, lo: float = AGE_MIN, hi: float = AGE_MAX) -> np.ndarray:
    """Convert a series to numeric age values and retain only ages within bounds."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    s = s[(s >= lo) & (s <= hi)]
    return s.to_numpy()


def compute_kde(
    ages: np.ndarray,
    xgrid: np.ndarray,
    bandwidth_scale: float | None = None,
) -> np.ndarray | None:
    """Compute Gaussian KDE for a 1D age array."""
    ages = ages[np.isfinite(ages)]
    if ages.size < 5:
        return None

    kde = gaussian_kde(ages)
    if bandwidth_scale is not None:
        kde.set_bandwidth(kde.factor * bandwidth_scale)

    return kde(xgrid)


# ---------------------------------------------------------------------
# WORKFLOW
# ---------------------------------------------------------------------
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.is_file():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    if not IGNEOUS_ZIRCON_FILE.is_file():
        raise FileNotFoundError(f"Igneous zircon file not found: {IGNEOUS_ZIRCON_FILE}")

    # -----------------------------------------------------------------
    # Read primary dataset
    # -----------------------------------------------------------------
    df = read_excel_safely(INPUT_FILE, SHEET_NAME)

    required_cols = ["Confidence", "Crystallisation_age_Ma", "Normative_Name"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required column(s) in primary dataset: {missing}")

    df["Confidence"] = df["Confidence"].astype(str).str.strip().str.lower()
    df = df[df["Confidence"] == "high"].copy()

    df["Crystallisation_age_Ma"] = pd.to_numeric(df["Crystallisation_age_Ma"], errors="coerce")
    df = df.dropna(subset=["Crystallisation_age_Ma"])
    df = df[
        (df["Crystallisation_age_Ma"] >= AGE_MIN)
        & (df["Crystallisation_age_Ma"] <= AGE_MAX)
    ].copy()

    df["Normative_Name"] = df["Normative_Name"].astype(str).str.strip().str.lower()
    df["normative_group"] = np.where(
        df["Normative_Name"].isin(TARGET_NORMS),
        df["Normative_Name"],
        "other",
    )

    if df.empty:
        raise ValueError("No data remain after filtering the primary dataset.")

    ages = df["Crystallisation_age_Ma"].to_numpy()

    # -----------------------------------------------------------------
    # Bin setup
    # -----------------------------------------------------------------
    bin_edges = np.arange(AGE_MIN, AGE_MAX + BIN_WIDTH, BIN_WIDTH)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    df["age_bin"] = pd.cut(
        df["Crystallisation_age_Ma"],
        bins=bin_edges,
        right=False,
        include_lowest=True,
    )

    counts = df.groupby(["age_bin", "normative_group"], observed=False).size().unstack(fill_value=0)

    stack_order = [cat for cat in TARGET_NORMS if cat in counts.columns]
    if "other" in counts.columns:
        stack_order.append("other")

    counts = counts.reindex(columns=stack_order, fill_value=0)

    all_bins = pd.Categorical(pd.IntervalIndex.from_breaks(bin_edges, closed="left"), ordered=True)
    counts = counts.reindex(all_bins, fill_value=0)

    row_sums = counts.sum(axis=1).astype(float)
    proportions = counts.div(row_sums.replace(0, np.nan), axis=0).fillna(0.0)

    # -----------------------------------------------------------------
    # Overlay KDE: igneous zircon ages
    # -----------------------------------------------------------------
    overlay_x = overlay_y = None
    try:
        ig_df = pd.read_excel(IGNEOUS_ZIRCON_FILE, engine="openpyxl")
        if IGNEOUS_ZIRCON_COLUMN not in ig_df.columns:
            raise KeyError(
                f"Column '{IGNEOUS_ZIRCON_COLUMN}' not found in {IGNEOUS_ZIRCON_FILE.name}"
            )

        ig_ages = clean_numeric_age(ig_df[IGNEOUS_ZIRCON_COLUMN], lo=AGE_MIN, hi=AGE_MAX)
        xgrid = np.linspace(AGE_MIN, AGE_MAX, 3000)
        kde_y = compute_kde(ig_ages, xgrid, bandwidth_scale=0.35)

        if kde_y is not None:
            overlay_x, overlay_y = xgrid, kde_y
    except Exception as exc:
        print(f"[Overlay warning] {exc}")

    # -----------------------------------------------------------------
    # Second overlay KDE: same primary dataset ages
    # -----------------------------------------------------------------
    overlay2_x = overlay2_y = None
    try:
        arr2 = clean_numeric_age(df["Crystallisation_age_Ma"], lo=AGE_MIN, hi=AGE_MAX)
        xgrid2 = np.linspace(AGE_MIN, AGE_MAX, 1024)
        kde2_y = compute_kde(arr2, xgrid2, bandwidth_scale=None)

        if kde2_y is not None:
            overlay2_x, overlay2_y = xgrid2, kde2_y
    except Exception as exc:
        print(f"[Second overlay warning] {exc}")

    # -----------------------------------------------------------------
    # Plot styling
    # -----------------------------------------------------------------
    plt.rcParams.update({
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "figure.dpi": 100,
        "axes.linewidth": 0.8,
    })

    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(89 / 25.4, 120 / 25.4),
        sharex=True,
        gridspec_kw={"height_ratios": [1, 1.2]},
    )

    # -----------------------------------------------------------------
    # Top panel: histogram + overlays
    # -----------------------------------------------------------------
    ax_top.hist(
        ages,
        bins=bin_edges,
        density=True,
        edgecolor="black",
        alpha=0.6,
    )

    if overlay_x is not None and overlay_y is not None:
        ax_top.plot(
            overlay_x,
            overlay_y,
            linewidth=1.8,
            color="darkorange",
            alpha=0.9,
            label="Igneous zircon KDE",
        )
        ax_top.fill_between(
            overlay_x,
            overlay_y,
            alpha=0.2,
            color="darkorange",
        )

    if overlay2_x is not None and overlay2_y is not None:
        ax_top.plot(
            overlay2_x,
            overlay2_y,
            linewidth=1.2,
            color="purple",
            alpha=0.9,
            label="Palaeoproterozoic dataset KDE",
        )

    for xline in VERTICAL_LINES:
        ax_top.axvline(x=xline, color="red", linewidth=1)

    ax_top.axvspan(
        SHADED_INTERVAL[0],
        SHADED_INTERVAL[1],
        color="green",
        alpha=0.15,
        linewidth=0,
    )

    ax_top.set_xlim(AGE_MIN, AGE_MAX)
    ax_top.set_ylabel("Frequency density")
    ax_top.grid(alpha=0.3, linestyle="--", linewidth=0.5)

    # -----------------------------------------------------------------
    # Bottom panel: stacked proportions
    # -----------------------------------------------------------------
    x = bin_centers
    bottom = np.zeros(len(proportions), dtype=float)

    for cat in stack_order:
        vals = proportions[cat].to_numpy()
        ax_bot.bar(
            x,
            vals,
            width=BIN_WIDTH * 0.9,
            bottom=bottom,
            edgecolor="black",
            color=COLORS.get(cat, "#bdbdbd"),
            align="center",
            linewidth=0.6,
        )
        bottom += vals

    for xline in VERTICAL_LINES:
        ax_bot.axvline(x=xline, color="red", linewidth=1)

    ax_bot.axvspan(
        SHADED_INTERVAL[0],
        SHADED_INTERVAL[1],
        color="green",
        alpha=0.15,
        linewidth=0,
    )

    for i in range(len(proportions)):
        y0 = 0.0
        for cat in stack_order:
            p = proportions.iloc[i][cat]
            if p >= 0.08:
                ax_bot.text(
                    x[i],
                    y0 + p / 2.0,
                    f"{p * 100:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=7,
                )
            y0 += p

        n_val = int(row_sums.iloc[i]) if row_sums.iloc[i] > 0 else 0
        if n_val > 0:
            ax_bot.text(
                x[i],
                1.02,
                f"n={n_val}",
                ha="center",
                va="bottom",
                fontsize=5,
                fontweight="bold",
            )

    ax_bot.set_ylim(0, 1.1)
    ax_bot.set_xlim(AGE_MIN, AGE_MAX)
    ax_bot.set_ylabel("Proportion")
    ax_bot.set_xlabel("Crystallisation age (Ma)")
    ax_bot.grid(alpha=0.3, linestyle="--", linewidth=0.5)

    xticks_step = max(1, len(bin_centers) // 9)
    ax_bot.set_xticks(bin_centers[::xticks_step])
    ax_bot.set_xticklabels([f"{int(v)}" for v in bin_centers[::xticks_step]])

    plt.tight_layout(pad=0.6)
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
    plt.show()

    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
