# LCI modelling for each category

This document defines category-specific LCI models for a comparable functional unit:

- FU = 1 MJ usable bio-oil delivered for marine fuel use

The goal is to test whether higher bio-oil yield from each biomass category also leads to lower impact per FU.

> **Changing values:** all default parameters, transport distances, and energy intensities are defined in the *Biomass_Selection* and *Parameters* sheets of `LCA_process_config.xlsx`. Edit values there — not in the notebook.

---

## Shared parameter set (all categories)

The model parameters and FU equations are the same across all three biomass categories. What differs between categories are the default values assigned to those parameters — see the per-category tables below.

| Parameter | Symbol | Unit | Description |
|---|---|---|---|
| Bio-oil yield | x | % | Yield of bio-oil from selected biomass |
| HHV bio-oil | T | MJ/kg oil | HHV of produced bio-oil; used in FU normalisation |
| Pyrolysis temperature | T_py | °C | Scenario parameter linked to yield and energy demand |
| Biomass per FU | y | kg/FU | Biomass required to deliver 1 MJ usable bio-oil |
| Energy basis | w | J/FU | Energy linked to FU normalisation |
| Bio-oil per FU | z | kg/FU | Produced bio-oil mass per FU |
| Bio-char per FU | c | kg/FU | Co-product bio-char mass per FU |
| Syngas per FU | g | kg/FU | Co-product syngas mass per FU |
| Electricity intensity | k_el | kWh/kg biomass | Electricity demand of pyrolysis per kg dry biomass |
| Heat intensity | k_th | MJ/kg biomass | Process heat demand of pyrolysis per kg dry biomass |
| Feedstock transport distance | d1 | km | Feedstock to pyrolysis plant |
| Bio-oil transport distance | d2 | km | Pyrolysis plant to port / end use |
| Co-product transport distance | d3 | km | Bio-char to soil amendment site |

**FU equations:**

- z = 1 / T &nbsp;&nbsp;[kg oil/FU]
- y = z / (x/100) &nbsp;&nbsp;[kg biomass/FU]
- w = z × T × 10⁶ &nbsp;&nbsp;[J/FU]
- c and g are scenario-specific [kg/FU] from yield results
- Transport work feedstock = d1 × (y/1000) &nbsp;&nbsp;[tonne-km/FU]
- Transport work bio-oil = d2 × (z/1000) &nbsp;&nbsp;[tonne-km/FU]
- Transport work co-products = d3 × ((c + g)/1000) &nbsp;&nbsp;[tonne-km/FU]

## System phases (all categories)

1. Raw material supply (category-specific feedstock production and handling)
2. Conversion (pyrolysis to bio-oil, char, syngas)
3. Transportation (feedstock, bio-oil, co-products)
4. Use phase (marine combustion of bio-oil)
5. Co-product credits (avoided heat from syngas; biochar carbon sequestration)

---

## Category-specific default values

The table below shows what differs between categories. All values come from the *Biomass_Selection* sheet of `LCA_process_config.xlsx`.

| Parameter | Wood | Agricultural wastes | Residues and wastes |
|---|---|---|---|
| k_el (kWh/kg biomass) | 0.15 | 0.18 | 0.15 |
| k_th (MJ/kg biomass) | 0.75 | 0.90 | 0.75 |
| d1 — feedstock transport (km) | 50 | 100 | 75 |
| d2 — bio-oil transport (km) | 100 | 150 | 100 |
| d3 — co-product transport (km) | 150 | 200 | 100 |
| Feedstock supply proxy | Sawmill wood chips (hardwood/softwood) | Straw market (dry) / biowaste market (fruit/olive) | Post-consumer waste wood (mill residues) / biowaste (fruit/seed) |

**Rationale for differences:**
- Agricultural wastes use slightly higher energy intensities (k_el, k_th) due to greater moisture variability and denser material handling.
- Transport distances reflect the typical collection radius for each feedstock type: wood from nearby forestry/sawmills, agricultural residues from a wider farm catchment, and industrial residues from short-haul industrial collection.
- The feedstock supply proxy differs because each category has a distinct origin in ecoinvent 3.12 — see the *LCI_Mapping* sheet of `LCA_process_config.xlsx` for the exact process names and locations used in the model.
