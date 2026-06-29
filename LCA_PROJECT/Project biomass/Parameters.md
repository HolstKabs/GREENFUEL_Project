# Parameters in the model
These parameters are used to conduct transferable LCA scenarios depending on the biomass type inputs, contribution analysis and sensitivity analysis. 

### General parameters
1. Bio-Oil yield = x (Specific biomass type' yield, in [%]).
2. HHV = T (specific HHV of biomass).
3. pyrolysis_temp = T_py (If possible, theoretical best temperature of biomass).
4. weight of biomass = y (Specific required weight of biomass type, in [Kg/FU]).
5.  Energy of biomass = w (Specific energy carrier in specific biomass [J/FU]).
6.  weight of bio-oil = z (mass of specific bio-oil [kg/FU]).
7.  weight of bio-char = c (mass of specific bio-char [kg/FU]).
8.  weight of syngas = g (mass of specific syngas [kg/FU]).
9. Transportation = d1, d2, d3 (Distance for different transportation scenarios - to/from production, use etc. [tonnes-km]).

Example of use of parameters with the pyrolysis process:
1. Pyrolysis machinery = 1 unit.
2. Electricity to run the pyrolysis = 1 unit (kWh) * x (%)
> x (% amount of bio-oil yield).
3. Transportation from biomass production to pyrolysis = d1 * y 
> d1 = distance xx (km)

> y = mass of biomass [kg/FU]
4. Transportation from pyrolysis site to bio-oil refinery / use of bio-oil = d2 * z
> d2 = distance xx (km)

> z = mass of bio-oil [kg/FU]

### 1. Parameter set used for category 'wood'

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