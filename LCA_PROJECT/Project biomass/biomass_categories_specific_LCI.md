# LCI modelling for each category

This document defines category-specific LCI models for a comparable functional unit:

- FU = 1 MJ usable bio-oil delivered for marine fuel use

The goal is to test whether higher bio-oil yield from each biomass category also leads to lower impact per FU.

## Biomass category "WOOD"

### 1. Parameter set used for wood (aligned with Parameters.md)

Use one row of parameters per wood scenario (species, moisture basis, and technology assumptions).

| Parameter | Symbol in Parameters.md | Unit | Description |
|---|---|---|---|
| Bio-oil yield | x | % | Yield of bio-oil from selected wood type |
| HHV | T | MJ/kg oil | HHV used for the produced bio-oil in FU normalization |
| Pyrolysis temperature | T_py | degC | Technology/scenario parameter linked to yield and energy demand |
| Weight of biomass | y | kg/FU | Biomass required per FU |
| Energy of biomass (or delivered oil energy basis in model) | w | J/FU | Energy linked to FU normalization |
| Weight of bio-oil | z | kg/FU | Produced bio-oil mass per FU |
| Weight of bio-char | c | kg/FU | Co-product bio-char mass per FU |
| Weight of syngas | g | kg/FU | Co-product syngas mass per FU |
| Transport distance feedstock to pyrolysis | d1 | km | Wet wood transport |
| Transport distance oil to use/refining | d2 | km | Bio-oil transport |
| Transport distance co-product route (char/syngas) | d3 | km | Optional transport route for co-products |

Mass and transport per FU should be computed with these equations using your symbols:

- z = 1 / T [kg oil/FU], when T is in MJ/kg and FU = 1 MJ usable bio-oil
- y = z / (x/100) [kg biomass/FU]
- w = z * T * 1e6 [J/FU]
- c and g are scenario-specific co-product masses [kg/FU] (from literature/experimental data)
- Transport work feedstock = d1 * (y/1000) [tonne-km/FU]
- Transport work bio-oil = d2 * (z/1000) [tonne-km/FU]
- Transport work co-products = d3 * ((c + g)/1000) [tonne-km/FU]


### 2. System phases for wood

1. Raw material supply (wood production and handling)
2. Conversion (pyrolysis to bio-oil, char, syngas)
3. Transportation (feedstock, oil, optional co-products)
4. Use phase (combustion/use of bio-oil)
5. End-of-life and/or substitution credits for co-products

### 3. Tables of specific ecoinvent processes and foreground values

Use these as process candidates in ecoinvent 3.12 cutoff. Final choice must match geography and available process names in your database.

**Phase 1 - Raw materials (wood supply):**

| Name | Ecoinvent process (ecoinvent 3.12 cutoff) | Geography | Value (per FU) | Unit | Notes |
|---|---|---|---|---|---|
| Feedstock production — hardwood | `wood chips production, hardwood, at sawmill` | RER | y | kg | Primary choice for hardwood feedstock (e.g. beech, birch) |
| Feedstock production — softwood | `wood chips production, softwood, at sawmill` | RER | y | kg | Alternative for softwood feedstock (e.g. spruce, pine) |
| Feedstock — forest residues | `market for forest chips, green, from logging residues, measured as dry mass` | RER | y | kg | Use for residue/waste wood scenarios; adjust moisture handling |
| Forestry (hardwood) | `hardwood forestry, mixed species, sustainable forest management` | RER | y | kg | Upstream forestry if not included in sawmill dataset |
| Forestry (softwood) | `softwood forestry, mixed species, sustainable forest management` | RER | y | kg | Upstream forestry if not included in sawmill dataset |
| Chipping at forest road | `market for wood chipping, chipper, mobile, diesel, at forest road` | GLO | foreground parameter | unit | Include only if chipping is not captured in upstream forestry dataset |

**Phase 2 - Production (pyrolysis conversion):**

| Name | Ecoinvent process (ecoinvent 3.12 cutoff) | Geography | Value (per FU) | Unit | Notes |
|---|---|---|---|---|---|
| Pyrolysis reactor infrastructure | `heat production, natural gas, at industrial furnace low-NOx >100kW` (infrastructure proxy) | RER | 1 / lifetime_output | unit | Use as infrastructure proxy for slow/fast pyrolysis reactor; include only if capital goods are in scope |
| Electricity for pyrolysis | `market group for electricity, medium voltage` | RER | k_el * y | kWh | Preferred for European context; k_el is energy intensity per kg dry wood (literature value) |
| Process heat for pyrolysis | `market for heat, district or industrial, natural gas` | RER | k_th * y | MJ | Use if external heat input is required; link k_th to T_py scenario |
| Alternative heat — industrial furnace | `heat production, natural gas, at industrial furnace >100kW` | RER | k_th * y | MJ | More representative for on-site pyrolysis heat at larger scales |
| Process water | `market for tap water` | RER | scenario parameter | kg | Include if water quenching or scrubbing is modelled |
| Bio-oil product flow | foreground production exchange | — | z | kg | Reference product of foreground activity; linked to FU |
| Bio-char co-product flow | foreground co-product flow | — | c | kg | Use substitution model; see Phase 5 for credit |
| Syngas co-product flow | foreground co-product flow | — | g | kg | Syngas typically used internally for heat; model as avoided heat input |

