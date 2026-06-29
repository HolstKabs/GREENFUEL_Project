# Biomass Pyrolysis Equilibrium Workflow — Codebase Analysis & Assessment

**Date:** April 2026  
**Reviewer:** Code Analysis Agent  
**Status:** Phases 1-3 Complete; Phase 4 Planned

---

## Executive Summary

This Python workflow performs **thermodynamic equilibrium modeling of biomass pyrolysis** to calculate theoretical bio-oil, gas, and char yields. It reads feedstock proximate/ultimate analysis from Excel, maps feedstocks to bio-oil profiles, applies fuzzy matching and synonym normalization, solves Gibbs free energy minimization across temperature-pressure grids, and generates analytics plots.

**Primary Goal (User):** Compare biomass-derived bio-oil properties with conventional container ship fuel oil.

**Current State:** Phases 1-3 fully implemented with 20 unit tests passing. Sweep mode enabled; three analytics plots generated.

---

## 1. SYSTEM ARCHITECTURE & WHAT IT DOES

### 1.1 High-Level Workflow

```
Excel Input (Feedstock_table.xlsx)
    ↓
[Parser] Normalize & map feedstocks ↔ bio-oils
    ↓
[Thermodynamics] Compute HHV, LHV, ΔH_f, ΔS_f, ΔG_f
    ↓
[Species Pool] Generate product candidates (gases, bio-oil, char)
    ↓
[Gibbs Solver] Minimize total Gibbs free energy at each T,P condition
    ↓
[Post-Processor] Extract yields (oil, gas, char) & efficiency
    ↓
[Reporting & QA] Generate DataFrames with metadata
    ↓
[Plotting & Export] Van Krevelen, ternary C-H-O, yield-vs-temperature charts
    ↓
Excel Output (yield_results.xlsx) + PNG Plots
```

### 1.2 Key Modules

| Module | Purpose | Status |
|--------|---------|--------|
| **config.py** | Configuration contracts (Processing, Thermo, Equilibrium, Sweep, Species configs) | ✅ Complete |
| **models.py** | Domain dataclasses (FeedstockRecord, BioOilRecord, EquilibriumSolution, WorkflowRowResult, etc.) | ✅ Complete |
| **data/parser.py** | Parse Excel sheets, normalize decimals/ranges, fuzzy-match feedstocks to bio-oils | ✅ Complete (Phase 1) |
| **data/normalizer.py** | Clean numerical data (comma→dot, ranges→midpoints, etc.) | ✅ Complete |
| **thermodynamics/heating_value.py** | Channiwala-Parikh HHV correlation; LHV calculation | ✅ Complete |
| **thermodynamics/properties.py** | Compute ΔH_f, ΔS_f, ΔG_f for feedstock | ✅ Complete |
| **thermodynamics/stoichiometry.py** | Elemental mole balance from proximate/ultimate analysis | ✅ Complete |
| **species/bio_oil.py** | Convert BioOilRecord → pseudo-species with thermo properties | ✅ Complete |
| **species/candidate_pool.py** | Build species pool (bio-oil + gas candidates + fallback char) | ✅ Complete |
| **species/registry.py** | Standard gas species thermodynamic database | ✅ Complete |
| **optimization/gibbs_solver.py** | Gibbs objective function, element balance residuals, multi-start initial guesses | ✅ Complete |
| **optimization/executor.py** | solve_feedstock_equilibrium() — orchestrate solver per condition | ✅ Complete (Phase 2) |
| **optimization/post_processor.py** | Convert EquilibriumSolution → WorkflowRowResult with yields | ✅ Complete |
| **workflow/orchestrator.py** | run_workflow() — Parse, sweep conditions, loop solver, collect results | ✅ Complete (Phase 2) |
| **qa/reporting.py** | Convert results to DataFrames; compute temperature & pressure conversions | ✅ Complete |
| **qa/plotting.py** | Van Krevelen, ternary C-H-O, yield-vs-temperature matplotlib charts | ✅ Complete (Phase 3) |
| **qa/artifacts.py** | Export to Excel/CSV, optional plot PNG files | ✅ Complete (Phase 3) |
| **qa/validator.py** | Count non-converged rows, max residual inspection | ✅ Complete |

