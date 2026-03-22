"""
figure7a.py — Roy et al. (2026), Communications Earth & Environment

Plots experimental melt compositions from Mallik & Dasgupta (2012) on the
unfolded basalt tetrahedron (Thompson 1984) for Figure 7a.

Points are coloured by the proportion of eclogite-derived melt added (wt.%)
and labelled with run numbers.  Only rows where Comment == "Mix Run" are plotted.

Input
-----
Supplementary Data 2 (Figshare: https://doi.org/10.6084/m9.figshare.30386002)
  Sheet: Mallik and Dasgupta 2012

Required columns
----------------
  Comment, normative_name, Run no./Name, Melt added (wt.%)
  Nepheline_%wt, Olivine_%wt, Diopside_%wt, Hypersthene_%wt, Quartz_%wt

References
----------
  Mallik, A. & Dasgupta, R. (2012). Reaction between MORB-eclogite derived
  melts and fertile peridotite and generation of ocean island basalts.
  Earth and Planetary Science Letters, 329–330, 97–108.
  https://doi.org/10.1016/j.epsl.2012.02.007

  Thompson, R. N. (1984). Dispatches from the basalt front.
  Proceedings of the Geologists' Association, 95(3), 249–262.
  http://dx.doi.org/10.1016/S0016-7878(84)80011-5

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
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# USER CONFIGURATION — update these two paths before running
# ---------------------------------------------------------------------------
INPUT_FILE = Path(r"C:\path\to\Supplementary Data 2.xlsx")
OUTPUT_DIR = Path(r"C:\path\to\output\figure7a")

SHEET_NAME = "Mallik and Dasgupta 2012"

# Ternary apices in Cartesian space (unfolded tetrahedron geometry)
_H  = np.sqrt(3) / 2
_NE = (0.0, _H)
_OL = (0.5, 0.0)
_DI = (1.0, _H)
_HY = (1.5, 0.0)
_QZ = (2.0, _H)


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


def _row_normalise(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out      = df.copy()
    row_sums = out[cols].sum(axis=1)
    out      = out[row_sums > 0].copy()
    out[cols] = out[cols].div(row_sums[row_sums > 0], axis=0)
    return out.dropna(subset=cols)


def _ternary_to_cartesian(
    a: pd.Series, b: pd.Series, c: pd.Series,
    pa: tuple[float, float], pb: tuple[float, float], pc: tuple[float, float],
) -> tuple[pd.Series, pd.Series]:
    return (a * pa[0] + b * pb[0] + c * pc[0],
            a * pa[1] + b * pb[1] + c * pc[1])


def _draw_tetrahedron(ax: plt.Axes) -> None:
    for tri in [
        [_NE, _OL, _DI, _NE],
        [_OL, _DI, _HY, _OL],
        [_DI, _HY, _QZ, _DI],
    ]:
        xs, ys = zip(*tri)
        ax.plot(xs, ys, "k-", linewidth=1)
    for (x, y), label, dy in [
        (_NE, "Ne", 0.05), (_OL, "Ol", -0.05), (_DI, "Di", 0.05),
        (_HY, "Hy", -0.05), (_QZ, "Qz", 0.05),
    ]:
        ax.text(x, y + dy, label, fontsize=12, ha="center", fontweight="bold")


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

    # Resolve columns
    col_map = {
        "Comment":            ["Comment"],
        "normative_name":     ["normative_name", "Normative_Name", "normative name"],
        "Nepheline_%wt":      ["Nepheline_%wt", "Nepheline %wt"],
        "Olivine_%wt":        ["Olivine_%wt",   "Olivine %wt"],
        "Diopside_%wt":       ["Diopside_%wt",  "Diopside %wt"],
        "Hypersthene_%wt":    ["Hypersthene_%wt","Hypersthene %wt"],
        "Quartz_%wt":         ["Quartz_%wt",    "Quartz %wt"],
        "Melt added (wt.%)":  ["Melt added (wt.%)", "Melt_added", "Melt added"],
        "Run no./Name":       ["Run no./Name",  "Run No./Name", "Run no", "Run Name"],
    }
    resolved = {k: _resolve_column(df, v) for k, v in col_map.items()}
    missing  = [k for k, v in resolved.items() if v is None]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    # Rename to standard internal names
    df = df[[resolved[k] for k in col_map]].copy()
    df.columns = list(col_map.keys())

    numeric_cols = ["Nepheline_%wt", "Olivine_%wt", "Diopside_%wt",
                    "Hypersthene_%wt", "Quartz_%wt", "Melt added (wt.%)"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    # Filter to Mix Run experiments
    df = df[df["Comment"].astype(str).str.strip() == "Mix Run"].copy()
    df = df.dropna(subset=numeric_cols + ["normative_name", "Run no./Name"])

    if df.empty:
        raise ValueError("No rows remain after filtering Comment == 'Mix Run'.")
    print(f"  {len(df)} 'Mix Run' experiments to plot")

    # Split by normative field and compute ternary coordinates
    def _make_sub(norm: str, cols: list[str], apex1, apex2, apex3) -> pd.DataFrame:
        mask = df["normative_name"].str.strip().str.lower() == norm
        sub  = df[mask][["Run no./Name", "Comment", "Melt added (wt.)"] + cols
                        if "Melt added (wt.)" in df.columns
                        else ["Run no./Name", "Comment", "Melt added (wt.%)"] + cols].copy()
        sub  = _row_normalise(sub, cols)
        if not sub.empty:
            sub["x"], sub["y"] = _ternary_to_cartesian(
                sub[cols[0]], sub[cols[1]], sub[cols[2]], apex1, apex2, apex3
            )
        return sub

    df_left   = _make_sub("nepheline_normative",
                           ["Nepheline_%wt", "Olivine_%wt", "Diopside_%wt"],  _NE, _OL, _DI)
    df_middle = _make_sub("olivine_normative",
                           ["Olivine_%wt", "Diopside_%wt", "Hypersthene_%wt"], _OL, _DI, _HY)
    df_right  = _make_sub("quartz_normative",
                           ["Diopside_%wt", "Hypersthene_%wt", "Quartz_%wt"],  _DI, _HY, _QZ)

    df_all = pd.concat([df_left, df_middle, df_right], ignore_index=True)
    if df_all.empty:
        raise ValueError("No plottable data after processing normative groups.")

    # Marker shapes by Comment category
    shapes = ["o", "s", "*", "^", "D", "x", "P", "v", ">"]
    comment_to_shape = {
        comment: shapes[i % len(shapes)]
        for i, comment in enumerate(df_all["Comment"].value_counts().index)
    }

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    cmap = plt.cm.viridis
    melt_col = "Melt added (wt.%)"
    norm_plt = plt.Normalize(df_all[melt_col].min(), df_all[melt_col].max())

    for _, row in df_all.iterrows():
        marker = comment_to_shape.get(row["Comment"], "o")
        ax.scatter(row["x"], row["y"],
                   color=cmap(norm_plt(row[melt_col])),
                   marker=marker, s=80 if marker != "*" else 60,
                   edgecolor="k", linewidth=0.8, alpha=0.9)
        ax.text(row["x"] + 0.015, row["y"] + 0.015,
                str(row["Run no./Name"]), fontsize=7, ha="left", va="bottom")

    _draw_tetrahedron(ax)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm_plt)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, pad=0.02).set_label("Melt added (wt.%)", fontsize=10)

    legend_elements = [
        Line2D([0], [0], marker=shape, color="w", label=str(label),
               markerfacecolor="gray", markeredgecolor="k", markersize=7)
        for label, shape in comment_to_shape.items()
    ]
    ax.legend(handles=legend_elements, loc="upper center", bbox_to_anchor=(0.5, -0.15),
              ncol=3, frameon=False, fontsize=9, title="Comment")

    ax.set_xticks([]); ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_xlim(-0.1, 2.1); ax.set_ylim(-0.1, _H + 0.1)
    ax.set_title("Figure 7a — Mallik & Dasgupta (2012)", fontsize=14)

    out_path = OUTPUT_DIR / "figure7a_mallik_dasgupta_2012.pdf"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