**Phase 3 - Transportation:**

| Name | Ecoinvent process (ecoinvent 3.12 cutoff) | Geography | Value (per FU) | Unit | Notes |
|---|---|---|---|---|---|
| Transport feedstock to pyrolysis (lorry) | `market for transport, freight, lorry, 7.5-16 metric ton, diesel, EURO 6` | RER | d1 * (y/1000) | tonne-kilometer | European road freight; most appropriate for short-distance biomass collection |
| Transport bio-oil to port/use (lorry) | `market for transport, freight, lorry, 7.5-16 metric ton, diesel, EURO 6` | RER | d2 * (z/1000) | tonne-kilometer | Road leg from pyrolysis site to port or end use |
| Transport bio-oil by sea (optional) | `market for transport, freight, sea, bulk carrier for dry goods, heavy fuel oil` | GLO | d2_sea * (z/1000) | tonne-kilometer | Add sea leg for international bio-oil distribution to marine sector |
| Transport bio-char (optional) | `market for transport, freight, lorry, 7.5-16 metric ton, diesel, EURO 6` | RER | d3 * (c/1000) | tonne-kilometer | Only if bio-char leaves site for soil amendment or sequestration |

**Phase 4 - Use:**

| Name | Ecoinvent process (ecoinvent 3.12 cutoff) | Geography | Value (per FU) | Unit | Notes |
|---|---|---|---|---|---|
| Marine combustion proxy — heavy fuel oil | `market for diesel, burned in fishing vessel` | GLO | 1 MJ output | MJ | Closest proxy for marine combustion in ecoinvent 3.12; document substitution bias. A direct bio-oil marine dataset does not exist in 3.12 |
| Marine combustion proxy — residual fuel | `market for pyrolysis fuel oil` | GLO | z | kg | Use if bio-oil is explicitly modelled as pyrolysis fuel oil substitute |
| Biogenic CO2 from combustion | foreground biosphere flow: Carbon dioxide, biogenic | — | z * 44/12 * C_bio_frac | kg | Add as foreground biosphere emission; value from IPCC biomass carbon fraction |

**Phase 5 - End-of-life / co-product treatment:**

| Name | Ecoinvent process (ecoinvent 3.12 cutoff) | Geography | Value (per FU) | Unit | Notes |
|---|---|---|---|---|---|
| Syngas substitution credit — heat | `market for heat, district or industrial, natural gas` (avoided) | RER | -(g * HHV_syngas * eta_comb) | MJ | Negative technosphere exchange; HHV_syngas ≈ 10–14 MJ/kg, eta_comb ≈ 0.85 |
| Syngas substitution credit — electricity | `market group for electricity, medium voltage` (avoided) | RER | -(g * HHV_syngas * eta_elec / 3.6) | kWh | Only if syngas is used for power; eta_elec ≈ 0.30–0.35 |
| Bio-char soil amendment credit | `market for wood ash mixture, pure` (avoided, closest proxy) | RER | -c | kg | Conservative proxy; document assumed C stability fraction and 100-year permanence |
| Bio-char waste if not sequestered | `treatment of waste wood, untreated, municipal incineration with fly ash extraction` | RER | c | kg | Use if bio-char is incinerated rather than sequestered |
| Wood ash handling | `treatment of wood ash mixture, pure, sanitary landfill` | CH | foreground parameter | kg | Include if ash from pyrolysis requires disposal |
| Residual waste wood | `treatment of waste wood, post-consumer, sorting and shredding` | RER | foreground parameter | kg | For pre-treatment rejects or non-converted biomass fractions |

### 4. Modelling choice for multi-output pyrolysis

For wood pyrolysis, keep one consistent approach across all biomass categories:

- Option A: System expansion/substitution (recommended for scenario comparison)
- Option B: Allocation by energy or mass (only if substitution data are too uncertain)

Do not mix allocation and substitution across categories, otherwise cross-biomass comparison is not robust.

### 5. Data quality and uncertainty notes for wood

- Most sensitive parameters: x, T, T_py, y, z, and d1.
- Run deterministic low/medium/high scenarios plus Monte Carlo for uncertain parameters.
- Keep one moisture basis convention for all yields and convert explicitly before assigning y, z, c, and g.
- If temperature is used, link T_py to both yield x and process energy coefficients (k_el, k_th).

### 6. Minimum implementation mapping for your Brightway script

Each wood scenario should provide these fields at minimum:

- biomass_type (wood)
- scenario_id
- x, T, T_py
- y, w, z, c, g
- d1, d2, d3

Your script then computes FU-normalized exchange amounts and writes one foreground activity per scenario, which is directly compatible with the current Brightway workflow.

## Biomass category "STRAW"

To be completed with the same structure as wood (parameters, FU equations, process table, uncertainty).

## Biomass category "GRASS"

To be completed with the same structure as wood (parameters, FU equations, process table, uncertainty).