### 1.3 Current Feature Set

#### ✅ Implemented (Phases 1-3)
1. **Data Parsing & Cleaning**
   - Comma-to-dot decimal conversion
   - Numerical range handling (midpoint or single-bound)
   - Reference metadata retention (bibliography, suitability, regionality)

2. **Feedstock-to-Bio-Oil Mapping (Phase 1: Fuzzy Matching)**
   - 4-tier matching strategy:
     1. Exact canonical match
     2. Synonym-normalized match (e.g., "wood" → "timber", "sawdust")
     3. Token-overlap fuzzy match (difflib.SequenceMatcher)
     4. Levenshtein distance fallback (thefuzz.token_set_ratio, configurable threshold)
   - Graceful fallback to generic bio-oil if no match found
   - Warning codes track matching method used (MAP_SYNONYM_NORMALIZED, MAP_SUBCATEGORY_LEVENSHTEIN, etc.)

3. **Thermodynamic Property Calculation**
   - HHV via Channiwala-Parikh correlation (C, H, O, N, S, Ash)
   - LHV from HHV accounting for hydrogen oxidation + moisture latent heat
   - Enthalpy of formation (ΔH_f) from LHV + product combustion terms
   - Entropy heuristic (calibrated but not yet literature-backed)
   - Gibbs free energy (ΔG_f = ΔH_f - T·ΔS_f) at reference temperature

4. **Temperature-Pressure Sweep (Phase 2)**
   - Configurable ranges: 300–800°C, 1–5 bar default
   - Configurable point counts: 11 temperature × 5 pressure = 55 conditions
   - Linspace grid generation (linear spacing)
   - Per-condition solver execution
   - Output cardinality: feedstocks × conditions (e.g., 499 × 55 = 27,445 rows)

5. **Gibbs Minimization Solver**
   - Simultaneous multi-phase equilibrium (gas + liquid oil + solid char)
   - Element conservation constraints (C, H, O, N, S)
   - Multi-start initial guesses (3 attempts by default)
   - scipy.optimize.minimize with SLSQP
   - Residual tracking and convergence diagnostics

6. **Analytics & Visualization (Phase 3)**
   - **Van Krevelen diagram:** O/C vs H/C scatter with bio-oil yield colormap
   - **Ternary C-H-O plot:** Barycentric composition of feedstocks
   - **Yield-vs-Temperature:** Line plot with pressure grouping (requires sweep)
   - Matplotlib output to PNG; graceful fallback if columns missing

7. **Reporting & Export**
   - Results DataFrame with condition columns (T_K, T_°C, P_Pa, P_bar)
   - Feedstock composition (C, H, O, N, S daf%)
   - Yield breakdown (oil, gas, char kg/kg, efficiency ratio)
   - Warnings and solver diagnostics
   - Export to Excel (multiple sheets: results, unmatched, parse warnings, solver warnings)
   - Optional plot export to PNG directory

#### ⏳ In Progress / Deferred
1. **Phase 4: Kinetic Correction Factors** (Not yet implemented)
   - Empirical kinetic model to adjust equilibrium yields for real fast-pyrolysis conditions
   - Literature-fit aging factors for heating rate and residence time
   - Expected to bridge gap between theoretical (equilibrium) and experimental yields

2. **Phase 5: Expanded Test Coverage**
   - Further edge cases for kinetics and literature correlations

---

## 2. STRENGTHS

### 2.1 Architecture & Code Quality
- **Modular design:** Clear separation of concerns (parsing, thermo, optimization, reporting)
- **Type safety:** Extensive use of dataclasses and type hints for maintainability
- **Error resilience:** Comprehensive try-except wrapping; failures log warnings rather than crash
- **Backward compatibility:** New features (sweep, plotting) are opt-in; defaults work for single-point runs
- **Config-driven:** All major parameters exposed in configuration layer; easy to tune without code edits

