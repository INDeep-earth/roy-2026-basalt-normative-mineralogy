"""
figure5.py — Roy et al. (2026), Communications Earth & Environment

Generates unfolded basalt tetrahedron (Thompson 1984) plots for each
geological age group in the deep-time compilation (Gard et al., 2019
Filtered sheet of Supplementary Data 1).

One PDF is saved per geological age group.

Input
-----
Supplementary Data 1 (Figshare: https://doi.org/10.6084/m9.figshare.30386002)
  Sheet: Gard et al., 2019 Filtered

Required columns
----------------
  geol_age, normative_name
  Quartz_%wt, Hypersthene_%wt, Olivine_%wt, Nepheline_%wt, Diopside_%wt

Optional columns (set to 0 if absent)
--------------------------------------
  Leucite_%wt, Kaliophilite_%wt

Notes
-----
  - The combined nepheline field plotted on the Ne apex is:
        Ne_combo = Nepheline + Leucite + Kaliophilite
  - normative_name is required for exact reproducibility of the published figure.

References
----------
  Gard, M., Hasterok, D. & Halpin, J. A. (2019). Global whole-rock geochemical
  database compilation. Earth Syst. Sci. Data, 11, 1553–1566.
  https://doi.org/10.5194/essd-11-1553-2019

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
import seaborn as sns

# ---------------------------------------------------------------------------
# USER CONFIGURATION — update these two paths before running
# ---------------------------------------------------------------------------
INPUT_FILE = Path(r"C:\path\to\Supplementary Data 1.xlsx")
OUTPUT_DIR = Path(r"C:\path\to\output\figure5")

SHEET_NAME = "Gard et al., 2019 Filtered"

# ---------------------------------------------------------------------------
# COLUMN RESOLUTION
# ---------------------------------------------------------------------------
_COLUMN_CANDIDATES: dict[str, list[str]] = {
    "Quartz_%wt":       ["Quartz_%wt", "Quartz %wt", "Quartz", "quartz", "Q"],
    "Hypersthene_%wt":  ["Hypersthene_%wt", "Hypersthene %wt", "Hypersthene", "hypersthene", "Hy"],
    "Olivine_%wt":      ["Olivine_%wt", "Olivine %wt", "Olivine", "olivine", "Ol"],
    "Nepheline_%wt":    ["Nepheline_%wt", "Nepheline %wt", "Nepheline", "nepheline", "Ne"],
    "Diopside_%wt":     ["Diopside_%wt", "Diopside %wt", "Diopside", "diopside", "Di"],
    "Leucite_%wt":      ["Leucite_%wt", "Leucite %wt", "Leucite", "leucite", "Lc"],
    "Kaliophilite_%wt": ["Kaliophilite_%wt", "Kaliophilite %wt", "Kaliophilite", "kaliophilite",
                         "Kalsilite_%wt", "Kalsilite %wt", "Kalsilite", "kalsilite", "Kls"],
}

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


def _sanitise_filename(name: str, max_len: int = 150) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", str(name))
    name = re.sub(r"\s+", "_", name.strip())
    return name[:max_len]


def _ternary_to_cartesian(
    a: pd.Series, b: pd.Series, c: pd.Series,
    pa: tuple[float, float], pb: tuple[float, float], pc: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    x = a * pa[0] + b * pb[0] + c * pc[0]
    y = a * pa[1] + b * pb[1] + c * pc[1]
    return x.to_numpy(), y.to_numpy()


def _row_normalise(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    row_sums = df.sum(axis=1)
    df = df[row_sums > 0]
    return df.div(row_sums[row_sums > 0], axis=0).dropna(how="any")


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
# PER-AGE PLOT
# ---------------------------------------------------------------------------

def _plot_age(
    df: pd.DataFrame,
    age_col: str,
    normative_col: str,
    age_value: str,
    output_dir: Path,
) -> bool:
    sub = df[df[age_col].astype(str) == age_value].copy()
    if sub.empty:
        print(f"  [skip] No data for: {age_value}")
        return False

    required = ["Ne_combo_%wt", "Olivine_%wt", "Diopside_%wt", "Hypersthene_%wt", "Quartz_%wt"]
    if any(col not in sub.columns for col in [normative_col] + required):
        print(f"  [skip] {age_value}: missing required columns")
        return False

    numeric = sub[required].apply(pd.to_numeric, errors="coerce")
    sub = pd.concat([sub[[normative_col]], numeric], axis=1)

    left   = sub[sub[normative_col] == "nepheline_normative"][["Ne_combo_%wt", "Olivine_%wt",  "Diopside_%wt"]].dropna()
    middle = sub[sub[normative_col] == "olivine_normative"]  [["Olivine_%wt",  "Diopside_%wt", "Hypersthene_%wt"]].dropna()
    right  = sub[sub[normative_col] == "quartz_normative"]   [["Diopside_%wt", "Hypersthene_%wt", "Quartz_%wt"]].dropna()

    left_n, middle_n, right_n = _row_normalise(left), _row_normalise(middle), _row_normalise(right)

    def to_xy(d, p1, p2, p3):
        if d.empty:
            return np.array([]), np.array([])
        return _ternary_to_cartesian(d.iloc[:, 0], d.iloc[:, 1], d.iloc[:, 2], p1, p2, p3)

    x_l, y_l = to_xy(left_n,   _NE, _OL, _DI)
    x_m, y_m = to_xy(middle_n, _OL, _DI, _HY)
    x_r, y_r = to_xy(right_n,  _DI, _HY, _QZ)

    all_x = np.concatenate([x_l, x_m, x_r])
    all_y = np.concatenate([y_l, y_m, y_r])

    if all_x.size == 0:
        print(f"  [skip] {age_value}: no plottable points")
        return False

    fig, ax = plt.subplots(figsize=(10, 6))

    for xs, ys, label in [
        (x_l, y_l, "Ne-normative (Ne+Lc+Kp)"),
        (x_m, y_m, "Ol-normative"),
        (x_r, y_r, "Qz-normative"),
    ]:
        if xs.size:
            ax.scatter(xs, ys, s=12, alpha=0.7, facecolor="gray",
                       edgecolor="black", linewidth=0.2, label=label)

    if all_x.size > 2:
        sns.kdeplot(x=all_x, y=all_y, cmap="RdYlBu_r", fill=True, ax=ax, alpha=0.45, thresh=0.1)
        sns.kdeplot(x=all_x, y=all_y, color="white", linewidths=0.4, ax=ax)

    _draw_tetrahedron(ax)
    ax.text(1.98, _H + 0.06, f"n={all_x.size}", fontsize=9, ha="right")
    ax.set_title(age_value, fontsize=13)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_xlim(-0.1, 2.1); ax.set_ylim(-0.1, _H + 0.12)

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc="upper left", fontsize=8, frameon=False)

    out_path = output_dir / f"{_sanitise_filename(age_value)}.pdf"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path.name}")
    return True


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.is_file():
        raise FileNotFoundError(f"Input file not found:\n  {INPUT_FILE}")

    print(f"Reading: {INPUT_FILE.name}  (sheet='{SHEET_NAME}')")
    xl = pd.ExcelFile(INPUT_FILE, engine="openpyxl")
    if SHEET_NAME not in xl.sheet_names:
        raise KeyError(f"Sheet '{SHEET_NAME}' not found. Available: {xl.sheet_names}")
    df = xl.parse(SHEET_NAME)
    print(f"  {len(df):,} rows, {len(df.columns)} columns")

    # Clean column names
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    # Resolve normative mineral columns
    for target, candidates in _COLUMN_CANDIDATES.items():
        src = _resolve_column(df, candidates)
        if src is None:
            if target in ("Leucite_%wt", "Kaliophilite_%wt"):
                df[target] = 0.0
                print(f"  Note: '{target}' not found — assumed 0.")
            else:
                raise KeyError(f"Required column '{target}' not found. Tried: {candidates}")
        else:
            df[target] = pd.to_numeric(df[src], errors="coerce")

    df["Ne_combo_%wt"] = (
        df["Nepheline_%wt"].fillna(0)
        + df["Leucite_%wt"].fillna(0)
        + df["Kaliophilite_%wt"].fillna(0)
    )

    age_col = _resolve_column(
        df, ["geol_age", "Geol_Age", "Geological Age", "geological age", "Age_Group"]
    )
    if age_col is None:
        raise KeyError("Column 'geol_age' not found.")

    normative_col = _resolve_column(df, ["normative_name", "Normative_Name", "normative name"])
    if normative_col is None:
        raise KeyError(
            "Column 'normative_name' not found. This column is required for "
            "exact reproducibility of the published figure."
        )

    ages = sorted(df[age_col].dropna().astype(str).unique())
    print(f"\nGenerating plots for {len(ages)} geological age group(s):\n")

    saved = sum(
        _plot_age(df, age_col, normative_col, age, OUTPUT_DIR)
        for age in ages
    )
    print(f"\nDone — {saved}/{len(ages)} plots saved to:\n  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
