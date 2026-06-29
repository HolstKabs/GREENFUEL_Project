import unittest

from biomass_pyrolysis_equilibrium.thermodynamics.heating_value import (
    compute_hhv_mj_per_kg,
    compute_lhv_mj_per_kg,
)


class TestHeatingValue(unittest.TestCase):
    def test_hhv_lhv(self):
        hhv = compute_hhv_mj_per_kg(c_pct=50.0, h_pct=6.0, o_pct=42.0, n_pct=1.0, s_pct=0.0, ash_pct=1.0)
        lhv = compute_lhv_mj_per_kg(hhv_mj_per_kg=hhv, h_pct=6.0, moisture_pct=8.0, latent_heat_water_mj_per_kg=2.26)

        self.assertGreater(hhv, 10.0)
        self.assertLess(hhv, 30.0)
        self.assertLess(lhv, hhv)


if __name__ == "__main__":
    unittest.main()