### 2.2 Thermodynamic Soundness
- **Established correlations:** Channiwala-Parikh HHV model is industry-standard
- **Element balance enforcement:** Explicit stoichiometric constraints in optimization
- **Multi-phase equilibrium:** Simultaneous gas + liquid + solid treatment (more realistic than sequential)
- **Diagnostics:** Residual tracking, convergence flags, and warning codes provide traceability

### 2.3 Data Quality & Traceability
- **Metadata preservation:** References, suitability, regionality retained end-to-end
- **Warning taxonomy:** Structured warning codes (>10 types) for reproducibility
- **Fallback transparency:** When generic bio-oil or default assumptions are used, explicit warning issued
- **Parser assistance:** Multi-tier matching reduces unmatched mappings from initial parse

### 2.4 Usability & Reproducibility
- **End-to-end automation:** Single function call triggers parse → thermo → solve → plot → export
- **Sweep capability:** Parametric studies across T/P without manual looping
- **Visualization:** Three plot types auto-generated; publication-ready PNG output
- **Test coverage:** 20 unit tests validate fuzzy matching, sweep grid, plotting, export

### 2.5 Extensibility
- **Plugin architecture for species:** Registry pattern allows adding custom gas/liquid candidates
- **Bio-oil mapping tier system:** Easy to add new synonym groups or fine-tune Levenshtein threshold
- **Plotting modular:** New chart types can be added without restructuring export pipeline

---

## 3. ISSUES & LIMITATIONS

### 3.1 **Critical Gap: No Container Ship Oil Reference Data**
**Severity:** 🔴 **High** — Blocks comparison goal  
**Issue:** The workflow calculates bio-oil yields from biomass but has **no representation of standard marine fuel oil** (HFO, MGO, or marine distillate).

**Impact:**
- Cannot compare feedstock-derived bio-oil composition/heating value to conventional marine fuel
- No basis for normalizing efficiency or cost/energy metrics
- Cannot assess blendability or compatibility with existing ship fuel infrastructure

**Recommendation:** 
- Create a reference database of marine fuel standards (ISO 8217 HFO, MGO, marine diesel)
- Add `RefFuelOilRecord` and static properties for comparison
- Refactor reporting to include side-by-side comparison columns

---

### 3.2 **Entropy Estimation: Heuristic Fallback, Not Calibrated** 
**Severity:** 🟡 **Medium** — Affects accuracy of Gibbs e
nergy  
**Issue:** Biomass and bio-oil absolute entropy is estimated using a heuristic factor, not validated against literature.

```python
# Current: Heuristic from biomass_pyrolysis_equilibrium/thermodynamics/properties.py
factor = 0.85 + 0.25 * max(0.0, min(2.0, oxygenation_ratio))
s_abs = 8.314462618 * total_atom_moles * factor
```

**Impact:**
- ΔG_f accuracy depends on entropy; if entropy is off, optimal T/P predicted may be wrong
- Relative yields between feedstocks may be skewed
- Comparison to ship fuel oil requires confident entropy estimates

**Note:** Code includes warning `ENTROPY_FALLBACK_HEURISTIC` to flag usage.

**Recommendation:**
- Calibrate against literature correlations (e.g., Benson group contribution, NIST DIPPR)
- Cross-validate ΔG_f predictions against experimental pyrolysis yields
- Document entropy confidence interval in outputs

---

### 3.3 **Generic Bio-Oil Fallback: Inflexible Composition**
**Severity:** 🟡 **Medium** — Affects 10-20% of feedstocks  
**Issue:** When a feedstock cannot be matched to an experimental bio-oil record, a generic fallback is used:
```python
generic_bio_oil_formula: Dict[str, float] = {"C": 8.0, "H": 8.0, "O": 3.0, "N": 0.0, "S": 0.0}
```

This is a **fixed pseudo-molecule**, not adaptive to feedstock composition.

**Impact:**
- Bio-oil yield predictions for unmatched feedstocks may be significantly off
- E.g., high-N biomass might have high-N bio-oil, but generic formula has N=0
- Reduces confidence in comparative studies if many feedstocks use fallback

