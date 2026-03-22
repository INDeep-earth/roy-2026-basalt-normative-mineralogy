"""
figure8.py — Roy et al. (2026), Communications Earth & Environment

Generates Figure 8: a 5 × 3 kernel-density panel showing the distributions
of LOI (wt%), CIA, and Mg# for nepheline-, olivine-, and quartz-normative
basalts across five geological age groups.

Input
-----
Supplementary Data 1 (Figshare: https://doi.org/10.6084/m9.figshare.30386002)
  Sheet: Gard et al., 2019 Filtered

Required columns
----------------
  loi, cia, mg_number, normative_name, geol_age

Expected geol_age values
------------------------
  archaean, palaeoproterozoic, mesoproterozoic, neoproterozoic, phanerozoic

Expected normative_name values
------------------------------
  nepheline_normative, olivine_normative, quartz_normative

References
----------
  Gard, M., Hasterok, D. & Halpin, J. A. (2019). Global whole-rock geochemical
  database compilation. Earth Syst. Sci. Data, 11, 1553–1566.
  https://doi.org/10.5194/essd-11-1553-2019

Citation
--------
  Roy, S., Kamber, B. S., Hayman, P. C. & Murphy, D. T. (2026).
  Tectonic setting and mantle source evolution reconstructed from deep time
  analysis of basalt geochemistry. Communications Earth & Environment.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# USER CONFIGURATION — update these two paths before running
# ---------------------------------------------------------------------------
INPUT_FILE = Path(r"C:\path\to\Supplementary Data 1.xlsx")
OUTPUT_DIR = Path(r"C:\path\to\output\figure8")

SHEET_NAME = "Gard et al., 2019 Filtered"

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
_ERA_ORDER = [
    "archaean",
    "palaeoproterozoic",
    "mesoproterozoic",
    "neoproterozoic",
    "phanerozoic",
]

_ERA_LABELS = [
    "a. Archaean",
    "b. Palaeoproterozoic",
    "c. Mesoproterozoic",
    "d. Neoproterozoic",
    "e. Phanerozoic",
]

_PARAMETERS = [
    ("loi",       "LOI (wt%)"),
    ("cia",       "CIA"),
    ("mg_number", "Mg#"),
]

_COLOR_MAP = {
    "nepheline_normative": "blue",
    "olivine_normative":   "green",
    "quartz_normative":    "red",
}

# Canonical label map
_ERA_MAP = dict(zip(_ERA_ORDER, _ERA_LABELS))


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _norm_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def _resolve_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    norm_map  = {_norm_key(c): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    for cand in candidates:
        if _norm_key(cand) in norm_map:
            return norm_map[_norm_key(cand)]
    return None


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.is_file():
        raise FileNotFoundError(f"Input file not found:\n  {INPUT_FILE}")

    print(f"Reading: {INPUT_FILE.name}  (sheet='{SHEET_NAME}')")
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, engine="openpyxl")
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )
    print(f"  {len(df):,} rows, {len(df.columns)} columns")

    col_map = {
        "loi":           ["loi", "LOI", "LOI (wt%)"],
        "cia":           ["cia", "CIA"],
        "mg_number":     ["mg_number", "Mg_number", "Mg#", "mg#"],
        "normative_name":["normative_name", "Normative_Name", "normative name"],
        "geol_age":      ["geol_age", "Geol_Age", "geological age", "Geological Age"],
    }
    resolved = {k: _resolve_column(df, v) for k, v in col_map.items()}
    missing  = [k for k, v in resolved.items() if v is None]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    df = df[[resolved[k] for k in col_map]].copy()
    df.columns = list(col_map.keys())

    df["normative_name"] = df["normative_name"].astype(str).str.strip().str.lower()
    df["geol_age"]       = df["geol_age"].astype(str).str.strip().str.lower()

    numeric_cols = ["loi", "cia", "mg_number"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=numeric_cols + ["normative_name", "geol_age"])
    df = df[df["geol_age"].isin(_ERA_ORDER)].copy()
    df = df[df["normative_name"].isin(_COLOR_MAP.keys())].copy()

    if df.empty:
        raise ValueError("No valid data remain after filtering.")

    df["era"] = df["geol_age"].map(_ERA_MAP)

    # Plot
    plt.rcParams.update({
        "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 11,
        "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.linewidth": 0.8,
    })

    fig, axes = plt.subplots(5, 3, figsize=(18, 16), sharex="col")

    for i, era_label in enumerate(_ERA_LABELS):
        subset = df[df["era"] == era_label].copy()

        for j, (param, xlabel) in enumerate(_PARAMETERS):
            ax = axes[i, j]
            if subset.empty:
                ax.set_visible(False)
                continue

            for norm_type in ["nepheline_normative", "olivine_normative", "quartz_normative"]:
                data = subset[subset["normative_name"] == norm_type][param].dropna()
                if len(data) < 2:
                    continue
                color = _COLOR_MAP[norm_type]
                sns.kdeplot(data=data, ax=ax, fill=True, alpha=0.4,
                            label=norm_type, color=color, linewidth=1.2)
                median_val = data.median()
                ax.axvline(median_val, color=color, linestyle="--", linewidth=1)
                ymax = ax.get_ylim()[1]
                ax.text(median_val, ymax * 0.9, f"{median_val:.2f}",
                        color=color, ha="center", va="top", fontsize=9, rotation=90)

            ax.set_title(f"({era_label}) {xlabel}", loc="left", fontsize=12)
            ax.set_ylabel("Density" if j == 0 else "")
            ax.set_xlabel(xlabel if i == 4 else "")
            ax.grid(alpha=0.25, linestyle="--", linewidth=0.5)

    # Legend on top-right panel
    handles, labels = axes[0, 2].get_legend_handles_labels()
    if handles:
        axes[0, 2].legend(handles, labels, title="Normative type",
                          loc="upper right", fontsize=10, frameon=False)

    out_path = OUTPUT_DIR / "figure8_loi_cia_mgnumber_kde.pdf"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
