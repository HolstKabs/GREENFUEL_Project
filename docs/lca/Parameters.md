# Parameters in the model

These parameters are used to conduct transferable LCA scenarios depending on the biomass type inputs, contribution analysis, and sensitivity analysis. For category-specific default values and system phase descriptions see `docs/lca/biomass_categories_specific_LCI.md`.

> **Changing values:** all default parameter values are defined in the *Biomass_Selection* and *Parameters* sheets of `LCA_process_config.xlsx`. Edit values there — not in the notebook.

---

## Parameter definitions

| Parameter | Symbol | Unit | Description |
|---|---|---|---|
| Bio-oil yield | x | % | Yield of bio-oil from selected biomass type |
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

---

## FU equations

All exchange amounts in the foreground LCI are derived from these equations:

- z = 1 / T &nbsp;&nbsp;[kg oil/FU]
- y = z / (x/100) &nbsp;&nbsp;[kg biomass/FU]
- w = z × T × 10⁶ &nbsp;&nbsp;[J/FU]
- c and g are scenario-specific [kg/FU] taken from yield results
- Transport work feedstock = d1 × (y/1000) &nbsp;&nbsp;[tonne-km/FU]
- Transport work bio-oil = d2 × (z/1000) &nbsp;&nbsp;[tonne-km/FU]
- Transport work co-products = d3 × ((c + g)/1000) &nbsp;&nbsp;[tonne-km/FU]
- Electricity for pyrolysis = k_el × y &nbsp;&nbsp;[kWh/FU]
- Process heat for pyrolysis = k_th × y &nbsp;&nbsp;[MJ/FU]

---

## Worked example

For a wood biomass with x = 66%, T = 17.11 MJ/kg, d1 = 50 km:

- z = 1 / 17.11 = 0.058 kg bio-oil per FU
- y = 0.058 / 0.66 = 0.088 kg biomass per FU
- Transport work feedstock = 50 × (0.088 / 1000) = 0.0044 tonne-km per FU
- Electricity = 0.15 × 0.088 = 0.013 kWh per FU
- Process heat = 0.75 × 0.088 = 0.066 MJ per FU