**Current Transparency:** Warning code `BIO_OIL_NO_MATCH_USING_FALLBACK` issued; count visible in output.

**Recommendation:**
- Implement **feedstock-adaptive bio-oil**: Generate expected composition from feedstock ultimate analysis directly (e.g., assume 80-90% feedstock composition passes through to oil)
- Cluster historical bio-oil data by feedstock category and compute category means
- Add configuration knob to control fallback strategy

---

### 3.4 **Phase 4 Not Yet Implemented: No Kinetic Corrections**
**Severity:** 🟡 **Medium** — Gap between theory and practice  
**Issue:** Current solver returns thermodynamic equilibrium yields (infinite time). Real fast pyrolysis has:
- Finite residence time (often <2s)
- High heating rates
- Quenching effects that preserve bio-oil before further cracking

**Impact:**
- Predicted yields often overestimate gas and underestimate liquid oil compared to experiments
- Comparison to marine fuel oil may be misleading if yields are high-biased
- Cannot model industrial process conditions

**Note:** Phase 4 is designed but not yet implemented. Planned approach:
- Empirical correction factors as function of heating rate, pressure, residence time
- Literature-fit model (e.g., from Bridgwater, Lédé, or equivalent studies)

**Recommendation:** 
- Prioritize Phase 4 implementation if accuracy relative to ship fuel is critical
- Or, accept current output as "theoretical upper bound" on bio-oil yield

---

### 3.5 **Temperature-Pressure Grid: Fixed Geom
etry, Not Adaptive**
**Severity:** 🟢 **Low** — Minor UX issue  
**Issue:** Sweep uses uniform linspace grid (11×5 = 55 points by default).

**Limitation:**
- No adaptive refinement near optimal regions
- No logarithmic or custom spacing for pressure (1–5 bar linear may miss detail at low P)
- 27,445 rows for 499 feedstocks at full grid = slow for large scans (but manageable in ~2–3 min)

**Recommendation:**
- Not urgent; current setup is fine for screening
- Future: Consider nonuniform grid or local optimization around max-yield point

---

### 3.6 **Solver Convergence: No Guaranteed Global Optimum**
**Severity:** 🟡 **Medium** — Local minima risk  
**Issue:** scipy.optimize.minimize with SLSQP can converge to local minima, especially with non-convex Gibbs landscape.

**Mitigation in Place:**
- Multi-start initialization (3 attempts by default)
- Residual tracking to flag under-convergence
- Warning codes issued if max_residual > tolerance

**Impact:**
- Some feedstocks may report sub-optimal yields
- Comparison studies sensitive to initial guess quality

**Recommendation:**
- Add global optimization option (e.g., scipy.optimize.differential_evolution or dual-annealing)
- Configure multi-start attempts per data quality (more for uncertain inputs)
- Log convergence stats in output for review

---

### 3.7 **No Sensitivity Analysis or Uncertainty Quantification**
**Severity:** 🟡 **Medium** — Reproducibility & confidence  
**Issue:** Output is point estimates; no error bars or sensitivity to input variations.

**Example:**
- If feedstock C% is uncertain (e.g., 48±3%), how does yield vary?
- Entropy heuristic produces yield spread of several %?

**Impact:**
- Hard to assess significance of differences between feedstocks
- Comparison to marine fuel oil precision depends on fuel spec tolerance

**Recommendation:**
- Add Monte Carlo sweep over feedstock composition uncertainty
- Propagate uncertainty through thermo calcs → final yields
- Output confidence intervals or sensitivity indices

---

### 3.8 **Missing Documentation: Key Assumptions Hidden in Code**
**Severity:** 🟡 **Medium** — Onboarding & audit trail  
**Issue:** Major assumptions buried in implementation:
- Generic bio-oil formula (hard-coded in `bio_oil.py`)
- Entropy heuristic constants (in `properties.py`)
- Species pool defaults (in `registry.py`)
- Min moles threshold (1e-12 in `config.py`)

**Impact:**
- New users or auditors must read code to understand modeling choices
- Hard to argue reproducibility or defend assumptions in papers/reports

