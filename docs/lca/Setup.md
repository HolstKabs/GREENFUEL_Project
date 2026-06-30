# LCA Script — Setup and Run Guide

The LCA notebook (`LCA_PROJECT/Project biomass/GREENFUEL_LCA_biomass.ipynb`) runs a fully automated cradle-to-grave Life Cycle Assessment for one biomass type at a time. It reads yield parameters from the thermodynamic model output, builds a foreground LCI from the process config file, and exports LCIA results and Monte Carlo data to Excel.

**Functional unit:** 1 MJ of usable bio-oil delivered for marine propulsion.

---

## Prerequisites

### 1. Run the thermodynamic model first

The LCA notebook looks for the most recent `yield_results_*/yield_results.xlsx` file inside `BIOMASS_to_BIO-OIL/`. If no such folder exists, Step 1 will fail.

```powershell
cd BIOMASS_to_BIO-OIL
.\.venv\Scripts\Activate.ps1
python tutorial.py
```

This creates a timestamped folder (e.g. `yield_results_20250630_143200/`) containing `yield_results.xlsx`.

### 2. Install ecoinvent 3.12 in a Brightway project

The notebook requires ecoinvent 3.12 cutoff to be imported into a local Brightway2.5 project. This is a one-time setup. Ecoinvent credentials and the database file are not distributed with this repository (DTU institutional licence required).

```python
import bw2io as bi
bi.bw2setup()                              # import biosphere flows and LCIA methods
bi.SingleOutputEcospold2Importer(          # import ecoinvent
    '/path/to/ecoinvent-3.12-cutoff/datasets', 'ecoinvent-3.12-cutoff'
).apply_strategies().write_database()
```

### 3. Locate your Brightway project and database names

If you are unsure of the exact project/database names, run the **DB Check cell** (Cell 4) in the notebook before editing any other config. It prints all projects and databases with activity counts — look for the row with > 10 000 activities.

---

## Configuration (the only cell you need to edit)

Open the notebook and edit **Section 1 — USER CONFIG** (Cell 2):

```python
BW_PROJECT   = 'GREENFUEL_LCA_WOOD'          # your Brightway project name
ECOINVENT_DB = 'ecoinvent-3.12-cutoff'       # your ecoinvent database name
BIOSPHERE_DB = 'ecoinvent-3.12-biosphere'    # usually unchanged

BIOMASS_NAME    = 'Poplar 4'      # partial, case-insensitive match against subcategory column
MC_ITERATIONS   = 100             # Monte Carlo iterations (500–1000 for publication quality)
KEEP_FOREGROUND = True            # True = keep foreground DB after run; False = delete on exit
```

`BIOMASS_NAME` is matched against the `subcategory` column in both `yield_results.xlsx` and `LCA_process_config.xlsx`. Valid names are listed in the *Biomass_Selection* sheet of the config file.

---

## Running the notebook

Run all cells **top to bottom** after editing Section 1. The steps are:

| Step | What it does |
|---|---|
| **1** | Auto-locates the most recent `yield_results_*/yield_results.xlsx` and loads all biomass data |
| **1.5** | Loads `LCA_process_config.xlsx` (sheets: *Biomass_Selection*, *LCI_Mapping*) |
| **2** | Selects the chosen biomass by name match; extracts yield parameters (x, T, y, z, c, g) |
| **3** | Connects to the Brightway project and validates ecoinvent + biosphere databases |
| **4** | Looks up all ecoinvent background processes defined in *LCI_Mapping* |
| **5** | Builds the foreground LCI activity with all exchanges (Ph1–Ph5) scaled to the FU |
| **6** | Validates all exchanges — prints a warning if any are invalid |
| **7** | Runs LCIA across all 18 ReCiPe 2016 Midpoint (H) categories |
| **7b** | Runs endpoint LCIA — ReCiPe 2016 Endpoint (H), 3 areas of protection (Human Health, Ecosystem Quality, Natural Resources) |
| **8** | Exports results to `LCA_results/lca_results_{BIOMASS_NAME}.xlsx` (sheets: *All Categories*, *Top 4*, endpoint) |
| **9** | Runs Monte Carlo uncertainty analysis for the top 4 impact categories; saves samples to `Monte_carlo_analysis/` |

Do **not** edit cells below the `ENGINE — do not edit cells below this line` divider.

---

## Output files

After a successful run, two output locations are updated (relative to `LCA_PROJECT/Project biomass/`):

```
LCA_results/
    lca_results_{BIOMASS_NAME}.xlsx   ← LCIA scores for all 18 midpoint + 3 endpoint categories

Monte_carlo_analysis/
    mc_{BIOMASS_NAME}_{category}.xlsx ← Monte Carlo samples per top-4 impact category
```

These files are read by the Streamlit webapp (`webapp/pages/3_Environmental.py`) to display results and uncertainty charts. Run the notebook for each of the 9 modelled biomass types to populate the full dataset.

---

## Changing processes or parameters

All ecoinvent process names, transport distances, and energy intensities are defined in `LCA_process_config.xlsx` — **not** in the notebook. To change a process or default value:

1. Open `LCA_process_config.xlsx`
2. Edit the relevant row in the *LCI_Mapping* sheet (process name, location) or *Parameters* sheet (default values)
3. Re-run the notebook

See `docs/lca/LCA_reporting.md` for a full description of all phases and amount formulas.

---

## Reference documents

| Document | Description |
|---|---|
| `docs/lca/LCA_reporting.md` | Goal, scope, and full LCI phase descriptions |
| `docs/lca/Parameters.md` | All model parameters with symbols, defaults and units |
| `docs/lca/biomass_categories_specific_LCI.md` | Per-category feedstock and process selection notes |
| `LCA_process_config.xlsx` | Master config: biomass data, parameters, LCI process mapping |
