import unittest

try:
    import chemicals.heat_capacity as _chem_hc

    HAS_CHEMICALS = True
except Exception:  # pragma: no cover
    HAS_CHEMICALS = False

from biomass_pyrolysis_equilibrium.models import EquilibriumSolution, FeedstockRecord, Species
from biomass_pyrolysis_equilibrium.thermodynamics.cp import (
    estimate_feedstock_cp_ar_kj_per_kg_k,
    estimate_feedstock_cp_dry_kj_per_kg_k,
    gas_mixture_cp,
    gas_mixture_cp_diagnostics,
    gas_species_cp_molar_j_per_mol_k,
)


class TestCp(unittest.TestCase):
    def test_feedstock_cp_ar_is_higher_with_moisture(self):
        dry_record = FeedstockRecord(
            feedstock_id="dry",
            category="Wood",
            subcategory="dry",
            moisture_pct=0.0,
            volatile_matter_pct=70.0,
            fixed_carbon_pct=20.0,
            ash_pct=2.0,
            c_pct_daf=50.0,
            h_pct_daf=6.0,
            o_pct_daf=42.0,
            n_pct_daf=1.5,
            s_pct_daf=0.5,
        )
        wet_record = FeedstockRecord(
            feedstock_id="wet",
            category="Wood",
            subcategory="wet",
            moisture_pct=20.0,
            volatile_matter_pct=70.0,
            fixed_carbon_pct=20.0,
            ash_pct=2.0,
            c_pct_daf=50.0,
            h_pct_daf=6.0,
            o_pct_daf=42.0,
            n_pct_daf=1.5,
            s_pct_daf=0.5,
        )

        cp_dry = estimate_feedstock_cp_dry_kj_per_kg_k(dry_record, 773.15)
        cp_ar_dry = estimate_feedstock_cp_ar_kj_per_kg_k(dry_record, 773.15)
        cp_ar_wet = estimate_feedstock_cp_ar_kj_per_kg_k(wet_record, 773.15)

        self.assertGreater(cp_dry, 0.0)
        self.assertAlmostEqual(cp_ar_dry, cp_dry, places=8)
        self.assertGreater(cp_ar_wet, cp_ar_dry)

    def test_gas_species_cp_uses_available_backend(self):
        cp, source = gas_species_cp_molar_j_per_mol_k("CO2", 773.15, 101325.0)
        self.assertGreater(cp, 0.0)

        if HAS_CHEMICALS:
            self.assertTrue(source.startswith("chemicals"))
        else:
            self.assertTrue(source.startswith("coolprop") or source.startswith("fallback"))

    def test_gas_mixture_cp_returns_positive_values(self):
        species = [
            Species("CO2", "gas", {"C": 1.0, "O": 2.0}, 44.01, -393.52, 213.79),
            Species("H2", "gas", {"H": 2.0}, 2.016, 0.0, 130.68),
            Species("CHAR", "solid_char", {"C": 1.0}, 12.01, 0.0, 5.74),
        ]
        solution = EquilibriumSolution(
            feedstock_id="mix",
            temperature_k=773.15,
            pressure_pa=101325.0,
            species_moles={"CO2": 0.5, "H2": 0.5, "CHAR": 0.1},
            element_residuals={"C": 0.0, "H": 0.0, "O": 0.0, "N": 0.0, "S": 0.0},
            max_residual=0.0,
            converged=True,
            g_total_kj=-1.0,
            solver_message="ok",
            warnings=[],
        )

        cp_molar, cp_mass, mw_mix, source = gas_mixture_cp(
            solution,
            species,
            solution.temperature_k,
            solution.pressure_pa,
        )

        self.assertGreater(cp_molar, 0.0)
        self.assertGreater(cp_mass, 0.0)
        self.assertGreater(mw_mix, 0.0)
        self.assertTrue(len(source) > 0)

    def test_gas_mixture_cp_diagnostics_tracks_fallback_fraction(self):
        species = [
            Species("XGAS", "gas", {"C": 1.0}, 28.0, 0.0, 100.0),
        ]
        solution = EquilibriumSolution(
            feedstock_id="mix-fallback",
            temperature_k=700.0,
            pressure_pa=101325.0,
            species_moles={"XGAS": 1.0},
            element_residuals={"C": 0.0, "H": 0.0, "O": 0.0, "N": 0.0, "S": 0.0},
            max_residual=0.0,
            converged=True,
            g_total_kj=-1.0,
            solver_message="ok",
            warnings=[],
        )

        cp_molar, cp_mass, mw_mix, dominant_source, source_counts, fallback_fraction = gas_mixture_cp_diagnostics(
            solution,
            species,
            solution.temperature_k,
            solution.pressure_pa,
        )

        self.assertGreater(cp_molar, 0.0)
        self.assertGreater(cp_mass, 0.0)
        self.assertGreater(mw_mix, 0.0)
        self.assertEqual(dominant_source, "fallback:constant")
        self.assertIn("fallback:constant=1", source_counts)
        self.assertAlmostEqual(fallback_fraction, 1.0, places=8)


if __name__ == "__main__":
    unittest.main()