**Recommendation:**
- Create **ASSUMPTIONS.md** documenting all fallback values, heuristics, and their rationale
- Add code comments with references to literature or internal notes
- Version assumptions alongside config

---

### 3.9 **Limited Quality Metrics for Comparison**
**Severity:** 🟡 **Medium** — Goal-specific gap  
**Issue:** Current output includes yields (oil, gas, char) and efficiency, but lacks metrics relevant to marine fuel context:
- Heating value (energy density relative to marine fuel)
- Viscosity (rough estimate from composition could help)
- Cetane number or distillation range (critical for ignition)
- Environmental metrics (flash point, pour point, sulfur)
- Compatibility with existing fuel infrastructure

**Impact:**
- Cannot directly assess "is this bio-oil suitable as ship fuel or blend component?"
- Requires post-processing in external tools

**Recommendation:** (See Section 4)

---

## 4. ASSESSMENT FOR GOAL: "COMPARE BIOMASS BIO-OIL TO CONTAINER SHIP FUEL OIL"

### 4.1 Current Capability
**What the tool can tell you:**
- ✅ Theoretical maximum bio-oil yield per biomass type (kg bio-oil per kg biomass)
- ✅ Heating value (HHV, LHV) of bio-oil estimated from composition
- ✅ Elemental analysis (C%, H%, O%, N%, S% daf) of bio-oil
- ✅ Efficiency ratio (useful output / total energy input)
- ✅ Temperature-pressure optimization (where yield is highest)
- ✅ Visual grouping (Van Krevelen, ternary, yield trends)

**What it cannot directly tell you:**
- ❌ How bio-oil elemental properties map to marine fuel quality metrics (cetane, viscosity, flash point)
- ❌ How bio-oil performs relative to ISO 8217 standards for marine fuel
- ❌ Blendability with marine diesel or HFO
- ❌ Kinetics: actual yield under fast-pyrolysis conditions (requires Phase 4)
- ❌ Cost comparison, scalability, or implementation barriers

### 4.2 Gap Analysis

| Capability | Current | Needed | Effort |
|-----------|---------|--------|--------|
| Biomass feedstock data | ✅ Loaded from Excel | — | — |
| Thermo property calc | ✅ Complete | — | — |
| Bio-oil yield prediction | ✅ Equilibrium | 🟡 Kinetic correction | Medium (Phase 4) |
| Marine fuel reference | ❌ None | ✅ ISO 8217 data | Low–Medium |
| Bio-oil → fuel metrics | ❌ None | ✅ Composition → cetane, viscosity, etc. | Medium |
| Comparison frontend | ❌ None | ✅ Side-by-side tables, radar charts | Low |
| Blending study | ❌ None | ⚠️ Optional; nice-to-have | Medium |
| Supply-chain analysis | ❌ None | ⚠️ Optional; meta-analysis | High |

### 4.3 Specific Recommendations to Enable Comparison

#### **Step 1: Add Marine Fuel Reference Data (Low Effort, High Value)**
Create a new reference module with ISO 8217 marine fuel properties:

```python
# biomass_pyrolysis_equilibrium/reference/marine_fuels.py

@dataclass
class MarineFuelProfile:
    """ISO 8217 or typical marine fuel specification."""
    name: str                    # e.g., "ISO 8217 HFO 180"
    c_pct: float                 # ~86–87%
    h_pct: float                 # ~11–12%
    o_pct: float                 # ~0–1%
    s_pct_max: float             # Varies by grade
    kin_viscosity_cst_at_40c: float
    cetane_number: float         # If distillate
    flash_point_c: float
    heating_value_mj_per_kg: float
    regionality: str             # "ISO Standard"
    reference: str
```

Add a reference database:
```python
MARINE_FUEL_PROFILES = {
    "ISO8217_HFO180": MarineFuelProfile(...),
    "ISO8217_MGO": MarineFuelProfile(...),
    "ISO8217_MDO": MarineFuelProfile(...),
}
```

