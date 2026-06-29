# Biomass Pyrolysis Equilibrium Workflow

This project predicts biomass pyrolysis equilibrium yields and exports results with analysis plots.

## Start Here

For full setup, model explanation, and troubleshooting, read:

- [docs/WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md)

## Quick Start (New Users)

1. Activate the virtual environment:


2. Set your workbook path key and file path in [tutorial_workbook_paths.py](tutorial_workbook_paths.py).

3. Run the tutorial workflow:

```powershell
python tutorial.py
```

## What You Get

- A timestamped result workbook in project root:
  - `yield_results_YYYYMMDD_HHMMSS.xlsx`
- Plot artifacts in:
  - `yield_results_plots`

## Optional

- Example runner: [examples/run_workflow_example.py](examples/run_workflow_example.py)
- Run tests:

```powershell
python -m unittest discover tests -v
```
