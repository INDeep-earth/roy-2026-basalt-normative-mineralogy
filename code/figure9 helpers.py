"""
_figure9_helpers.py — shared utilities for figure9a/b/c.py

Internal module — not intended for direct use.

Roy et al. (2026), Communications Earth & Environment.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ternary apices in Cartesian space (unfolded tetrahedron geometry)
H  = np.sqrt(3) / 2
NE = (0.0, H)
OL = (0.5, 0.0)
DI = (1.0, H)
HY = (1.5, 0.0)
QZ = (2.0, H)


def norm_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def resolve_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    norm_map  = {norm_key(c): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    for cand in candidates:
        if norm_key(cand) in norm_map:
            return norm_map[norm_key(cand)]
    return None


def row_normalise(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out      = df.copy()
    row_sums = out[cols].sum(axis=1)
    out      = out[row_sums > 0].copy()
    out[cols] = out[cols].div(row_sums[row_sums > 0], axis=0)
    return out.dropna(subset=cols)


def ternary_to_cartesian(
    a: pd.Series, b: pd.Series, c: pd.Series,
    pa: tuple[float, float], pb: tuple[float, float], pc: tuple[float, float],
) -> tuple[pd.Series, pd.Series]:
    return (a * pa[0] + b * pb[0] + c * pc[0],
            a * pa[1] + b * pb[1] + c * pc[1])


def draw_tetrahedron(ax: plt.Axes) -> None:
    for tri in [[NE, OL, DI, NE], [OL, DI, HY, OL], [DI, HY, QZ, DI]]:
        xs, ys = zip(*tri)
        ax.plot(xs, ys, "k-", linewidth=1)
    for (x, y), label, dy in [
        (NE, "Ne", 0.05), (OL, "Ol", -0.05), (DI, "Di", 0.05),
        (HY, "Hy", -0.05), (QZ, "Qz", 0.05),
    ]:
        ax.text(x, y + dy, label, fontsize=12, ha="center", fontweight="bold")


def load_sheet(input_file: Path, sheet_name: str) -> pd.DataFrame:
    if not input_file.is_file():
        raise FileNotFoundError(f"Input file not found:\n  {input_file}")
    xl = pd.ExcelFile(input_file, engine="openpyxl")
    if sheet_name not in xl.sheet_names:
        raise KeyError(f"Sheet '{sheet_name}' not found. Available: {xl.sheet_names}")
    df = xl.parse(sheet_name)
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )
    return df


def build_cartesian(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resolve the three normative sub-fields, normalise, and compute Cartesian
    coordinates.  Returns a combined DataFrame with columns x, y, P[kbar].
    """
    col_map = {
        "normative_name":  ["normative_name", "Normative_Name", "normative name"],
        "Nepheline_%wt":   ["Nepheline_%wt", "Nepheline %wt"],
        "Olivine_%wt":     ["Olivine_%wt",   "Olivine %wt"],
        "Diopside_%wt":    ["Diopside_%wt",  "Diopside %wt"],
        "Hypersthene_%wt": ["Hypersthene_%wt","Hypersthene %wt"],
        "Quartz_%wt":      ["Quartz_%wt",    "Quartz %wt"],
        "P[kbar]":         ["P[kbar]", "P [kbar]", "Pressure", "Pressure_kbar"],
    }
    resolved = {k: resolve_column(df, v) for k, v in col_map.items()}
    missing  = [k for k, v in resolved.items() if v is None]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    df = df[[resolved[k] for k in col_map]].copy()
    df.columns = list(col_map.keys())

    numeric = ["Nepheline_%wt", "Olivine_%wt", "Diopside_%wt",
               "Hypersthene_%wt", "Quartz_%wt", "P[kbar]"]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["normative_name"] + numeric)

    parts = []
    for norm, cols, apices in [
        ("nepheline_normative", ["Nepheline_%wt", "Olivine_%wt",  "Diopside_%wt"],    (NE, OL, DI)),
        ("olivine_normative",   ["Olivine_%wt",   "Diopside_%wt", "Hypersthene_%wt"], (OL, DI, HY)),
        ("quartz_normative",    ["Diopside_%wt",  "Hypersthene_%wt", "Quartz_%wt"],   (DI, HY, QZ)),
    ]:
        sub = df[df["normative_name"].str.strip().str.lower() == norm].copy()
        sub = row_normalise(sub, cols)
        if not sub.empty:
            sub["x"], sub["y"] = ternary_to_cartesian(
                sub[cols[0]], sub[cols[1]], sub[cols[2]], *apices
            )
            parts.append(sub[["x", "y", "P[kbar]"]])

    if not parts:
        raise ValueError("No plottable data after processing normative groups.")
    return pd.concat(parts, ignore_index=True)
