import tempfile
import unittest
from pathlib import Path

import pandas as pd

from biomass_pyrolysis_equilibrium.qa.plotting import save_default_plots


class TestPlotting(unittest.TestCase):
    def test_save_default_plots_generates_expected_files(self):
        results_df = pd.DataFrame(
            {
                "feedstock_id": ["a", "a", "b", "b"],
                "category": ["Wood", "Wood", "Herb", "Herb"],
                "subcategory": ["Pine", "Pine", "Straw", "Straw"],
                "feedstock_c_pct_daf": [50.0, 50.0, 48.0, 48.0],
                "feedstock_h_pct_daf": [6.0, 6.0, 6.2, 6.2],
                "feedstock_o_pct_daf": [42.0, 42.0, 43.0, 43.0],
                "oil_yield_kg_per_kg": [0.3, 0.35, 0.28, 0.32],
                "gas_yield_kg_per_kg": [0.45, 0.40, 0.49, 0.44],
                "char_yield_kg_per_kg": [0.25, 0.25, 0.23, 0.24],
                "oil_yield_kg_per_kg_dry": [0.33, 0.39, 0.31, 0.36],
                "gas_yield_kg_per_kg_dry": [0.49, 0.44, 0.54, 0.49],
                "char_yield_kg_per_kg_dry": [0.27, 0.27, 0.25, 0.26],
                "oil_yield_kg_per_kg_daf": [0.35, 0.41, 0.33, 0.38],
                "gas_yield_kg_per_kg_daf": [0.52, 0.47, 0.57, 0.52],
                "char_yield_kg_per_kg_daf": [0.29, 0.29, 0.27, 0.28],
                "temperature_c": [300.0, 400.0, 300.0, 400.0],
                "pressure_bar": [1.0, 1.0, 2.0, 2.0],
                "converged": [True, False, True, True],
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_paths = save_default_plots(results_df, tmp_dir)

            names = {path.name for path in output_paths}
            self.assertIn("van_krevelen.png", names)
            self.assertIn("van_krevelen_dry.png", names)
            self.assertIn("van_krevelen_daf.png", names)
            self.assertIn("ternary_cho.png", names)
            self.assertIn("yield_basis_comparison.png", names)
            self.assertIn("peak_yield_basis_comparison.png", names)
            self.assertIn("peak_yield_vs_temperature.png", names)
            self.assertIn("peak_yield_vs_temperature_dry.png", names)
            self.assertIn("peak_yield_vs_temperature_daf.png", names)
            self.assertIn("root_category_oil_percentile_summary.png", names)
            self.assertIn("root_category_oil_percentile_summary_dry.png", names)
            self.assertIn("root_category_oil_percentile_summary_daf.png", names)
            self.assertIn("root_category_oil_percentile_summary_all_bases.png", names)
            self.assertIn("root_category_oil_vs_temperature.png", names)
            self.assertIn("root_category_oil_vs_temperature_dry.png", names)
            self.assertIn("root_category_oil_vs_temperature_daf.png", names)
            self.assertNotIn("yield_vs_temperature.png", names)
            self.assertNotIn("yield_vs_temperature_dry.png", names)
            self.assertNotIn("yield_vs_temperature_daf.png", names)

            for path in output_paths:
                self.assertTrue(Path(path).exists())
                self.assertGreater(Path(path).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
