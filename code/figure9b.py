"""
figure9b.py — Roy et al. (2026), Communications Earth & Environment

Plots MAGEMin thermodynamic fractional crystallisation model output (Fig. 9b)
on the unfolded basalt tetrahedron (Thompson 1984).

Points are coloured by pressure (P[kbar]) using a dynamic scale derived
from the data range in the sheet.

Input
-----
Supplementary Data 4 (Figshare: https://doi.org/10.6084/m9.figshare.30386002)
  Sheet: Fig 9b

Required columns
----------------
  normative_name, P[kbar]
  Nepheline_%wt, Olivine_%wt, Diopside_%wt, Hypersthene_%wt, Quartz_%wt

Notes
-----
  MAGEMin (v1.x) was used for modelling; see
  https://github.com/ComputationalThermodynamics/MAGEMin for installation.

References
----------
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

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from _figure9_helpers import H, build_cartesian, draw_tetrahedron, load_sheet

# ---------------------------------------------------------------------------
# USER CONFIGURATION — update these two paths before running
# ---------------------------------------------------------------------------
INPUT_FILE = Path(r"C:\path\to\Supplementary Data 4.xlsx")
OUTPUT_DIR = Path(r"C:\path\to\output\figure9b")

SHEET_NAME = "Fig 9b"


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading: {INPUT_FILE.name}  (sheet='{SHEET_NAME}')")
    df     = load_sheet(INPUT_FILE, SHEET_NAME)
    df_all = build_cartesian(df)
    print(f"  {len(df_all)} points to plot")

    p_vals = df_all["P[kbar]"].to_numpy()
    vmin, vmax = float(np.nanmin(p_vals)), float(np.nanmax(p_vals))
    if np.isclose(vmin, vmax):
        vmin, vmax = vmin - 1e-9, vmax + 1e-9

    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(
        df_all["x"], df_all["y"],
        c=p_vals,
        cmap="viridis_r",
        norm=plt.Normalize(vmin=vmin, vmax=vmax),
        edgecolor="k", marker="o", s=80, linewidth=0.3, alpha=0.9,
    )
    draw_tetrahedron(ax)
    plt.colorbar(sc, ax=ax, pad=0.02).set_label("P (kbar)")

    ax.set_xticks([]); ax.set_yticks([])
    ax.set_frame_on(False)
    ax.set_xlim(-0.1, 2.1); ax.set_ylim(-0.1, H + 0.1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Figure 9b — MAGEMin model output", fontsize=13)

    out_path = OUTPUT_DIR / "figure9b_magemin_projection.pdf"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.show()
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
