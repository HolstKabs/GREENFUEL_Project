# LCI modelling for each category

This document defines what differs between the three biomass categories in the LCI model. All shared parameter definitions, FU equations, and a worked example are in `docs/lca/Parameters.md`.

- FU = 1 MJ usable bio-oil delivered for marine fuel use
- The goal is to test whether higher bio-oil yield from each biomass category also leads to lower impact per FU.

> **Changing values:** all default parameters, transport distances, and energy intensities are defined in the *Biomass_Selection* and *Parameters* sheets of `LCA_process_config.xlsx`. Edit values there — not in the notebook.

---

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
