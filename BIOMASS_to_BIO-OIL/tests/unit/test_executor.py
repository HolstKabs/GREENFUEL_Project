import unittest
from unittest.mock import patch

import numpy as np

from biomass_pyrolysis_equilibrium.config import EquilibriumConfig, WorkflowConfig
from biomass_pyrolysis_equilibrium.models import FeedstockRecord, Species, ThermoProperties
from biomass_pyrolysis_equilibrium.optimization.executor import solve_feedstock_equilibrium


class TestExecutorTimeout(unittest.TestCase):
    def test_solver_attempt_timeout_returns_non_converged_result(self):
        feedstock = FeedstockRecord(
            feedstock_id="test-feedstock",
            category="Wood",
            subcategory="Oak",
            moisture_pct=10.0,
            volatile_matter_pct=70.0,
            fixed_carbon_pct=18.0,
            ash_pct=2.0,
            c_pct_daf=50.0,
            h_pct_daf=6.0,
            o_pct_daf=42.0,
            n_pct_daf=1.5,
            s_pct_daf=0.5,
        )

        thermo = ThermoProperties(
            feedstock_id=feedstock.feedstock_id,
            hhv_mj_per_kg=20.0,
            lhv_mj_per_kg=18.0,
            delta_hf_kj_per_kg=0.0,
            delta_sf_j_per_kg_k=0.0,
            delta_gf_kj_per_kg=0.0,
            element_moles_per_kg_feedstock={"C": 0.0, "H": 0.0, "O": 0.0, "N": 0.0, "S": 0.0},
            warnings=[],
        )

        species = [
            Species(
                name="CO2",
                phase="gas",
                composition={"C": 1.0, "O": 2.0},
                molecular_weight_g_per_mol=44.01,
                delta_hf_kj_per_mol=-393.52,
                s0_j_per_mol_k=213.79,
            )
        ]

        cfg = WorkflowConfig(
            equilibrium=EquilibriumConfig(
                max_iterations=100,
                tolerance=1e-8,
                residual_tolerance=1e-6,
                multi_start_attempts=1,
                max_wall_time_seconds_per_attempt=0.0,
                min_moles=1e-12,
            )
        )

        def fake_minimize(*args, **kwargs):
            callback = kwargs.get("callback")
            if callback is not None:
                callback(np.array([1e-12]))
            raise AssertionError("Timeout callback should have raised before this point")

        with patch("biomass_pyrolysis_equilibrium.optimization.executor.minimize", side_effect=fake_minimize):
            result = solve_feedstock_equilibrium(feedstock, thermo, species, cfg)

        self.assertFalse(result.converged)
        warning_codes = {w.code for w in result.warnings}
        self.assertIn("SOLVER_ATTEMPT_TIMEOUT", warning_codes)
        self.assertIn("SOLVER_DID_NOT_CONVERGE", warning_codes)


if __name__ == "__main__":
    unittest.main()
