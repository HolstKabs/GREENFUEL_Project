# Goal and Scope

## Goal

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
### Modelling framework and decision context

Cut-off and decision context is Situation A - Micro level.

### System Boundary

As this report will be dynamically modelling several biomass types and calculating the impacts, the biomass types have been categorized to create category-type-specific LCI modelling. This results in not one specific system boundary but several, thus a section for each biomass category can be read in section "Biomass_categories_specific_LCI.md."

### Geographical, temporal and technological representativenes

Background modelling with mostly generic processes provided by the EcoInvent database will be used for an assumption-based study.
- **Geographical transportation:** accounted for average distance to nearest biomass production site, generalized for all biomass categories, potential and need to distinguish between feedstock types for more accurate results
- **Temporal:** Data will be acquired with the most recent processes from the EcoInvent database, thus leading to most likely process modelled without foreground modelling.
- **Technological:** Based on a general fast-pyrolysis process. A **light bio-oil stabilization** step (mild hydrodeoxygenation/deacidification: small H2, electricity and heat inputs) is included before marine use; heavy upgrading (hydrotreating/hydrocracking/distillation) is still excluded, as marine combustion engines are expected to handle lightly stabilized bio-oil. Mass loss in stabilization is currently assumed negligible.

### Basis for Impact Assessment

This report will be using Brightway2.5 and EcoInvent Database 3.12 to model and calculate potential impacts of the described scope of system. The chosen LCIA method is **xxx** where both midpoint and endpoint categories will be scrutinized to focus on four impact categories, which will ultimately, be presented and interpreted in this report. A table with results for all impact categories will be provided in the supplementary data.

### Reporting of results

To be used for internal purposes and for a web application showing the potential impacts when choosing different biomass types. The results will be a comparable table where the reader can see how far we can transport a full container ship, fuelled with xx tonnes of biomass and how high. the four chosen, environmental impacts is going to be for each scenario.

# LCI of biomass conversion with pyrolysis process to bio-oil

## LCI modelling

The unit processes in the system boundary were benchmarked against the 58-study review of fast-pyrolysis
LCAs (Elkhalifa et al., 2024, *Bioresource Technology Reports*; supplementary Table A.1). Each FU
(1 MJ usable bio-oil) now includes, per category:

- **Raw material:** category-specific feedstock supply (kept category-specific: Wood = sawmill wood-chip
  production; Agricultural wastes = straw/biowaste; Residues = post-consumer waste wood / biowaste) and
  on-site feedstock storage (silo, amortised).
- **Pre-treatment:** feedstock drying (heat, scales with as-received moisture) and comminution / size
  reduction (electric chipper).
- **Conversion:** electricity, process heat (RER industrial furnace), process water, and pyrolysis-plant
  infrastructure (capital-goods proxy).
- **Bio-oil stabilization (Ph2b):** light stabilization — H2 + electricity + heat (see Technological note).
- **Transport:** feedstock, bio-oil and bio-char road freight, plus bio-oil tank storage (amortised).
- **Use (marine):** combustion modelled as foreground biosphere emissions — biogenic CO2
  (`Carbon dioxide, non-fossil`, GWP CF = 0) + NOx / CO / NMVOC / PM scaled from a marine-engine proxy
  (`diesel, burned in fishing vessel`); SO2/SOx scaled ×0.10 for low-sulfur bio-oil. No fossil CO2.
- **Co-product credits (Ph5):** syngas heat credit (avoided natural-gas heat, capped at internal demand);
  **biochar carbon-sequestration credit** — char is spread on soil (proxy: solid manure spreading) and
  the recalcitrant carbon is credited as `Carbon dioxide, to soil or biomass stock` (ReCiPe 2016 midpoint
  GWP CF = −1), amount = c × 0.80 (C fraction) × 0.80 (100-yr stable fraction) × 44/12. This is a
  system-expansion element applied uniformly across all three categories; report GWP **with and without**
  the biochar credit so its (potentially dominant) contribution is transparent.


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