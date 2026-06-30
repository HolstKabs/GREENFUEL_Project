# GREENFUEL — Biomass Pyrolysis & Life Cycle Assessment Toolkit

This repository contains a thermodynamic modelling workflow and Streamlit web application for predicting bio-oil yields from biomass pyrolysis, combined with Life Cycle Assessments (LCA) modelled and programmed for evaluating the environmental impact of biomass-derived fuels. The project was developed at the Technical University of Denmark (DTU) with the goal of comparing biomass-derived bio-oil with conventional marine fuel oil.

## Webpage for easy access to results

To see all results in a user-friendly way, go to: **https://greenfuelproject.streamlit.app/** and browse through the pages. You can see theoretical bio-oil yields for specific biomass types, compare different biomass types, read LCA results for 9 modelled and computed biomass types, more are going to be modelled, and finally, look at how far certain biomass types, in theory can transport goods from the transport sector from China to Denmark.

---

## Repository Structure

```
GREENFUEL_PROJECT/
├── BIOMASS_to_BIO-OIL/          # Thermodynamic modelling engine + Streamlit webapp
│   ├── biomass_pyrolysis_equilibrium/   # Core Python package
│   │   ├── data/                # Excel parsing, normalisation, feedstock–bio-oil matching
│   │   ├── thermodynamics/      # HHV/LHV, ΔHf, ΔSf, ΔGf calculations
│   │   ├── species/             # Gas species registry, bio-oil pseudo-species, candidate pool
│   │   ├── optimization/        # Gibbs free energy minimisation solver (SLSQP)
│   │   ├── workflow/            # Top-level orchestrator
│   │   ├── qa/                  # Reporting, plotting, Excel/PNG export, validator
│   │   ├── config.py            # Configuration dataclasses
│   │   └── models.py            # Domain dataclasses
│   ├── webapp/                  # Streamlit web application
│   │   ├── pages/               # Multi-page app (Overview, Pyrolysis, Environmental, …)
│   │   ├── charts.py            # All Plotly/matplotlib chart functions
│   │   ├── app.py               # App entry point
│   │   └── requirements_webapp.txt
│   ├── tests/                   # Unit and integration test suite
│   ├── docs/                    # User guide, technical manual, workflow guide
│   ├── examples/                # Example scripts
│   ├── Feedstock_reference/     # Master feedstock Excel workbook
│   ├── tutorial.py              # CLI entry point
│   ├── tutorial_workbook_paths.py  # Workbook path configuration
│   ├── excel_generator.py       # Post-processing utility for yield results
│   ├── formulations.md          # Scientific formulations reference
│   ├── CODEBASE_ANALYSIS.md     # Detailed architecture documentation
│   └── requirements.txt         # Python dependencies
│
├── LCA_PROJECT/
│   └── Project biomass/         # LCA notebooks, results, and Monte Carlo analysis
│       ├── GREENFUEL_LCA_biomass.ipynb   # Main LCA analysis notebook
│       ├── combine_all_excel.ipynb       # Result aggregation notebook
│       ├── LCA_results/                  # Per-biomass LCA result workbooks (9 feedstocks)
│       ├── Monte_carlo_analysis/         # Monte Carlo uncertainty data (9 × xlsx)
│       └── LCA_process_config.xlsx       # Brightway2 process configuration
│
└── README.md                    # This file
```

---

## Requirements

- Python 3.10 or later
- pip

The thermodynamic modelling engine and Streamlit webapp have separate dependency files.

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd GREENFUEL_PROJECT
```

### 2. Create and activate a virtual environment

```bash
cd BIOMASS_to_BIO-OIL
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

For the core modelling engine:

```bash
pip install -r requirements.txt
```

For the Streamlit webapp (additional packages):

```bash
pip install -r webapp/requirements_webapp.txt
```

---

## Running the CLI Tutorial

The tutorial script runs the full thermodynamic workflow from the command line and writes a timestamped Excel workbook and PNG charts to a `yield_results_YYYYMMDD_HHMMSS/` folder.

**Step 1 — configure the workbook path** in `tutorial_workbook_paths.py`:

```python
WORKBOOK_PATHS = {
    "path1": "Feedstock_reference/Feedstock_table - USE THIS ONE.xlsx",
}
ACTIVE_WORKBOOK_PATH_KEY = "path1"
```

**Step 2 — run:**

```bash
python tutorial.py
```

Output files are written to `BIOMASS_to_BIO-OIL/yield_results_<timestamp>/`.

---

## Running the Streamlit Webapp

```bash
cd BIOMASS_to_BIO-OIL
streamlit run webapp/app.py
```

The app opens in your browser at `http://localhost:8501`. It provides an interactive multi-page interface covering:

- **🏠Home** - Short introduction to project and overview of page tabs.
- **🔍Biomass Xplorer** - browse all feedstocks, filter by category or yield, and spot the best candidates.
- **📊Comparing-X/Y's** pick different feedstocks and compare them side-by-side on yield or many other metrics.
- **🌱Environmental ImpactsX** - explore the LCA results, with Monte Carlo uncertainty ranges, to see how the feedstocks compare on environmental impact.
- **🚢Transportation of GoodsX** - see how far, long-distance container shipping, can travel and how it changes, when the feedstock types changes.
- **ℹ️About** - Introduction to development team, research team and funded by. 

---

## Running the LCA Notebook

Open Jupyter and navigate to the main LCA notebook:

```bash
jupyter notebook "LCA_PROJECT/Project biomass/GREENFUEL_LCA_biomass.ipynb"
```

> **Prerequisites:** ecoinvent 3.12 (cutoff system model) must be installed in a local Brightway2 project. See `LCA_PROJECT/Project biomass/Setup.md` for setup instructions.

---

## Running the Tests

```bash
cd BIOMASS_to_BIO-OIL
python -m unittest discover tests -v
```

The test suite covers all core modules across unit and integration levels.

---

## Documentation

| Document | Description |
|----------|-------------|
| `BIOMASS_to_BIO-OIL/docs/userguide.tex` | Step-by-step guide for end users |
| `BIOMASS_to_BIO-OIL/docs/usermanual.tex` | Technical reference for developers and researchers |
| `BIOMASS_to_BIO-OIL/docs/WORKFLOW_GUIDE.md` | Model walkthrough with equations |
| `BIOMASS_to_BIO-OIL/docs/TECHNICAL_SUMMARY.md` | Architecture overview |
| `BIOMASS_to_BIO-OIL/formulations.md` | Thermodynamic formulations reference |
| `BIOMASS_to_BIO-OIL/CODEBASE_ANALYSIS.md` | Module-by-module codebase analysis |

---

## License

This project is licensed under the [MIT License](LICENSE) — free to use, modify, and distribute with attribution.

---

## Citation & Acknowledgements

This work was carried out at the Technical University of Denmark (DTU). If you use this software in your research, please cite the accompanying publication (reference to be added upon acceptance).

Ecoinvent database access was provided through DTU's institutional licence. The ecoinvent database itself is not distributed with this repository.
