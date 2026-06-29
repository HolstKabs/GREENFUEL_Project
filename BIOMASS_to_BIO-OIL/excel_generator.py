import os
import glob
from pathlib import Path

import pandas as pd
import numpy as np

# ── Configuration ─────────────────────────────────────────────────────────────
# Resolve relative to this file so the project runs from any location.
YIELD_BASE = str(Path(__file__).resolve().parent)
FILENAME = 'yield_results_clean.xlsx'          # file name inside the yield_results_* folder
SHEET_NAME = 'results'                   # change if your sheet name differs
yield_col = "oil_yield_kg_per_kg"        # change to oil_yield_kg_per_kg_dry etc. if desired

# ── Find latest folder ────────────────────────────────────────────────────────
folders = sorted(glob.glob(os.path.join(YIELD_BASE, 'yield_results_*')))
if not folders:
    raise FileNotFoundError(f'No yield_results_* folders found in: {YIELD_BASE}')

latest = folders[-1]
yield_file = os.path.join(latest, FILENAME)

print('Folders found:')
for f in folders:
    tag = '  <-- USING THIS' if f == latest else ''
    print(f'  {os.path.basename(f)}{tag}')

print(f'\nReading: {yield_file}')

# ── Load data ─────────────────────────────────────────────────────────────────
if not Path(yield_file).exists():
    raise FileNotFoundError(f'Expected file not found: {yield_file}')

df_all = pd.read_excel(yield_file)
print(f'Loaded {len(df_all)} rows | {df_all.get("feedstock_id", pd.Series()).nunique()} unique feedstocks')

# ── Clean and ensure numeric ──────────────────────────────────────────────────
df = df_all.copy()
df[yield_col] = pd.to_numeric(df[yield_col], errors="coerce")
df = df.dropna(subset=[yield_col])
if df.empty:
    raise ValueError(f'No valid numeric values found in column: {yield_col}')

# ── Filter unrealistic yield values before percentile calculation ─────────────
df = df[df[yield_col].between(0.01, 0.90, inclusive='both')]
if df.empty:
    raise ValueError('No rows remain after applying yield cutoffs (0.01 – 0.90).')
print(f'After cutoff filter: {len(df)} rows | {df["feedstock_id"].nunique()} unique feedstocks')

# ── Compute global quantiles ─────────────────────────────────────────────────
q25 = df[yield_col].quantile(0.25)
q45 = df[yield_col].quantile(0.45)
q50 = df[yield_col].quantile(0.50)
q55 = df[yield_col].quantile(0.55)
q75 = df[yield_col].quantile(0.75)

# ---------- Build filters ----------
mask_low = df[yield_col] <= q25
mask_mid = (df[yield_col] >= q45) & (df[yield_col] <= q55)   # inclusive 45-55%
mask_high = df[yield_col] >= q75

# ---------- Combine and keep only matching rows ----------
df_selected = pd.concat([df[mask_low], df[mask_mid], df[mask_high]], axis=0)
df_selected = df_selected.drop_duplicates().reset_index(drop=True)

# ---------- Add a label column for clarity ----------
def label_row(v):
    if v <= q25:
        return "Low <=25%"
    if q45 <= v <= q55:
        return "Mid 45-55%"
    if v >= q75:
        return "High >=75%"
    return "UNEXPECTED"

df_selected["selected_range"] = df_selected[yield_col].apply(label_row)

# ---------- Summary and save ----------
print(f"Quantiles: 25%={q25:.6g}, 45%={q45:.6g}, 50%={q50:.6g}, 55%={q55:.6g}, 75%={q75:.6g}")
print(df_selected["selected_range"].value_counts())

out_path = os.path.join(latest, "yield_with_categories.xlsx")
df_selected.to_excel(out_path, index=False)
print(f"Saved categorized results to: {out_path}")


