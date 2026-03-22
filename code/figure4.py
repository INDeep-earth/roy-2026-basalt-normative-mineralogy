"""
figure4.py — Roy et al. (2026), Communications Earth & Environment

Generates unfolded basalt tetrahedron (Thompson 1984) plots for each tectonic
setting in the Phanerozoic dataset (GEOROC - PhanZ Filtered sheet of
Supplementary Data 1).

One PDF is saved per tectonic setting.

Input
-----
Supplementary Data 1 (Figshare: https://doi.org/10.6084/m9.figshare.30386002)
  Sheet: GEOROC - PhanZ Filtered

Required columns
----------------
  TECTONIC SETTING
  Quartz_%wt, Hypersthene_%wt, Olivine_%wt, Nepheline_%wt, Diopside_%wt

Optional columns (set to 0 if absent)
--------------------------------------
  Leucite_%wt, Kaliophilite_%wt

Notes
-----
  - The combined nepheline field plotted on the Ne apex is:
        Ne_combo = Nepheline + Leucite + Kaliophilite
  - normative_name is used if present; otherwise it is estimated from the
    non-zero normative mineral fields.

Reference
---------
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
OUTPUT_DIR = Path(r"C:\path\to\output\figure4")

SHEET_NAME = "GEOROC - PhanZ Filtered"

# ---------------------------------------------------------------------------
# COLUMN RESOLUTION — tolerant matching for known variants
# ---------------------------------------------------------------------------
_COLUMN_CANDIDATES: dict[str, list[str]] = {
    "Quartz_%wt":        ["Quartz_%wt", "Quartz %wt", "Quartz", "quartz", "Q"],
    "Hypersthene_%wt":   ["Hypersthene_%wt", "Hypersthene %wt", "Hypersthene", "hypersthene", "Hy"],
    "Olivine_%wt":       ["Olivine_%wt", "Olivine %wt", "Olivine", "olivine", "Ol"],
    "Nepheline_%wt":     ["Nepheline_%wt", "Nepheline %wt", "Nepheline", "nepheline", "Ne"],
    "Diopside_%wt":      ["Diopside_%wt", "Diopside %wt", "Diopside", "diopside", "Di"],
    "Leucite_%wt":       ["Leucite_%wt", "Leucite %wt", "Leucite", "leucite", "Lc"],
    "Kaliophilite_%wt":  ["Kaliophilite_%wt", "Kaliophilite %wt", "Kaliophilite", "kaliophilite",
                          "Kalsilite_%wt", "Kalsilite %wt", "Kalsilite", "kalsilite", "Kls"],
}

# Ternary apices in Cartesian space (unfolded tetrahedron geometry)
_H = np.sqrt(3) / 2
_NE  = (0.0, _H)
_OL  = (0.5, 0.0)
_DI  = (1.0, _H)
_HY  = (1.5, 0.0)
_QZ  = (2.0, _H)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _norm_key(text: str) -> str:
    """Strip non-alphanumeric characters and lowercase for fuzzy matching."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def _resolve_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first matching DataFrame column from a list of candidates."""
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
    """Return a filesystem-safe version of *name*."""
    name = re.sub(r'[\\/*?:"<>|]', "_", str(name))
    name = re.sub(r"\s+", "_", name.strip())
    return name[:max_len]


