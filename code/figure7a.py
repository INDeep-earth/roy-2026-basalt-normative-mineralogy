"""
Figure 7a plotting script for Roy et al. (2026)

Purpose
-------
Plots experimental melt compositions from Mallik and Dasgupta (2012) on the
unfolded basalt tetrahedron for Figure 7a.

Mallik and Dasgupta (2012)
Citation: Mallik, A. & Dasgupta, R. Reaction between MORB-eclogite derived melts and fertile peridotite and generation of ocean island basalts. Earth and Planetary Science Letters 329-330, 97-108 (2012). https://doi.org/10.1016/j.epsl.2012.02.007

Input
-----
Supplementary File 2
Sheet: Mallik and Dasgupta 2012

Expected columns
----------------
Required:
- Comment
- normative_name
- Nepheline_%wt
- Olivine_%wt
- Diopside_%wt
- Hypersthene_%wt
- Quartz_%wt
- Melt added (wt.%)
- Run no./Name

Filtering
---------
Only rows with:
    Comment == "Mix Run"
are plotted.

Output
------
Displays the figure and saves a PDF to the output directory.

Notes
-----
- Points are coloured by Melt added (wt.%).
- Run numbers/names are labelled next to each point.
- Data are projected into the Ne–Ol–Di, Ol–Di–Hy, and Di–Hy–Qz fields
  according to normative_name.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


# ---------------------------------------------------------------------
# USER INPUTS
# ---------------------------------------------------------------------
INPUT_FILE = Path(r"C:\add\your\path\Supplementary File 2.xlsx")
SHEET_NAME = "Mallik and Dasgupta 2012"

OUTPUT_DIR = Path(r"C:\add\your\output-path\test")
OUTPUT_FILE = OUTPUT_DIR / "figure7a_mallik_dasgupta_2012.pdf"


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


def row_normalise(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Normalise selected columns in each row to unit sum."""
    out = df.copy()
    row_sums = out[cols].sum(axis=1)
    out = out[row_sums > 0].copy()
    out[cols] = out[cols].div(row_sums[row_sums > 0], axis=0)
    return out.dropna(subset=cols)


