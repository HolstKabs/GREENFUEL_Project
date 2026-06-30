# Goal and Scope

## Goal

This study quantifies the life-cycle environmental performance of fast-pyrolysis bio-oil produced from nine biomass feedstocks as a potential drop-in marine fuel, with the aim of comparing it against conventional marine heavy fuel oil (HFO). The study is comparative and attributional in nature, following a Situation A micro-level decision context. Results are intended for internal research use at the Technical University of Denmark (DTU) and for public communication via the interactive web application at [https://greenfuelproject.streamlit.app/](https://greenfuelproject.streamlit.app/).

## Scope

### Functional Unit

> FU = 1 MJ of usable bio-oil for marine transportation based on European standards.

1 MJ of usable bio-oil has been calculated according to the bio-oil yield represented by the Thermodynamic Equilibrium of Biomass with the following equation:
>**Biomass required to deliver 1 MJ usable bio-oil (kg biomass per 1MJ):**
>
> $m_{bio}$ = $1/(y/100)*HHV$ 
>
> where **y** = bio-oil yield(wt$%), 
>
> **HHV** = Higher Heating Value (of produced bio-oil).

With this equation it's possible to calculate the required amount of biomass to produce 1 MJ of usable bio-oil.

### Reference flow

1 MJ of usable bio-oil delivered for marine propulsion. The required biomass input per functional unit is derived from the thermodynamic equilibrium bio-oil yield, which represents an upper bound on achievable yield; see the functional unit equation above.

### Modelling framework and decision context

Cut-off and decision context is Situation A - Micro level.

### System Boundary

As this report will be dynamically modelling several biomass types and calculating the impacts, the biomass types have been categorized to create category-type-specific LCI modelling. This results in not one specific system boundary but several, thus a section for each biomass category can be read in section "Biomass_categories_specific_LCI.md."

### Geographical, temporal and technological representativeness

Background modelling with mostly generic processes provided by the EcoInvent database will be used for an assumption-based study.
- **Geographical transportation:** accounted for average distance to nearest biomass production site, generalized for all biomass categories, potential and need to distinguish between feedstock types for more accurate results
- **Temporal:** Data will be acquired with the most recent processes from the EcoInvent database, thus leading to most likely process modelled without foreground modelling.
- **Technological:** Based on a general fast-pyrolysis process. A **light bio-oil stabilization** step (mild hydrodeoxygenation/deacidification: small H2, electricity and heat inputs) is included before marine use; heavy upgrading (hydrotreating/hydrocracking/distillation) is still excluded, as marine combustion engines are expected to handle lightly stabilized bio-oil. Mass loss in stabilization is currently assumed negligible.

### Basis for Impact Assessment

This study uses Brightway2.5 and the EcoInvent Database 3.12 (cutoff system model) to model and calculate potential impacts. The chosen LCIA method is **ReCiPe 2016 Midpoint (H)**. The following five impact categories are presented and interpreted in this report and in the web application:

| # | Impact category | Abbreviation | Unit |
|---|---|---|---|
| 1 | Global Warming Potential (100 yr) | GWP100 | kg CO₂-eq |
| 2 | Terrestrial Ecotoxicity Potential | TETP | kg 1,4-DCB-eq |
| 3 | Human Toxicity Potential (non-cancer) | HTPnc | kg 1,4-DCB-eq |
| 4 | Agricultural Land Occupation | LOP | m²·yr |
| 5 | Fossil Fuel Potential | FFP | MJ |

Full results across all 18 ReCiPe midpoint categories and 3 endpoint areas are available in the supplementary Excel workbooks in `LCA_PROJECT/Project biomass/LCA_results/`.

### Reporting of results

Results are published publicly at **[https://greenfuelproject.streamlit.app/](https://greenfuelproject.streamlit.app/)** across five interactive pages:

1. **Home** — project introduction and overview
2. **Biomass Xplorer** — browse and filter all feedstocks by yield and category
3. **Comparison** — side-by-side yield and property comparison across selected biomass types
4. **Environmental Impacts** — LCA results with Monte Carlo uncertainty ranges for each of the five impact categories
5. **Transportation of Goods** — scenario explorer showing how far a fully loaded container ship travelling from China to Denmark can sail when fuelled by bio-oil from each biomass type, compared against conventional HFO

Full numerical results per biomass type are available in the supplementary Excel workbooks.

# LCI of biomass conversion with pyrolysis process to bio-oil


> **Config file:** all ecoinvent process names, amount formulas and default parameter values are stored in `LCA_PROJECT/Project biomass/LCA_process_config.xlsx` (sheets: *Biomass_Selection*, *Parameters*, *LCI_Mapping*). The notebook reads this file at runtime; edits to process selection or default values should be made there, not in the notebook.

The foreground LCI is structured in six phases, applied uniformly across all three biomass categories per 1 MJ usable bio-oil (FU). Key derived quantities: **y** = kg dry biomass per FU; **z** = kg bio-oil per FU; **c** = kg bio-char per FU; **g** = kg syngas per FU.

### Ph1 — Raw material supply

Feedstock supply is category-specific. The feedstock process used for each biomass type is defined in the *LCI_Mapping* sheet of `LCA_process_config.xlsx`. Amount = **y** kg per FU. Feedstock on-site storage (tower silo) is amortised per kg biomass; expected negligible.

### Ph2 — Pre-treatment and pyrolysis conversion

- **Feedstock drying:** SEC_dry = 3 MJ / kg water evaporated; applied only where as-received moisture exceeds the 10 wt% fast-pyrolysis target. Amount = `water_evap × 3.0` MJ per FU (zero for already-dry feedstocks).
- **Comminution:** electric wood chipper, amount = **y** kg per FU; used as a size-reduction proxy for non-wood categories.
- **Electricity:** amount = `k_el × y` kWh per FU — see category parameter table below.
- **Process heat:** amount = `k_th × y` MJ per FU — see category parameter table below.
- **Process water:** amount = `0.05 × y` kg per FU (quenching and scrubbing); uniform across all categories.
- **Plant infrastructure:** capital-goods proxy, amortised at `4×10⁻¹⁰ × z` units per FU; negligible.

### Ph2b — Bio-oil stabilisation

Light stabilisation (mild hydrodeoxygenation / deacidification) before marine use. Amounts are uniform across all categories:

| Input | Amount per FU |
|---|---|
| Hydrogen | 0.01 × z kg |
| Electricity | 0.02 × z kWh |
| Process heat | 0.10 × z MJ |

Mass loss during stabilisation is assumed negligible.

### Ph3 — Transport and storage

Road freight for three flows. Distances are category-specific — see parameter table below.

| Flow | Amount formula |
|---|---|
| Feedstock → pyrolysis plant | `d1 × (y / 1000)` tonne-km |
| Bio-oil → port / end use | `d2 × (z / 1000)` tonne-km |
| Bio-char → soil amendment | `d3 × (c / 1000)` tonne-km |

Bio-oil tank storage is amortised at `1×10⁻⁷ units / kg bio-oil`; negligible.

### Ph4 — Use (marine combustion)

Combustion modelled as foreground biosphere flows:

- **Biogenic CO₂:** amount = `z × C_bio × 44/12` kg per FU (C_bio = 0.60 kg C/kg bio-oil; GWP CF = 0).
- **NOx, CO, NMVOC, PM:** scaled from marine-engine diesel proxy per MJ bio-oil.
- **SO₂/SOx:** diesel proxy value × 0.10 (bio-oil assumed ~10% of marine diesel sulfur content).
- Fossil CO₂ and diesel supply chain excluded.

### Ph5 — Co-product credits

**Syngas heat credit (avoided burden):**
- Gross available heat = `g × HHV_syn × η_comb` (HHV_syn = 12 MJ/kg; η_comb = 0.85).
- Credit = `−min(gross syngas heat, k_th × y)` MJ per FU — **capped at internal heat demand**. Surplus syngas beyond internal demand is not credited in the current model scope.

**Biochar carbon-sequestration credit:**
- Biochar spread on soil (proxy: solid manure spreading), amount = **c** kg per FU.
- Sequestration credit = `c × 0.80 (C fraction) × 0.80 (100-yr stable fraction) × 44/12` kg CO₂ per FU, added as biosphere flow `Carbon dioxide, to soil or biomass stock` (ReCiPe 2016 GWP CF = −1).
- Applied uniformly across all categories. **Report GWP with and without the biochar credit** — this credit can dominate the result and its contribution should be made explicit.

---

## Category parameters

All values sourced from the *Biomass_Selection* sheet of `LCA_process_config.xlsx`.

### Wood

| Biomass | Yield range | Bio-oil yield (kg/kg a.r.) | HHV bio-oil (MJ/kg) | Pyrolysis temp. (°C) | Moisture a.r. (wt%) | k_el (kWh/kg) | k_th (MJ/kg) | d1 (km) | d2 (km) | d3 (km) |
|---|---|---|---|---|---|---|---|---|---|---|
| Oak wood | Low (≤25%) | 0.2145 | 33.01 | 600 | 10.5 | 0.15 | 0.75 | 50 | 100 | 150 |
| Branches and leaves from poplar tree | Mid (45–55%) | 0.3984 | 17.11 | 575 | 6.2 | 0.15 | 0.75 | 50 | 100 | 150 |
| Poplar | High (≥75%) | 0.6619 | 17.11 | 350 | 0.1 | 0.15 | 0.75 | 50 | 100 | 150 |

### Agricultural wastes

| Biomass | Yield range | Bio-oil yield (kg/kg a.r.) | HHV bio-oil (MJ/kg) | Pyrolysis temp. (°C) | Moisture a.r. (wt%) | k_el (kWh/kg) | k_th (MJ/kg) | d1 (km) | d2 (km) | d3 (km) |
|---|---|---|---|---|---|---|---|---|---|---|
| Walnut shell | Low (≤25%) | 0.0494 | 23.92 | 600 | 0 | 0.18 | 0.90 | 100 | 150 | 200 |
| Peanut hulls | Mid (45–55%) | 0.1423 | 32.54 | 600 | 0 | 0.18 | 0.90 | 100 | 150 | 200 |
| Olive kernels | High (≥75%) | 0.6145 | 31.69 | 625 | 13.8 | 0.18 | 0.90 | 100 | 150 | 200 |

### Residues and wastes

| Biomass | Yield range | Bio-oil yield (kg/kg a.r.) | HHV bio-oil (MJ/kg) | Pyrolysis temp. (°C) | Moisture a.r. (wt%) | k_el (kWh/kg) | k_th (MJ/kg) | d1 (km) | d2 (km) | d3 (km) |
|---|---|---|---|---|---|---|---|---|---|---|
| Fir mill waste | Low (≤25%) | 0.1149 | 24.40 | 600 | 0 | 0.15 | 0.75 | 75 | 100 | 100 |
| Maple fruit | Mid (45–55%) | 0.3443 | 31.18 | 450 | 8.7 | 0.15 | 0.75 | 75 | 100 | 100 |
| Grape seeds | High (≥75%) | 0.6526 | 35.16 | 525 | 0 | 0.15 | 0.75 | 75 | 100 | 100 |


## Sensitivity and Uncertainty Analysis

- Bio-oil yield should be parameterized and have a monte carlo analysis to see the difference in results.
- HHV is mostly based on literature, so needs to be run with sensitivity.
- Pyrolysis temperatures
- biomass types as-received, dry, DAF, what will the consequences be if they biomass is in either "form"

Refer to Parameters.md section for a better explanation of used parameters for uncertainty and sensitivity analysis.