Then in reporting, add comparison columns:
```python
"bio_oil_heating_value_vs_hfo": bio_oil_lhv / hfo_lhv,
"bio_oil_c_concentration_vs_hfo": bio_oil_c_pct / hfo_c_pct,
# ... etc
```

#### **Step 2: Implement Quality Metric Estimators (Medium Effort)**
Use composition-based empirical models to estimate marine fuel properties from C, H, O, N, S:

```python
# biomass_pyrolysis_equilibrium/qa/fuel_metrics.py

def estimate_density_kg_per_m3(c_pct, h_pct, o_pct) -> float:
    """Estimate fuel density from elemental composition (ASTM correlation)."""
    # Reference: ASTM D2219 or similar
    return ~800 + 10 * o_pct - 5 * h_pct  # Approximate

def estimate_cetane_number(c_pct, h_pct, aromatic_pct_est) -> float:
    """Rough cetane estimate from composition and aromaticity."""
    # Simplified; real cetane depends on molecular structure
    return 45 + 0.5 * c_pct - 0.8 * aromatic_pct_est

def estimate_viscosity_cst(mw_g_per_mol, temp_c=40) -> float:
    """ASTM viscosity estimate from pseudo-molecular weight."""
    # Heuristic; accurate only within family
    return 2 + 0.02 * mw_g_per_mol

def estimate_flash_point_c(c_pct, h_pct, o_pct, lhv_mj_per_kg) -> float:
    """Flash point estimate (correlation from open literature)."""
    return 100 + 2 * lhv_mj_per_kg - 1.5 * o_pct
```

These are rough; refine with literature or own experimental data.

#### **Step 3: Create Comparison Report Module (Low Effort, High Value)**
```python
# biomass_pyrolysis_equilibrium/qa/marine_fuel_comparison.py

def compare_biooil_to_marine_fuel(
    results_df: pd.DataFrame,
    reference_fuel: MarineFuelProfile = MARINE_FUEL_PROFILES["ISO8217_HFO180"]
) -> pd.DataFrame:
    """Augment results DataFrame with marine fuel comparison metrics."""
    
    df = results_df.copy()
    
    # Heating value ratio
    df["heating_value_ratio_to_fuel"] = df["estimated_lhv"] / reference_fuel.heating_value_mj_per_kg
    
    # Elemental alignments
    df["c_concentration_diff_pct"] = df["feedstock_c_pct_daf"] - reference_fuel.c_pct
    df["h_concentration_diff_pct"] = df["feedstock_h_pct_daf"] - reference_fuel.h_pct
    df["o_concentration_excess_pct"] = df["feedstock_o_pct_daf"] - reference_fuel.o_pct  # O is problematic in fuels
    
    # Estimated fuel quality scores
    df["estimated_density_kg_m3"] = estimate_density_kg_per_m3(...)
    df["estimated_cetane_number"] = estimate_cetane_number(...)
    df["estimated_viscosity_cst"] = estimate_viscosity_cst(...)
    
    # "Suitability score" (0=incompatible, 1=excellent)
    df["marine_fuel_suitability_score"] = (
        (1 - np.clip(df["o_concentration_excess_pct"] / 5, 0, 1)) *  # Penalize oxygen
        (np.clip(df["heating_value_ratio_to_fuel"], 0.8, 1.0)) *    # Penalize if <80% HV
        (1 - np.clip(abs(df["c_concentration_diff_pct"]) / 10, 0, 1)) # Penalize if C% way off
    )
    
    return df
```

#### **Step 4: Extend Plotting (Low Effort, Immediate Insight)**
Add a radar chart or box plot comparing bio-oil vs. standard fuel:

```python
# biomass_pyrolysis_equilibrium/qa/plotting.py

def _plot_comparison_radar(
    results_df: pd.DataFrame,
    reference_fuel: MarineFuelProfile,
    title: str = "Bio-Oil vs. Marine Fuel (ISO 8217 Reference)"
) -> None:
    """Radar chart: Bio-Oil Properties vs. Fuel Standard."""
    # normalized metrics on 0–1 scale
    # Show both individual feedstocks and aggregate
    # Reference fuel as outer ring for easy visual comparison
```

