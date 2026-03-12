"""
Figure 8 plotting script for Roy et al. (2026)

Purpose
-------
Generates a 5 × 3 KDE panel figure showing the distributions of:

- LOI (wt%)
- CIA
- Mg#

for nepheline-, olivine-, and quartz-normative basalts across geological age
groups for Figure 8.

Input
-----
Supplementary File 1
Sheet: Gard et al., 2019 Filtered

Expected columns
----------------
Required:
- loi
- cia
- mg_number
- normative_name
- geol_age

Expected geol_age groups
------------------------
- archaean
- palaeoproterozoic
- mesoproterozoic
- neoproterozoic
- phanerozoic

Expected normative_name groups
------------------------------
- nepheline_normative
- olivine_normative
- quartz_normative

Output
------
Displays the figure and saves a PDF to the output directory.

Notes
-----
- KDEs are filled by normative type.
- Vertical dashed lines indicate medians for each normative type.
- Median values are annotated beside the dashed lines.

Gard et al., 2019
Citation: Gard, M., Hasterok, D. & Halpin, J. A. Global whole-rock geochemical database compilation. Earth Syst. Sci. Data 11, 1553-1566 (2019). https://doi.org/10.5194/essd-11-1553-2019
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# ---------------------------------------------------------------------
# USER INPUTS
# ---------------------------------------------------------------------
INPUT_FILE = Path(r"C:\add\your\path\Supplementary File 1.xlsx")
SHEET_NAME = "Gard et al., 2019 Filtered"

OUTPUT_DIR = Path(r"C:\add\your\output-path\test")
OUTPUT_FILE = OUTPUT_DIR / "figure8_loi_cia_mgnumber_kde.pdf"


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


def normalise_key(text: str) -> str:
    """Normalise a text string for robust column matching."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def get_col(df: pd.DataFrame, target: str, candidates: list[str] | None = None) -> str | None:
    """Return the best-matching column name from a list of candidates."""
    if candidates is None:
        candidates = [target]

    lower_map = {col.lower(): col for col in df.columns}
    norm_map = {normalise_key(col): col for col in df.columns}

    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]

    for cand in candidates:
        key = normalise_key(cand)
        if key in norm_map:
            return norm_map[key]

    return None


# ---------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------
ERA_ORDER = [
    "archaean",
    "palaeoproterozoic",
    "mesoproterozoic",
    "neoproterozoic",
    "phanerozoic",
]

ERA_LABELS = [
    "a. Archaean",
    "b. Palaeoproterozoic",
    "c. Mesoproterozoic",
    "d. Neoproterozoic",
    "e. Phanerozoic",
]

ERA_MAP = dict(zip(ERA_ORDER, ERA_LABELS))

PARAMETERS = [
    ("loi", "LOI (wt%)"),
    ("cia", "CIA"),
    ("mg_number", "Mg#"),
]

COLOR_MAP = {
    "nepheline_normative": "blue",
    "olivine_normative": "green",
    "quartz_normative": "red",
}


# ---------------------------------------------------------------------
# WORKFLOW
# ---------------------------------------------------------------------
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.is_file():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = read_excel_safely(INPUT_FILE, SHEET_NAME)

    # Clean column names
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    # Resolve required columns
    col_loi = get_col(df, "loi", ["loi", "LOI", "LOI (wt%)"])
    col_cia = get_col(df, "cia", ["cia", "CIA"])
    col_mg = get_col(df, "mg_number", ["mg_number", "Mg_number", "Mg#", "mg#"])
    col_norm = get_col(df, "normative_name", ["normative_name", "Normative_Name", "normative name"])
    col_age = get_col(df, "geol_age", ["geol_age", "Geol_Age", "geological age", "Geological Age"])

    required = {
        "loi": col_loi,
        "cia": col_cia,
        "mg_number": col_mg,
        "normative_name": col_norm,
        "geol_age": col_age,
    }
    missing = [name for name, col in required.items() if col is None]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    # Keep only required columns
    df = df[[col_loi, col_cia, col_mg, col_norm, col_age]].copy()
    df.columns = ["loi", "cia", "mg_number", "normative_name", "geol_age"]

    # Clean and standardise
    df["normative_name"] = df["normative_name"].astype(str).str.strip().str.lower()
    df["geol_age"] = df["geol_age"].astype(str).str.strip().str.lower()

    numeric_cols = ["loi", "cia", "mg_number"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=numeric_cols + ["normative_name", "geol_age"])

    df = df[df["geol_age"].isin(ERA_ORDER)].copy()
    df = df[df["normative_name"].isin(COLOR_MAP.keys())].copy()

    if df.empty:
        raise ValueError("No valid data remain after filtering age groups and normative types.")

    df["era"] = df["geol_age"].map(ERA_MAP)

    # Plot styling
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.linewidth": 0.8,
    })

    fig, axes = plt.subplots(5, 3, figsize=(18, 16), sharex="col")

    for i, era_label in enumerate(ERA_LABELS):
        subset = df[df["era"] == era_label].copy()

        if subset.empty:
            for j in range(3):
                axes[i, j].set_visible(False)
            continue

        for j, (param, xlabel) in enumerate(PARAMETERS):
            ax = axes[i, j]

            for name in ["nepheline_normative", "olivine_normative", "quartz_normative"]:
                group = subset[subset["normative_name"] == name]
                if group.empty:
                    continue

                data = group[param].dropna()
                if len(data) < 2:
                    continue

                color = COLOR_MAP.get(name, "gray")

                sns.kdeplot(
                    data=data,
                    ax=ax,
                    fill=True,
                    alpha=0.4,
                    label=name,
                    color=color,
                    linewidth=1.2,
                )

                median_val = data.median()
                ax.axvline(median_val, color=color, linestyle="--", linewidth=1)

                ymax = ax.get_ylim()[1]
                ax.text(
                    median_val,
                    ymax * 0.9,
                    f"{median_val:.2f}",
                    color=color,
                    ha="center",
                    va="top",
                    fontsize=9,
                    rotation=90,
                )

            ax.set_title(f"({era_label}) {xlabel}", loc="left", fontsize=12)
            ax.set_ylabel("Density" if j == 0 else "")

            if i == 4:
                ax.set_xlabel(xlabel, fontsize=12)
            else:
                ax.set_xlabel("")

            ax.grid(alpha=0.25, linestyle="--", linewidth=0.5)

    # Legend
    handles, labels = axes[0, 2].get_legend_handles_labels()
    if handles:
        axes[0, 2].legend(
            handles,
            labels,
            title="Normative Type",
            loc="upper right",
            fontsize=10,
            frameon=False,
        )

    plt.suptitle(
        "Distribution of LOI, CIA, and Mg# by Normative Type Across Geological Time",
        fontsize=16,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
    plt.show()

    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