def ternary_to_cartesian(
    a: pd.Series,
    b: pd.Series,
    c: pd.Series,
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    point_c: tuple[float, float],
) -> tuple[pd.Series, pd.Series]:
    """Convert ternary proportions to Cartesian coordinates."""
    x = a * point_a[0] + b * point_b[0] + c * point_c[0]
    y = a * point_a[1] + b * point_b[1] + c * point_c[1]
    return x, y


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
    col_comment = get_col(df, "Comment", ["Comment"])
    col_norm = get_col(df, "normative_name", ["normative_name", "Normative_Name", "normative name"])
    col_ne = get_col(df, "Nepheline_%wt", ["Nepheline_%wt", "Nepheline %wt"])
    col_ol = get_col(df, "Olivine_%wt", ["Olivine_%wt", "Olivine %wt"])
    col_di = get_col(df, "Diopside_%wt", ["Diopside_%wt", "Diopside %wt"])
    col_hy = get_col(df, "Hypersthene_%wt", ["Hypersthene_%wt", "Hypersthene %wt"])
    col_qz = get_col(df, "Quartz_%wt", ["Quartz_%wt", "Quartz %wt"])
    col_melt = get_col(
        df,
        "Melt added (wt.%)",
        ["Melt added (wt.%)", "Melt_added", "Melt added", "Melt Added (wt.%)"]
    )
    col_run = get_col(df, "Run no./Name", ["Run no./Name", "Run No./Name", "Run no", "Run Name"])

    required = {
        "Comment": col_comment,
        "normative_name": col_norm,
        "Nepheline_%wt": col_ne,
        "Olivine_%wt": col_ol,
        "Diopside_%wt": col_di,
        "Hypersthene_%wt": col_hy,
        "Quartz_%wt": col_qz,
        "Melt added (wt.%)": col_melt,
        "Run no./Name": col_run,
    }
    missing = [name for name, col in required.items() if col is None]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    # Filter to Mix Run
    df = df[df[col_comment].astype(str).str.strip() == "Mix Run"].copy()

    if df.empty:
        raise ValueError("No rows remain after filtering Comment == 'Mix Run'.")

    # Keep only required columns
    df = df[
        [
            col_comment,
            col_norm,
            col_ne,
            col_ol,
            col_di,
            col_hy,
            col_qz,
            col_melt,
            col_run,
        ]
    ].copy()

    # Rename to standard internal names
    df.columns = [
        "Comment",
        "normative_name",
        "Nepheline_%wt",
        "Olivine_%wt",
        "Diopside_%wt",
        "Hypersthene_%wt",
        "Quartz_%wt",
        "Melt_added",
        "Run no./Name",
    ]

    # Convert numerics
    numeric_cols = [
        "Nepheline_%wt",
        "Olivine_%wt",
        "Diopside_%wt",
        "Hypersthene_%wt",
        "Quartz_%wt",
        "Melt_added",
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=numeric_cols + ["normative_name", "Run no./Name"])

    # Split by normative field
    df_left = df[df["normative_name"].astype(str).str.strip().str.lower() == "nepheline_normative"][
        ["Comment", "Run no./Name", "Nepheline_%wt", "Olivine_%wt", "Diopside_%wt", "Melt_added"]
    ].copy()

    df_middle = df[df["normative_name"].astype(str).str.strip().str.lower() == "olivine_normative"][
        ["Comment", "Run no./Name", "Olivine_%wt", "Diopside_%wt", "Hypersthene_%wt", "Melt_added"]
    ].copy()

    df_right = df[df["normative_name"].astype(str).str.strip().str.lower() == "quartz_normative"][
        ["Comment", "Run no./Name", "Diopside_%wt", "Hypersthene_%wt", "Quartz_%wt", "Melt_added"]
    ].copy()

    # Normalise ternary coordinates
    df_left = row_normalise(df_left, ["Nepheline_%wt", "Olivine_%wt", "Diopside_%wt"])
    df_middle = row_normalise(df_middle, ["Olivine_%wt", "Diopside_%wt", "Hypersthene_%wt"])
    df_right = row_normalise(df_right, ["Diopside_%wt", "Hypersthene_%wt", "Quartz_%wt"])

    # Geometry
    h = np.sqrt(3) / 2
    ne = (0.0, h)
    di = (1.0, h)
    qz = (2.0, h)
    ol = (0.5, 0.0)
    hy = (1.5, 0.0)

    # Convert to Cartesian coordinates
    if not df_left.empty:
        df_left["x"], df_left["y"] = ternary_to_cartesian(
            df_left["Nepheline_%wt"],
            df_left["Olivine_%wt"],
            df_left["Diopside_%wt"],
            ne,
            ol,
            di,
        )

    if not df_middle.empty:
        df_middle["x"], df_middle["y"] = ternary_to_cartesian(
            df_middle["Olivine_%wt"],
            df_middle["Diopside_%wt"],
            df_middle["Hypersthene_%wt"],
            ol,
            di,
            hy,
        )

    if not df_right.empty:
        df_right["x"], df_right["y"] = ternary_to_cartesian(
            df_right["Diopside_%wt"],
            df_right["Hypersthene_%wt"],
            df_right["Quartz_%wt"],
            di,
            hy,
            qz,
        )

    df_all = pd.concat([df_left, df_middle, df_right], ignore_index=True)

    if df_all.empty:
        raise ValueError("No plottable data remain after processing normative groups.")

    # Marker mapping by Comment
    comment_counts = df_all["Comment"].value_counts().sort_values(ascending=False)
    shapes = ["o", "s", "*", "^", "D", "x", "P", "v", ">"]
    comment_to_shape = {
        comment: shapes[i] if i < len(shapes) else "x"
        for i, comment in enumerate(comment_counts.index)
    }

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))

    cmap = plt.cm.viridis
    norm = plt.Normalize(df_all["Melt_added"].min(), df_all["Melt_added"].max())

    for _, row in df_all.iterrows():
        marker = comment_to_shape.get(row["Comment"], "x")
        size = 60 if marker == "*" else 80

        ax.scatter(
            row["x"],
            row["y"],
            color=cmap(norm(row["Melt_added"])),
            marker=marker,
            s=size,
            edgecolor="k",
            linewidth=0.8,
            alpha=0.9,
        )
        ax.text(
            row["x"] + 0.015,
            row["y"] + 0.015,
            str(row["Run no./Name"]),
            fontsize=7,
            ha="left",
            va="bottom",
        )

    # Triangle outlines
    ax.plot([ne[0], ol[0], di[0], ne[0]], [ne[1], ol[1], di[1], ne[1]], "k-", linewidth=1)
    ax.plot([ol[0], di[0], hy[0], ol[0]], [ol[1], di[1], hy[1], ol[1]], "k-", linewidth=1)
    ax.plot([di[0], hy[0], qz[0], di[0]], [di[1], hy[1], qz[1], di[1]], "k-", linewidth=1)

    # Apex labels
    ax.text(ne[0], ne[1] + 0.05, "Ne", fontsize=12, ha="center", fontweight="bold")
    ax.text(ol[0], ol[1] - 0.05, "Ol", fontsize=12, ha="center", fontweight="bold")
    ax.text(di[0], di[1] + 0.05, "Di", fontsize=12, ha="center", fontweight="bold")
    ax.text(hy[0], hy[1] - 0.05, "Hy", fontsize=12, ha="center", fontweight="bold")
    ax.text(qz[0], qz[1] + 0.05, "Qz", fontsize=12, ha="center", fontweight="bold")

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_xlim(-0.1, 2.1)
    ax.set_ylim(-0.1, h + 0.1)
    ax.set_title("Figure 7a - Mallik and Dasgupta 2012", fontsize=14)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.02)
    cbar.set_label("Melt added (wt.%)", fontsize=10)

    # Legend
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker=shape,
            color="w",
            label=str(label),
            markerfacecolor="gray",
            markeredgecolor="k",
            markersize=7,
        )
        for label, shape in comment_to_shape.items()
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
        frameon=False,
        fontsize=9,
        title="Comment",
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
    plt.show()

    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