#### **Step 5: Update Tutorial (Minimal Effort)**
```python
# tutorial.py additions

from biomass_pyrolysis_equilibrium.qa.marine_fuel_comparison import compare_biooil_to_marine_fuel
from biomass_pyrolysis_equilibrium.reference.marine_fuels import MARINE_FUEL_PROFILES

# After export_run_result(...)
comparison_df = compare_biooil_to_marine_fuel(
    results_df,
    reference_fuel=MARINE_FUEL_PROFILES["ISO8217_HFO180"]
)
comparison_df.to_excel("bio_oil_vs_marine_fuel_comparison.xlsx", index=False)
print(f"Comparison report written to bio_oil_vs_marine_fuel_comparison.xlsx")
```

### 4.4 Information Gaps (Requires External Data or Validation)

To enable a **rigorous** comparison, you'll need:

1. **Experimental bio-oil composition data** from literature or your own pyrolysis trials
   - Reference heating values for bio-oils
   - Viscosity, density, flash point measurements
   - Distillation curves or boiling-point ranges

2. **Marine fuel property correlations**
   - ISO 8217 specifications (publicly available)
   - ASTM standards for density, viscosity, cetane number
   - Blending rules (e.g., ASTM D2786 for viscosity blends)

3. **Kinetic data for industrial pyrolysis**
   - Residence time, heating rate, quench strategy
   - Literature yields for representative feedstocks
   - To validate/calibrate Phase 4 kinetic corrections

4. **Cost & scalability data** (if economic comparison needed)
   - Feedstock cost and availability
   - Pyrolysis capital/operating cost benchmarks
   - Shipping fuel market prices

---

## 5. NEXT STEPS & RECOMMENDATIONS

### 5.1 **Priority 1: Immediate (If Comparison Goal is Urgent)**

- **Add marine fuel reference database** (1–2 hours)
  - ISO 8217 HFO, MGO, MDO profiles
  - Store in `reference/marine_fuels.py`

- **Implement fuel metric estimators** (2–4 hours)
  - Empirical models for density, cetane, viscosity, flash point
  - Base on ASTM correlations or literature
  - Store in `qa/fuel_metrics.py`

- **Create comparison report** (1–2 hours)
  - Extend reporting to include side-by-side columns
  - Suitability scoring logic
  - Export to "bio_oil_vs_fuel_comparison.xlsx"

- **Update plotting** (1–2 hours)
  - Add radar or box plots for visual comparison
  - Include reference fuel boundary

**Total Effort:** ~5–10 hours  
**Outcome:** Direct answer to "How does bio-oil stack up against marine fuel oil?"

---

### 5.2 **Priority 2: Near-term (For Accuracy & Credibility)**

- **Complete Phase 4: Kinetic Corrections** (8–16 hours)
  - Research literature on fast-pyrolysis kinetics
  - Implement empirical or machine-learning correction factors
  - Validate against known experimental data
  - Reduces gap between theoretic and real yields

- **Calibrate entropy model** (4–8 hours)
  - Replace heuristic with literature correlation
  - Cross-check ΔG_f against experimental yields
  - Document confidence intervals

- **Expand test coverage** (4–6 hours)
  - Edge cases for kinetics, bio-oil fallback
  - Sensitivity tests for key parameters
  - Comparison validation (e.g., "bio-oil vs. marine fuel should show X% difference")

**Total Effort:** ~16–30 hours  
**Outcome:** Higher confidence in absolute yields; defensible in research publications

---

### 5.3 **Priority 3: Medium-term (For Robustness)**

- **Implement adaptive bio-oil fallback** (4–6 hours)
  - Feedstock-specific or category-specific default compositions
  - Reduces generic formula bias

- **Add global optimization pathway** (2–4 hours)
  - Optional scipy global solvers (differential evolution, basin-hopping)
  - For uncertain or non-convex problems

- **Sensitivity & uncertainty analysis** (6–10 hours)
  - Monte Carlo sweep over input uncertainties
  - Gradient-based sensitivity indices
  - Confidence intervals on outputs

