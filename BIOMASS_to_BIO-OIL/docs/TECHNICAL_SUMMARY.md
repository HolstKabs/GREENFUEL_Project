# Technical Summary: Biomass Pyrolysis Equilibrium Package

## Scope
This implementation introduces a Python package that ingests two Excel sheets (`w.proximate+ultimate` and `bio-oil values`), cleans numeric values (including comma decimals and ranges), computes thermodynamic properties, and solves a constrained Gibbs minimization per feedstock.

## Implemented Modules
- `biomass_pyrolysis_equilibrium.data`
  - Parsing, validation, normalization, and feedstock-to-bio-oil matching.
- `biomass_pyrolysis_equilibrium.thermodynamics`
  - HHV/LHV correlations and feedstock formation-property calculations.
- `biomass_pyrolysis_equilibrium.species`
  - Gas/char base registry and bio-oil pseudo-species generation from sheet data or fallback.
- `biomass_pyrolysis_equilibrium.optimization`
  - Gibbs objective, element constraints, multi-start SLSQP execution, and post-processing.
- `biomass_pyrolysis_equilibrium.workflow`
  - End-to-end orchestration for row-wise batch execution.
- `biomass_pyrolysis_equilibrium.qa`
  - Tabular reporting and artifact export to XLSX/CSV.

## Key Assumptions in This First Implementation
1. Internal calculations use element moles per kg as-received feedstock.
2. Ash is treated as inert and carried into char reporting.
3. Entropy for biomass and bio-oil pseudo-species uses explicit fallback heuristics until a calibrated correlation/database is provided.
4. Gas phase uses ideal-gas activity term; condensed phases use unit activity.
5. Multi-start SLSQP is used for constrained minimization.

## Error Handling and Robustness
- Missing/ambiguous numeric cells create structured warning codes.
- Incomplete ranges can be converted using available bounds.
- Unmatched feedstock-to-bio-oil rows are logged and fallback bio-oil can be injected.
- Solver failures produce non-fatal row-level warnings so batch execution continues.

## Next Improvements Recommended
1. Replace entropy fallback heuristics with calibrated literature correlations.
2. Add temperature-dependent species properties (`Cp(T)`, integrated `H(T)`, `S(T)`).
3. Calibrate product species set to your target pyrolysis chemistry.
4. Add acceptance thresholds and hard-stop policies for residual and non-convergence rates.
5. **Phase 4 — kinetic correction factors:** Introduce empirical correction factors to scale equilibrium yields down to realistic fast-pyrolysis values, accounting for residence time, heating rate, and reactor type. The current model gives a thermodynamic upper bound; real reactors typically achieve 60–80 % of the equilibrium oil yield.
6. **Improve the LCI with case-specific values:** The current Life-Cycle Inventory (LCI) uses generic or estimated values for key inputs such as electricity consumption, process heat source, transport distances, and char utilisation pathway. These should be replaced with measured or site-specific data (e.g. actual reactor energy consumption from pilot-plant trials, regional electricity grid mix, verified transport routes) to improve the representativeness of the environmental scores.
7. **Acknowledge the theoretical nature of the LCA results:** Because the LCA is built on top of thermodynamic equilibrium yields — which represent a theoretical maximum rather than experimentally measured output — the resulting environmental scores inherit that optimism. The bio-oil yield fed into the LCA is likely higher than what a real reactor would achieve, which means energy inputs per MJ of bio-oil are underestimated and the true environmental burden per functional unit is higher. Any interpretation of the LCA results should clearly state this limitation, and a sensitivity analysis comparing equilibrium yields against experimentally reported yields is recommended before drawing policy-relevant conclusions.
