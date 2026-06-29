# Converting proximate and ultimate analysis to thermodynamic properties
A summary of the formulations for converting the biomass analysis data to thermodynamic properties

## Explain the structure of the analysis data file
Explain how the excel sheet is structured:

The dataset is provided in an Excel workbook (`Feedstock_table.xlsx`), which is structured to maintain data separation while preserving the integrity of the original research. The workbook consists of three primary worksheets: `w.proximate+ultimate`, `bio-oil values`, and `Feedstock tab 1.3 BOOK`.

**1. Worksheet: "w.proximate+ultimate":**
This sheet contains the foundational classification and elemental analysis of the biomass. Key columns include:
* **Column A (Feedstock Category):** The broad classification of the material (e.g., Rows 3-56 represent "Wood").
* **Column B (Feedstock Subcategory):** The specific biomass type (e.g., "Oak wood 1", "Oak wood 2").
* **Column C-F (Proximate Analysis (wt%)):** Including the specific weight distribution of Moisture (M), Volatile Matter (VM), Fixed Carbon (FC) and Ash (found on C2-F2).
* **Column G-K (Ultimate Analysis(wt% daf)):** The chemical composition of specific feedstock type. (e.g. Carbon (C), Hydrogen (H), Oxygen(O), Nitrogen (N), Sulphur (S). Described on cells G2-K2.)
* **Column L-M (Calorific Value(MJ/kg)):** Both Lower Heating Value (LHV) and Higher Heating Value (HHV) (shown on cells L2-M2).
* **Column N (Reference):** A numerical value referencing to the Bibliography (e.g. cell N5 representing reference [6]).
* **Column O (Pyrolysis suitability):** How suitable is the specific biomass type to the pyrolysis process.
* **Column P (Regionality):** In which country was the specific biomass type researched.

**2. Worksheet: "Bio-oil values":**

This sheet contains the foundational classification of bio-oil values and elemental analysis. Key columns include:
* **Column A (Bio-oil Category):** The broad classification of the material (e.g., Rows 3-33 represent "Wood").
* **Column B (Bio-oil Subcategory):** The specific bio-oil type (e.g., "Chips beech" in cell B3.).
* **Column C-D (Elemental Analysis) (wt%):** Including the specific weight distribution of Moisture (M) and Ash (found on C2-D2).
* **Column E-I (Elemental Analysis(wt% daf)):** The chemical composition of specific bio-oil type. (e.g. Carbon (C), Hydrogen (H), Oxygen(O), Nitrogen (N), Sulphur (S).)
* **Column J-K (Calorific Value(MJ/kg)):** Can include either or both Lower Heating Value (LHV) and Higher Heating Value (HHV).
* **Column L (Reference):** A numerical value referencing to the Bibliography (e.g. cell N5 representing reference [6], this is linked to the reference list on sheet "w.proximate+ultimate", but will eventually be described in a papar.)
* **Column M (Regionality):** In which country was the specific bio-oil type researched.
* **Column N-O (Measurement or Calculation):** In these columns the text "TRUE" will be written if the bio-oil values derives from experimental or theoretical work.

**3. Worksheet: "Feedstock tab 1.3 BOOK:**

Not needed for any further work this has been kept for explanation and identification of different feedstock types.

## Lower heating value
The Higher Heating Value (HHV) of biomass can be estimated from the ultimate analysis (where C, H, O, N, S, and Ash are mass percentages on a dry basis) using correlations like the Channiwala and Parikh formula:
$$ HHV = 0.3491 \cdot C + 1.1783 \cdot H + 0.1005 \cdot S - 0.1034 \cdot O - 0.0151 \cdot N - 0.0211 \cdot Ash \quad \text{[MJ/kg]} $$

The Lower Heating Value (LHV) is calculated by subtracting the latent heat of vaporization of the water produced from oxidation of hydrogen and any initial moisture content:
$$ LHV = HHV - h_{we} \cdot \left( \frac{9H}{100} + \frac{M}{100} \right) \quad \text{[MJ/kg]} $$
where $M$ is the moisture percentage, and $h_{we}$ is the latent heat of water ($\approx 2.26 \text{ MJ/kg}$).

## Enthalpy of formation
The standard enthalpy of formation ($\Delta h_f^\circ$) of biomass can be derived from its absolute lower heating value and the standard enthalpies of formation of the complete combustion products ($CO_2$, $H_2O_{(g)}$, $SO_2$). Based on stoichiometry:
$$ \Delta h_f^\circ (\text{Biomass}) = LHV + \left( \frac{C}{12.01} \Delta h_{f, CO_2}^\circ + \frac{H_2}{1.008 \cdot 2} \Delta h_{f, H_2O}^\circ + \frac{S}{32.06} \Delta h_{f, SO_2}^\circ \right) $$
*Note: Ensure consistent units, typically kJ/kg or kJ/kmol of a generic biomass structural unit.*

## Entropy of formation
The standard absolute entropy ($s^\circ$) of solid biomass is commonly estimated using empirical group contribution methods or elemental composition-based correlations. 
The standard entropy of formation ($\Delta s_f^\circ$) is then calculated as the difference between the standard entropy of the biomass and the standard entropies of its elements in their standard reference states (e.g., graphite, gaseous $H_2$, $O_2$, $N_2$):
$$ \Delta s_f^\circ = s^\circ_{\text{Biomass}} - \sum (\nu_{elem} \cdot s^\circ_{elem}) $$

## Gibbs energy of formation
The standard Gibbs energy of formation ($\Delta g_f^\circ$) represents the combined thermodynamic stability of the biomass component and is determined from the fundamental relationship:
$$ \Delta g_f^\circ = \Delta h_f^\circ - T_{ref} \cdot \Delta s_f^\circ $$
where $T_{ref}$ is the standard reference temperature, usually $298.15 \text{ K}$.

## Thermodynamic Equilibrium of Biomass Pyrolysis
The thermodynamic equilibrium representing the conversion of biomass to pyrolysis oil, char, and gas relies on utilizing non-stoichiometric models based on the **Gibbs Free Energy Minimization** approach.

The objective function is to minimize the total system Gibbs free energy ($G_{total}$), given a specified temperature ($T$) and pressure ($P$):
$$ \min (G_{total}) = \sum_{i=1}^{N_c} n_i \mu_i $$
where $n_i$ is the number of moles of species $i$ (including gas species, solid char, and bio-oil model compounds), and $\mu_i$ is the chemical potential of species $i$ in its phase.

This minimization is subject to mass conservation constraints for each atomic element $j$ (C, H, O, N, S):
$$ \sum_{i=1}^{N_c} a_{j,i} n_i = b_j \quad (j = 1, \dots, N_e) $$
where $a_{j,i}$ is the number of atoms of element $j$ in species $i$, and $b_j$ is the total initial moles of element $j$ provided by the biomass feed. Leveraging the derived $\Delta g_f^\circ$ constraints ensures accurate phase equilibrium and speciation for predicting pyrolysis oil yield and gas composition.