- **Documentation audit** (2–4 hours)
  - ASSUMPTIONS.md with all fallbacks and their sources
  - Code comments with references
  - Developer guide for extending model

**Total Effort:** ~14–24 hours  
**Outcome:** Production-grade tool; audit-ready; extensible

---

### 5.4 **Priority 4: Optional / If Time Permits**

- Blending study framework (e.g., "optimal bio-oil/marine fuel mix for performance X")
- Multi-objective optimization (e.g., maximize yield + minimize N/S content)
- Flowsheet integration with realistic pyrolysis reactor model
- Supply-chain / life-cycle analysis (LCA) framework

---

## 6. CODE QUALITY RATING

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Architecture** | ⭐⭐⭐⭐⭐ | Modular, extensible, clean separation of concerns |
| **Thermodynamics** | ⭐⭐⭐⭐☆ | Sound fundamentals; entropy heuristic pending calibration |
| **Data Quality** | ⭐⭐⭐⭐⭐ | Excellent traceability, metadata, fallback transparency |
| **Testing** | ⭐⭐⭐⭐☆ | Good unit coverage (20 tests); edge cases could expand |
| **Documentation** | ⭐⭐⭐☆☆ | README & formulations.md exist; ASSUMPTIONS, developer guide missing |
| **Usability** | ⭐⭐⭐⭐☆ | Easy to run; lacks comparison frontend for stated goal |
| **Production Readiness** | ⭐⭐⭐⭐☆ | Nearly ready; Phase 4 kinetics needed for industrial use |

**Overall Assessment:**  
This is a **well-engineered, research-grade tool** with strong thermodynamic foundations. It successfully models biomass pyrolysis equilibrium and generates publication-quality outputs. However, **it is not yet positioned for direct marine fuel comparison** — that requires reference data and quality estimators (achievable in ~5–10 hours). Phase 4 kinetics are planned and will significantly increase real-world accuracy.

---

## 7. SUMMARY TABLE: STRENGTHS vs. LIMITIATIONS

| Dimension | Strength or Limitation? | Details |
|-----------|------------------------|---------|
| **Modularity** | ✅ Strength | Easy to maintain, extend, or fork |
| **Thermodynamics** | ✅ Strength | Industry-standard correlations, multi-phase solver |
| **Data Handling** | ✅ Strength | Robust CSV/range parsing, full metadata trail |
| **Fuzzy Matching** | ✅ Strength (Phase 1) | Reduces unmapped species significantly |
| **Sweep & Grid** | ✅ Strength (Phase 2) | Temperature-pressure parametrics built-in |
| **Visualization** | ✅ Strength (Phase 3) | Van Krevelen, ternary, trend plots auto-generated |
| **Entropy Model** | ❌ Limitation | Heuristic only; should be calibrated |
| **Generic Bio-Oil** | ❌ Limitation | Fixed fallback; not adaptive to feedstock |
| **Kinetics** | 🟡 Gap | Phase 4 not yet implemented |
| **Marine Fuel Comparison** | ❌ Gap | No reference fuel data or metrics |
| **Sensitivity Analysis** | ❌ Limitation | No uncertainty quantification |
| **Convergence Guarantee** | ⚠️ Risk | Local optima possible; multi-start mitigates |
| **Performance** | ✅ Strength | 27K rows in 2–3 min; acceptable for screening |

---

## 8. FINAL RECOMMENDATION

**For your goal of "comparing biomass bio-oil to container ship fuel oil,"** I recommend a **3-phase approach:**

1. **Now (Week 1):** Add marine fuel reference data + comparison metrics (Low hanging fruit; ~8–10 hours)
2. **Next (Week 2–3):** Implement Phase 4 kinetics + calibrate entropy (Medium effort; ~20–30 hours; significant accuracy gain)
3. **Future:** Sensitivity analysis, documentation polish, extended validation

This keeps you moving toward your goal while addressing the most impactful accuracy gaps. The codebase is well-positioned to support these extensions.

---

**Document created:** April 2026 | **Status:** Analysis Complete | **Next Action:** Prioritize Phase 1 (marine fuel ref data)
