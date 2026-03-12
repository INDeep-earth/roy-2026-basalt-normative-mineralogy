"""
Figure 4 plotting script for Roy et al. (2026)

Purpose
-------
Generates unfolded basalt tetrahedron (Thompson 1984) plots for each tectonic setting from
Supplementary File 1, using the sheet:

    GEOROC - PhanZ Filtered

Input
-----
Excel workbook containing normative mineral proportions and tectonic setting
information.

Expected sheet
--------------
GEOROC - PhanZ Filtered

Expected columns
----------------
Required:
- TECTONIC SETTING
- Quartz_%wt
- Hypersthene_%wt
- Olivine_%wt
- Nepheline_%wt
- Diopside_%wt

Optional:
- Leucite_%wt
- Kaliophilite_%wt
- normative_name

Output
------
One PDF per tectonic setting, saved to the output directory.

Notes
-----
- If 'normative_name' is absent, it is estimated from normative mineral fields.
- Nepheline-combined field is calculated as:
      Nepheline + Leucite + Kaliophilite
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# ---------------------------------------------------------------------
# USER INPUTS
# ---------------------------------------------------------------------
INPUT_FILE = Path(r"C:\add\your\path\Supplementary File 1.xlsx")
SHEET_NAME = "GEOROC - PhanZ Filtered"
OUTPUT_DIR = Path(r"C:\add\your\path\Test")


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
    """Normalise column names for robust matching."""
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


def sanitize_filename(name: str) -> str:
    """Make a safe output filename."""
    name = re.sub(r'[\\/*?:"<>|]', "_", str(name))
    name = re.sub(r"\s+", "_", name.strip())
    return name[:150]


def ternary_to_cartesian(
    a: pd.Series,
    b: pd.Series,
    c: pd.Series,
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    point_c: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Convert ternary proportions to Cartesian coordinates."""
    x = a * point_a[0] + b * point_b[0] + c * point_c[0]
    y = a * point_a[1] + b * point_b[1] + c * point_c[1]
    return x.to_numpy(), y.to_numpy()


