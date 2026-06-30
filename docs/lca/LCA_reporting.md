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

## LCI modelling

> **Config file:** all ecoinvent process names, amount formulas and default parameter values are stored in `LCA_PROJECT/Project biomass/LCA_process_config.xlsx` (sheets: *Biomass_Selection*, *Parameters*, *LCI_Mapping*). The notebook reads this file at runtime; edits to process selection or default values should be made there, not in the notebook.

The foreground LCI is structured in six phases, applied uniformly across all three biomass categories per 1 MJ usable bio-oil (FU). Key derived quantities: **y** = kg dry biomass per FU; **z** = kg bio-oil per FU; **c** = kg bio-char per FU; **g** = kg syngas per FU.

### Ph1 — Raw material supply

Category-specific feedstock process (ecoinvent 3.12):

| Category | Default ecoinvent process | Location |
|---|---|---|
| Wood | `wood chips production, hardwood, at sawmill` (softwood alt. for spruce/pine/fir) | Europe w/o CH |
| Agricultural wastes | `market for straw` (dry residues) / `market for biowaste` (fruit/olive residues) | RER / RoW |
| Residues and wastes | `market for waste wood, post-consumer` (mill residues) / `market for biowaste` (fruit/seed) | RER / RoW |

Amount = **y** kg per FU. Feedstock on-site storage (tower silo, plastic) amortised at 1×10⁻⁵ m³ per kg biomass; expected negligible.

### Ph2 — Pre-treatment and pyrolysis conversion

- **Feedstock drying:** heat from industrial natural-gas furnace, `SEC_dry = 3 MJ / kg water evaporated`; applied only where as-received moisture exceeds the 10 wt% fast-pyrolysis target. Amount = `water_evap × 3.0` MJ per FU (zero for already-dry feedstocks).
- **Comminution:** electric wood chipper (`wood chipping, industrial residual wood, stationary electric chipper`, RER), amount = **y** kg per FU; used as a size-reduction proxy for non-wood categories.
- **Electricity:** `market group for electricity, medium voltage`, RER. Amount = `k_el × y` kWh per FU (default: 0.15 kWh/kg for Wood and Residues; 0.18 kWh/kg for Agricultural wastes).
- **Process heat:** `heat production, natural gas, at industrial furnace >100 kW`, Europe w/o CH. Amount = `k_th × y` MJ per FU (default: 0.75 MJ/kg for Wood and Residues; 0.90 MJ/kg for Agricultural wastes).
- **Process water:** `market for tap water`, Europe w/o CH. Amount = `0.05 × y` kg per FU (quenching and scrubbing).
- **Plant infrastructure:** `chemical factory construction, organics`, RER. Amount = `4×10⁻¹⁰ × z` units per FU (capital-goods proxy, ecoinvent organic-chemicals convention; negligible contribution).

### Ph2b — Bio-oil stabilisation

Light stabilisation (mild hydrodeoxygenation / deacidification) before marine use:

| Input | ecoinvent process | Amount |
|---|---|---|
| Hydrogen | `market for hydrogen, gaseous, low pressure`, RER | 0.01 × z kg/FU |
| Electricity | `market group for electricity, medium voltage`, RER | 0.02 × z kWh/FU |
| Process heat | `heat production, natural gas, at industrial furnace >100 kW`, Europe w/o CH | 0.10 × z MJ/FU |

Mass loss during stabilisation is assumed negligible.

### Ph3 — Transport and storage

Road freight (`market for transport, freight, lorry 7.5–16 t, diesel, EURO 6`, RER) for three flows:

| Flow | Distance (default) | Amount formula |
|---|---|---|
| Feedstock → pyrolysis plant | d1 (Wood 50 km / Agri. 100 km / Residues 75 km) | `d1 × (y / 1000)` tonne-km |
| Bio-oil → port / end use | d2 (Wood 100 km / Agri. 150 km / Residues 100 km) | `d2 × (z / 1000)` tonne-km |
| Bio-char → soil amendment | d3 (Wood 150 km / Agri. 200 km / Residues 100 km) | `d3 × (c / 1000)` tonne-km |

Bio-oil tank storage (`storage production, 10 000 l`, RER) amortised at 1×10⁻⁷ units per kg bio-oil; expected negligible.

### Ph4 — Use (marine combustion)

Combustion modelled as foreground biosphere flows (not linked to a background combustion process):

- **Biogenic CO₂:** `Carbon dioxide, non-fossil` (GWP CF = 0 in ReCiPe 2016), amount = `z × C_bio × 44/12` kg per FU (C_bio = 0.60 kg C/kg bio-oil).
- **NOx, CO, NMVOC, PM:** scaled from `diesel, burned in fishing vessel` proxy per MJ bio-oil.
- **SO₂/SOx:** diesel proxy value × 0.10 (bio-oil assumed ~10% of marine diesel sulfur content).
- Fossil CO₂ and diesel supply chain excluded.

### Ph5 — Co-product credits

**Syngas heat credit (avoided burden):**
- Gross available heat = `g × HHV_syn × η_comb` (HHV_syn = 12 MJ/kg; η_comb = 0.85).
- Credit = `−min(gross syngas heat, k_th × y)` MJ per FU — **capped at internal heat demand** to avoid crediting energy the plant does not actually displace externally. Surplus syngas beyond internal demand is not credited in the current model scope.
- Avoided process: `heat production, natural gas, at industrial furnace >100 kW`, Europe w/o CH.

**Biochar carbon-sequestration credit:**
- Biochar spread on soil (proxy: `solid manure loading and spreading, by hydraulic loader and spreader`, RoW), amount = **c** kg per FU.
- Sequestration credit added as biosphere flow `Carbon dioxide, to soil or biomass stock` (ReCiPe 2016 GWP CF = −1), amount = `c × 0.80 (C fraction) × 0.80 (100-yr stable fraction) × 44/12` kg CO₂ per FU.
- Applied uniformly across all three categories. **Report GWP with and without the biochar credit** — this credit can dominate the GWP result and its magnitude should be made explicit.


## Data collection and quality assessment
*Here we should insert the text from the script that writes the tables based on the processes used and the technological, temporal and geographical scores.*

## LCI results
Reference to excel sheet / table list of all the values calculated for each impact category at midpoint.

## Sensitivity and Uncertainty Analysis

- Bio-oil yield should be parameterized and have a monte carlo analysis to see the difference in results.
- HHV is mostly based on literature, so needs to be run with sensitivity.
- Pyrolysis temperatures
- biomass types as-received, dry, DAF, what will the consequences be if they biomass is in either "form"

Refer to Parameters.md section for a better explanation of used parameters for uncertainty and sensitivity analysis.