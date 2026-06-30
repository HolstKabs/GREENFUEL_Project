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

## Biomass category "AGRICULTURAL WASTES"

### 1. Parameter set used for agricultural wastes (aligned with Parameters.md)

Use one row of parameters per agricultural waste scenario (species, moisture basis, and technology assumptions).

| Parameter | Symbol in Parameters.md | Unit | Description |
|---|---|---|---|
| Bio-oil yield | x | % | Yield of bio-oil from selected agricultural waste type |
| HHV | T | MJ/kg oil | HHV used for the produced bio-oil in FU normalization |
| Pyrolysis temperature | T_py | degC | Technology/scenario parameter linked to yield and energy demand |
| Weight of biomass | y | kg/FU | Biomass required per FU |
| Energy of biomass (or delivered oil energy basis in model) | w | J/FU | Energy linked to FU normalization |
| Weight of bio-oil | z | kg/FU | Produced bio-oil mass per FU |
| Weight of bio-char | c | kg/FU | Co-product bio-char mass per FU |
| Weight of syngas | g | kg/FU | Co-product syngas mass per FU |
| Transport distance feedstock to pyrolysis | d1 | km | Agricultural residue collection transport |
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

### 2. System phases for agricultural wastes

1. Raw material supply (agricultural residue collection and handling)
2. Conversion (pyrolysis to bio-oil, char, syngas)
3. Transportation (feedstock, oil, optional co-products)
4. Use phase (combustion/use of bio-oil)
5. End-of-life and/or substitution credits for co-products

## Biomass category "RESIDUES AND WASTES"

### 1. Parameter set used for residues and wastes (aligned with Parameters.md)

Use one row of parameters per residue/waste scenario (species, moisture basis, and technology assumptions).

| Parameter | Symbol in Parameters.md | Unit | Description |
|---|---|---|---|
| Bio-oil yield | x | % | Yield of bio-oil from selected residue/waste type |
| HHV | T | MJ/kg oil | HHV used for the produced bio-oil in FU normalization |
| Pyrolysis temperature | T_py | degC | Technology/scenario parameter linked to yield and energy demand |
| Weight of biomass | y | kg/FU | Biomass required per FU |
| Energy of biomass (or delivered oil energy basis in model) | w | J/FU | Energy linked to FU normalization |
| Weight of bio-oil | z | kg/FU | Produced bio-oil mass per FU |
| Weight of bio-char | c | kg/FU | Co-product bio-char mass per FU |
| Weight of syngas | g | kg/FU | Co-product syngas mass per FU |
| Transport distance feedstock to pyrolysis | d1 | km | Residue/waste collection transport |
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

### 2. System phases for residues and wastes

1. Raw material supply (residue/waste collection and handling)
2. Conversion (pyrolysis to bio-oil, char, syngas)
3. Transportation (feedstock, oil, optional co-products)
4. Use phase (combustion/use of bio-oil)
5. End-of-life and/or substitution credits for co-products