def row_normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise rows to unit sum."""
    if df.empty:
        return df
    row_sums = df.sum(axis=1)
    df = df[row_sums > 0]
    out = df.div(row_sums[row_sums > 0], axis=0)
    return out.dropna(how="any")


def classify_normative_type(row: pd.Series) -> str | pd.NA:
    """
    Estimate normative_name if not present.

    Logic follows the three basalt fields:
    - quartz_normative
    - olivine_normative
    - nepheline_normative
    """
    q = row["Quartz_%wt"]
    h = row["Hypersthene_%wt"]
    o = row["Olivine_%wt"]
    n = row["Nepheline_%wt"]

    if pd.notna(q) and q > 0 and pd.notna(h) and h > 0:
        return "quartz_normative"
    if pd.notna(o) and o > 0 and pd.notna(h) and h > 0:
        return "olivine_normative"
    if pd.notna(n) and n > 0 and pd.notna(o) and o > 0:
        return "nepheline_normative"

    return pd.NA


# ---------------------------------------------------------------------
# COLUMN RESOLUTION
# ---------------------------------------------------------------------
TARGETS = {
    "Quartz_%wt": [
        "Quartz_%wt", "Quartz %wt", "Quartz", "quartz", "Q"
    ],
    "Hypersthene_%wt": [
        "Hypersthene_%wt", "Hypersthene %wt", "Hypersthene", "hypersthene", "Hy", "hy"
    ],
    "Olivine_%wt": [
        "Olivine_%wt", "Olivine %wt", "Olivine", "olivine", "Ol", "ol"
    ],
    "Nepheline_%wt": [
        "Nepheline_%wt", "Nepheline %wt", "Nepheline", "nepheline", "Ne", "ne"
    ],
    "Diopside_%wt": [
        "Diopside_%wt", "Diopside %wt", "Diopside", "diopside", "Di", "di"
    ],
    "Leucite_%wt": [
        "Leucite_%wt", "Leucite %wt", "Leucite", "leucite", "Lc", "lc"
    ],
    "Kaliophilite_%wt": [
        "Kaliophilite_%wt", "Kaliophilite %wt", "Kaliophilite", "kaliophilite",
        "Kalsilite_%wt", "Kalsilite %wt", "Kalsilite", "kalsilite", "Kls", "kls"
    ],
}

MIN_COLS_NEEDED = {
    "ne_combo": "Ne_combo_%wt",
    "olivine": "Olivine_%wt",
    "diopside": "Diopside_%wt",
    "hypersthene": "Hypersthene_%wt",
    "quartz": "Quartz_%wt",
}


# ---------------------------------------------------------------------
# MAIN PLOTTING FUNCTION
# ---------------------------------------------------------------------
def plot_for_setting(
    df_in: pd.DataFrame,
    tectonic_setting_col: str,
    normative_col: str,
    setting_value: str,
    output_dir: Path,
) -> bool:
    """Generate one Figure 4 panel for a single tectonic setting."""
    sub = df_in[df_in[tectonic_setting_col].astype(str) == str(setting_value)].copy()

    if sub.empty:
        print(f"[skip] No data for: {setting_value}")
        return False

    needed = [normative_col] + list(MIN_COLS_NEEDED.values())
    for col in needed:
        if col not in sub.columns:
            print(f"[skip] {setting_value}: missing column '{col}'")
            return False

    numeric = sub[list(MIN_COLS_NEEDED.values())].apply(pd.to_numeric, errors="coerce")
    sub = pd.concat([sub[[normative_col]], numeric], axis=1)

    ne_combo = MIN_COLS_NEEDED["ne_combo"]
    olivine = MIN_COLS_NEEDED["olivine"]
    diopside = MIN_COLS_NEEDED["diopside"]
    hypersthene = MIN_COLS_NEEDED["hypersthene"]
    quartz = MIN_COLS_NEEDED["quartz"]

    left = sub[sub[normative_col] == "nepheline_normative"][[ne_combo, olivine, diopside]].dropna()
    middle = sub[sub[normative_col] == "olivine_normative"][[olivine, diopside, hypersthene]].dropna()
    right = sub[sub[normative_col] == "quartz_normative"][[diopside, hypersthene, quartz]].dropna()

    left_n = row_normalise(left)
    middle_n = row_normalise(middle)
    right_n = row_normalise(right)

    h = np.sqrt(3) / 2
    ne = (0.0, h)
    di = (1.0, h)
    qz = (2.0, h)
    ol = (0.5, 0.0)
    hy = (1.5, 0.0)

    def to_xy(df_three: pd.DataFrame, p1, p2, p3) -> tuple[np.ndarray, np.ndarray]:
        if df_three.empty:
            return np.array([]), np.array([])
        return ternary_to_cartesian(
            df_three.iloc[:, 0], df_three.iloc[:, 1], df_three.iloc[:, 2], p1, p2, p3
        )

    x_left, y_left = to_xy(left_n, ne, ol, di)
    x_mid, y_mid = to_xy(middle_n, ol, di, hy)
    x_right, y_right = to_xy(right_n, di, hy, qz)

    all_x = np.concatenate([x_left, x_mid, x_right]) if (x_left.size + x_mid.size + x_right.size) else np.array([])
    all_y = np.concatenate([y_left, y_mid, y_right]) if (y_left.size + x_mid.size + x_right.size) else np.array([])

    if all_x.size == 0:
        print(f"[skip] {setting_value}: no points to plot")
        return False

    fig, ax = plt.subplots(figsize=(10, 6))
    n_points = len(all_x)
    ax.text(1.98, h + 0.06, f"n={n_points}", fontsize=9, ha="right")

    if x_left.size:
        ax.scatter(
            x_left, y_left, s=12, alpha=0.7,
            facecolor="gray", edgecolor="black", linewidth=0.2,
            label="Ne (Ne+Lc+Kp) Normative"
        )
    if x_mid.size:
        ax.scatter(
            x_mid, y_mid, s=12, alpha=0.7,
            facecolor="gray", edgecolor="black", linewidth=0.2,
            label="Olivine Normative"
        )
    if x_right.size:
        ax.scatter(
            x_right, y_right, s=12, alpha=0.7,
            facecolor="gray", edgecolor="black", linewidth=0.2,
            label="Quartz Normative"
        )

    ax.plot([ne[0], ol[0], di[0], ne[0]], [ne[1], ol[1], di[1], ne[1]], "k-", lw=1)
    ax.plot([ol[0], di[0], hy[0], ol[0]], [ol[1], di[1], hy[1], ol[1]], "k-", lw=1)
    ax.plot([di[0], hy[0], qz[0], di[0]], [di[1], hy[1], qz[1], di[1]], "k-", lw=1)

    if all_x.size > 2:
        sns.kdeplot(
            x=all_x, y=all_y, cmap="RdYlBu_r", fill=True,
            ax=ax, alpha=0.45, thresh=0.1
        )
        sns.kdeplot(
            x=all_x, y=all_y, color="white",
            linewidths=0.4, ax=ax
        )

    ax.text(ne[0], ne[1] + 0.05, "Ne", fontsize=12, ha="center", fontweight="bold")
    ax.text(ol[0], ol[1] - 0.05, "Ol", fontsize=12, ha="center", fontweight="bold")
    ax.text(di[0], di[1] + 0.05, "Di", fontsize=12, ha="center", fontweight="bold")
    ax.text(hy[0], hy[1] - 0.05, "Hy", fontsize=12, ha="center", fontweight="bold")
    ax.text(qz[0], qz[1] + 0.05, "Qz", fontsize=12, ha="center", fontweight="bold")

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_xlim(-0.1, 2.1)
    ax.set_ylim(-0.1, h + 0.12)
    ax.set_title(setting_value, fontsize=13)

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc="upper left", fontsize=8, frameon=False)

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(setting_value)
    out_path = output_dir / f"{safe_name}.pdf"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved: {out_path}")
    return True


# ---------------------------------------------------------------------
# WORKFLOW
# ---------------------------------------------------------------------
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df_plot = read_excel_safely(INPUT_FILE, SHEET_NAME)

    # Clean column names
    df_plot.columns = (
        df_plot.columns.astype(str)
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    # Resolve expected columns
    resolved: dict[str, str | None] = {}
    for outcol, candidates in TARGETS.items():
        resolved[outcol] = get_col(df_plot, outcol, candidates)

    for outcol, src in resolved.items():
        if src is None:
            if outcol in ("Leucite_%wt", "Kaliophilite_%wt"):
                df_plot[outcol] = 0.0
                print(f"Note: '{outcol}' not found; assuming 0.0 for plotting.")
            else:
                raise KeyError(f"Missing required column '{outcol}' (tried {TARGETS[outcol]})")
        else:
            df_plot[outcol] = pd.to_numeric(df_plot[src], errors="coerce")

    # Combined nepheline field
    df_plot["Ne_combo_%wt"] = (
        df_plot["Nepheline_%wt"].fillna(0)
        + df_plot["Leucite_%wt"].fillna(0)
        + df_plot["Kaliophilite_%wt"].fillna(0)
    )

    tectonic_setting_col = get_col(
        df_plot,
        "TECTONIC SETTING",
        ["TECTONIC SETTING", "Tectonic Setting", "tectonic setting"]
    )
    if tectonic_setting_col is None:
        raise KeyError("Column 'TECTONIC SETTING' not found in the dataset.")

    normative_col = get_col(
        df_plot,
        "normative_name",
        ["normative_name", "Normative_Name", "normative name"]
    )

    if normative_col is None:
        df_plot["normative_name"] = df_plot.apply(classify_normative_type, axis=1).astype("string")
        normative_col = "normative_name"

    settings = df_plot[tectonic_setting_col].dropna().astype(str).unique()

    saved = 0
    for setting in sorted(settings):
        if plot_for_setting(
            df_in=df_plot,
            tectonic_setting_col=tectonic_setting_col,
            normative_col=normative_col,
            setting_value=setting,
            output_dir=OUTPUT_DIR,
        ):
            saved += 1

    print(f"\nDone. Saved {saved} plot(s) to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