def _ternary_to_cartesian(
    a: pd.Series, b: pd.Series, c: pd.Series,
    pa: tuple[float, float], pb: tuple[float, float], pc: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Convert barycentric (ternary) coordinates to 2-D Cartesian."""
    x = a * pa[0] + b * pb[0] + c * pc[0]
    y = a * pa[1] + b * pb[1] + c * pc[1]
    return x.to_numpy(), y.to_numpy()


def _row_normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise each row so that selected columns sum to 1."""
    if df.empty:
        return df
    row_sums = df.sum(axis=1)
    df = df[row_sums > 0]
    return df.div(row_sums[row_sums > 0], axis=0).dropna(how="any")


def _classify_normative(row: pd.Series) -> str | float:
    """Infer normative_name from non-zero mineral fields when the column is absent."""
    q, h = row["Quartz_%wt"], row["Hypersthene_%wt"]
    o, n = row["Olivine_%wt"], row["Nepheline_%wt"]
    if pd.notna(q) and q > 0 and pd.notna(h) and h > 0:
        return "quartz_normative"
    if pd.notna(o) and o > 0 and pd.notna(h) and h > 0:
        return "olivine_normative"
    if pd.notna(n) and n > 0 and pd.notna(o) and o > 0:
        return "nepheline_normative"
    return float("nan")


def _draw_tetrahedron(ax: plt.Axes) -> None:
    """Draw the three-triangle unfolded tetrahedron outline and apex labels."""
    for tri in [
        [_NE, _OL, _DI, _NE],
        [_OL, _DI, _HY, _OL],
        [_DI, _HY, _QZ, _DI],
    ]:
        xs, ys = zip(*tri)
        ax.plot(xs, ys, "k-", linewidth=1)

    labels = [
        (_NE, "Ne", "center", 0.05),
        (_OL, "Ol", "center", -0.05),
        (_DI, "Di", "center", 0.05),
        (_HY, "Hy", "center", -0.05),
        (_QZ, "Qz", "center", 0.05),
    ]
    for (x, y), label, ha, dy in labels:
        ax.text(x, y + dy, label, fontsize=12, ha=ha, fontweight="bold")


# ---------------------------------------------------------------------------
# PER-SETTING PLOT
# ---------------------------------------------------------------------------

def _plot_setting(
    df: pd.DataFrame,
    tectonic_col: str,
    normative_col: str,
    setting: str,
    output_dir: Path,
) -> bool:
    sub = df[df[tectonic_col].astype(str) == setting].copy()
    if sub.empty:
        print(f"  [skip] No data for: {setting}")
        return False

    required = ["Ne_combo_%wt", "Olivine_%wt", "Diopside_%wt", "Hypersthene_%wt", "Quartz_%wt"]
    if any(col not in sub.columns for col in [normative_col] + required):
        print(f"  [skip] {setting}: missing required columns")
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
        print(f"  [skip] {setting}: no plottable points")
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
    ax.set_title(setting, fontsize=13)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_xlim(-0.1, 2.1); ax.set_ylim(-0.1, _H + 0.12)

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, loc="upper left", fontsize=8, frameon=False)

    out_path = output_dir / f"{_sanitise_filename(setting)}.pdf"
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

    # Resolve and coerce normative mineral columns
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

    # Combined Ne apex
    df["Ne_combo_%wt"] = (
        df["Nepheline_%wt"].fillna(0)
        + df["Leucite_%wt"].fillna(0)
        + df["Kaliophilite_%wt"].fillna(0)
    )

    # Tectonic setting column
    tectonic_col = _resolve_column(df, ["TECTONIC SETTING", "Tectonic Setting", "tectonic setting"])
    if tectonic_col is None:
        raise KeyError("Column 'TECTONIC SETTING' not found.")

    # normative_name column (or derive it)
    normative_col = _resolve_column(df, ["normative_name", "Normative_Name", "normative name"])
    if normative_col is None:
        print("  Note: 'normative_name' column absent — inferring from mineral fields.")
        df["normative_name"] = df.apply(_classify_normative, axis=1).astype("string")
        normative_col = "normative_name"

    settings = sorted(df[tectonic_col].dropna().astype(str).unique())
    print(f"\nGenerating plots for {len(settings)} tectonic setting(s):\n")

    saved = sum(
        _plot_setting(df, tectonic_col, normative_col, s, OUTPUT_DIR)
        for s in settings
    )
    print(f"\nDone — {saved}/{len(settings)} plots saved to:\n  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
