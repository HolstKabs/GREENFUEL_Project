# brightway-ecoinvent-project

Small Brightway2 workflow for:
- importing ecoinvent 3.12 in EcoSpold2 format, and
- running a SURE biomass LCA model with deterministic and Monte Carlo results.

## Notebook 1: Biomass LCA

Notebook: `Project biomass/GREENFUEL_LCA_biomass.ipynb`

Main steps:
1. Import Brightway, pandas, numpy, and Monte Carlo tools.
2. Set Brightway project (`Current`).
3. Load databases:
   - `eco 3.12_coff`
   - `biosphere3`
   - `sure_db`
4. Clear existing activities in `sure_db`.
5. Map required background activities from ecoinvent (chemicals, electricity, water, transport, drying, membrane, waste treatment, soybean).
6. Register `sure_db`, create a foreground activity (`CNF`), and add exchanges.
7. Read process data from multiple Excel sheets (`FOAK_TPC`, `1NOAK_TPC`, ..., `10NOAK_TPC`).
8. Run LCIA with ReCiPe 2016 midpoint (H) for selected categories:
   - global warming
   - terrestrial acidification
   - freshwater ecotoxicity
   - marine ecotoxicity
   - ozone depletion
   - particulate matter formation
9. Export deterministic scores and Monte Carlo summary statistics (mean/std) to an output Excel workbook.

Important notes:
- Input and output Excel paths are hard-coded to a local `C:/Users/...` directory and must be updated.
- Monte Carlo iterations are currently set to `100`.
- The notebook creates and deletes the temporary foreground activity inside each sheet loop.

## Requirements

Suggested Python packages (minimum):
- `brightway2`
- `bw2data`
- `bw2calc`
- `pandas`
- `numpy`
- `openpyxl`
- `tqdm`
- `jupyter`

Example install:

```bash
pip install brightway2 bw2data bw2calc pandas numpy openpyxl tqdm jupyter
```

## Typical run order

1. Set the desired Brightway project
5. Update Excel input/output paths.
6. Verify Brightway project and database names match your environment.
7. Run all cells to generate LCIA and Monte Carlo result sheets.

## Practical setup checklist

Before running notebooks, confirm:
- Brightway project names (`premise`, `Current`) exist or are changed to your own.
- Database name `eco 3.12_coff` is consistent across both notebooks.
- `biosphere3` is available in the active Brightway project.
- Local file paths are updated for your machine.
