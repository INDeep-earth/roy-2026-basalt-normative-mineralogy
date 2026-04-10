# Tectonic setting and mantle source evolution reconstructed from deep time analysis of basalt geochemistry

**Shubhadeep Roy, Balz S. Kamber, Patrick C. Hayman, David T. Murphy**

*Communications Earth & Environment* (2026)

[![DOI](https://img.shields.io/badge/DOI-10.1038%2Fs43247--026--03473--4-blue)](https://doi.org/10.1038/s43247-026-03473-4)

---

## Overview

This repository contains all Python scripts used for data analysis and geochemical visualisation in Roy et al. (2026). The study presents a global deep-time analysis of basalt CIPW normative mineralogy, tracking secular changes in basalt petrology from the Archaean to the present day.

### Key findings

- Archaean continental basalts are dominantly quartz-normative (~49%), with striking compositional similarity to Phanerozoic continental flood basalts.
- Normative clinopyroxene/orthopyroxene ratios argue against dominant hydrous flux-melting as a petrogenetic mechanism for Archaean basalts.
- A progressive secular increase in nepheline-normative (alkali) basalts, with a pronounced step-change near the Precambrian–Phanerozoic boundary, is attributed to widespread mantle hybridisation following the onset of sustained, modern-style deep subduction in the Neoproterozoic.
- Two lulls in Palaeoproterozoic mafic magmatic activity are identified: the established Tectono-Magmatic Lull (~2,365–2,235 Ma) and a newly recognised lull at ~2,000 Ma.

---

## Data

All data underlying the main-text and supplementary figures are deposited in the Figshare repository:

**https://doi.org/10.6084/m9.figshare.30386002**

| File | Contents |
|------|----------|
| Supplementary Data 1 | Compiled whole-rock geochemical database (GEOROC & Gard et al. 2019 filtered sheets, curated Palaeoproterozoic dataset) |
| Supplementary Data 2 | Experimental melt compositions (Mallik & Dasgupta 2012; Davis et al. 2011) |
| Supplementary Data 3 | LDA analysis outputs |
| Supplementary Data 4 | MAGEMin fractional crystallisation model output files |

Download these files from Figshare and update the `INPUT_FILE` / `OUTPUT_DIR` paths at the top of each script before running.

---

## External software

### IoGAS (Imdex)
Used for CIPW norm calculation from whole-rock major oxide data. IoGAS is proprietary software; normative mineral proportions are provided directly in Supplementary Data 1 and 2 so that all figures can be reproduced without a licence.

### MAGEMin (v1.x)
Used for thermodynamic fractional crystallisation modelling (Figures 9a–c). MAGEMin output files are provided in Supplementary Data 4. See the [MAGEMin GitHub repository](https://github.com/ComputationalThermodynamics/MAGEMin) for installation instructions.

---

## Repository structure

```
code/
├── figure4.py              # Unfolded tetrahedron plots by tectonic setting (GEOROC Phanerozoic)
├── figure5.py              # Unfolded tetrahedron plots by geological age (Gard et al. 2019)
├── figure6.py              # Palaeoproterozoic magmatism: histogram + stacked proportions
├── figure7a.py             # Experimental melts — Mallik & Dasgupta (2012)
├── figure7b.py             # Experimental melts — Davis et al. (2011)
├── figure8.py              # KDE panels: LOI, CIA, Mg# by normative type and age
├── figure9a.py             # MAGEMin model output — Fig. 9a
├── figure9b.py             # MAGEMin model output — Fig. 9b
├── figure9c.py             # MAGEMin model output — Fig. 9c
└── _figure9_helpers.py     # Shared utilities for figure9a/b/c (internal module)
```

---

## Requirements

Python ≥ 3.10 is recommended. All dependencies are available via `pip`:

```bash
pip install matplotlib numpy pandas scipy seaborn openpyxl
```

| Package | Tested version | Purpose |
|---------|---------------|---------|
| matplotlib | ≥ 3.7 | Plotting |
| numpy | ≥ 1.24 | Numerical arrays |
| pandas | ≥ 2.0 | Data I/O and manipulation |
| scipy | ≥ 1.11 | Gaussian KDE (figure6.py) |
| seaborn | ≥ 0.13 | KDE overlays (figures 4, 5, 8) |
| openpyxl | ≥ 3.1 | Excel file reading |

---

## Usage

1. Download the Supplementary Data files from Figshare (link above).
2. Open the relevant script and set `INPUT_FILE` and `OUTPUT_DIR` at the top.
3. Run from the command line:

```bash
python figure5.py
```

Each script prints progress to the terminal and saves output PDFs to `OUTPUT_DIR`.  Scripts that generate one plot per category (figures 4, 5) create one PDF per tectonic setting / geological age group.

> **Note for figure9a/b/c:** `_figure9_helpers.py` must be in the same directory as the figure9 scripts, as it provides shared geometry and data-loading functions.

---

## Figure scripts at a glance

| Script | Input sheet | Key variable | Output |
|--------|------------|-------------|--------|
| `figure4.py` | GEOROC - PhanZ Filtered | TECTONIC SETTING | One PDF per setting |
| `figure5.py` | Gard et al., 2019 Filtered | geol_age | One PDF per age group |
| `figure6.py` | Palaeoproterozoic - Curated | Crystallisation_age_Ma | Single PDF (2 panels) |
| `figure7a.py` | Mallik and Dasgupta 2012 | Melt added (wt.%) | Single PDF |
| `figure7b.py` | Davis et al 2011 | Melt Fexp | Single PDF |
| `figure8.py` | Gard et al., 2019 Filtered | loi / cia / mg_number | Single PDF (5×3 panels) |
| `figure9a.py` | Fig 9a | P[kbar] (fixed 1.80–2.20) | Single PDF |
| `figure9b.py` | Fig 9b | P[kbar] (dynamic range) | Single PDF |
| `figure9c.py` | Fig 9c | P[kbar] (dynamic range) | Single PDF |

---

## Citation

If you use these scripts or data in your work, please cite:

> Roy, S., Kamber, B.S., Hayman, P.C. et al. Tectonic setting and mantle source evolution reconstructed from deep time analysis of basalt geochemistry. Commun Earth Environ (2026). https://doi.org/10.1038/s43247-026-03473-4

Data citation:

> Roy, S., Kamber, B. S., Hayman, P. C. & Murphy, D. T. (2026). Data for: Tectonic setting and mantle source evolution reconstructed from deep time analysis of basalt geochemistry [Dataset]. *Figshare*. https://doi.org/10.6084/m9.figshare.30386002

---

## Acknowledgements

This work was funded by Australian Research Council grant DP220100136 (to B.S.K. and P.C.H.) and a Queensland University of Technology Postgraduate Scholarship (to S.R.).

---

## Contact

**Shubhadeep Roy** — [shubhadeep.roy@hdr.qut.edu.au](mailto:shubhadeep.roy@hdr.qut.edu.au)  
School of Earth and Atmospheric Sciences, Queensland University of Technology, Brisbane, QLD, Australia

---

## Licence

Code released under the [MIT Licence](LICENSE).
