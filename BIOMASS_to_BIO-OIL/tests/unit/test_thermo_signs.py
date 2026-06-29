import unittest

from biomass_pyrolysis_equilibrium.species.bio_oil import _estimate_delta_hf_kj_per_mol
from biomass_pyrolysis_equilibrium.thermodynamics.properties import _compute_delta_hf_kj_per_kg
from biomass_pyrolysis_equilibrium.utils.constants import STANDARD_FORMATION_ENTHALPY


class TestThermoSigns(unittest.TestCase):
    def test_bio_oil_delta_hf_uses_combustion_balance_sign(self):
        composition = {"C": 8.0, "H": 8.0, "O": 3.0, "N": 0.0, "S": 0.0}
        lhv_mj_per_kg = 17.0
        mw_g_per_mol = 152.0

        expected = (
            composition["C"] * STANDARD_FORMATION_ENTHALPY["CO2"]
            + (composition["H"] / 2.0) * STANDARD_FORMATION_ENTHALPY["H2O"]
            - lhv_mj_per_kg * mw_g_per_mol
        )

        actual = _estimate_delta_hf_kj_per_mol(composition, lhv_mj_per_kg, mw_g_per_mol)
        self.assertAlmostEqual(actual, expected, places=8)

    def test_feedstock_delta_hf_becomes_more_negative_with_higher_lhv(self):
        element_moles = {"C": 40.0, "H": 60.0, "O": 20.0, "N": 1.0, "S": 0.2}

        delta_low = _compute_delta_hf_kj_per_kg(10.0, element_moles)
        delta_high = _compute_delta_hf_kj_per_kg(20.0, element_moles)

        self.assertLess(delta_high, delta_low)


if __name__ == "__main__":
    unittest.main()
