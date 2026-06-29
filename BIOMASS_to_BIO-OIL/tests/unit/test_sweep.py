import tempfile
from pathlib import Path
import unittest

import pandas as pd

from biomass_pyrolysis_equilibrium import run_workflow
from biomass_pyrolysis_equilibrium.config import SweepConfig, WorkflowConfig
from biomass_pyrolysis_equilibrium.qa.reporting import workflow_result_to_dataframes


class TestSweep(unittest.TestCase):
    def _build_workbook(self, path: Path) -> None:
        feed_df = pd.DataFrame(
            {
                "Feedstock Category": ["Wood"],
                "Feedstock Subcategory": ["Oak wood 1"],
                "M": ["5,0"],
                "VM": ["75,0"],
                "FC": ["18,0"],
                "Ash": ["2,0"],
                "C": ["50,0"],
                "H": ["6,0"],
                "O": ["42,0"],
                "N": ["1,5"],
                "S": ["0,5"],
            }
        )

        oil_df = pd.DataFrame(
            {
                "Bio-oil Category": ["Wood"],
                "Bio-oil Subcategory": ["Oak wood 1"],
                "M": ["10,0"],
                "Ash": ["1,0"],
                "C": ["60,0"],
                "H": ["7,0"],
                "O": ["31,0"],
                "N": ["1,0"],
                "S": ["1,0"],
            }
        )

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
            oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

    def test_sweep_generates_expected_number_of_rows(self):
        config = WorkflowConfig(
            sweep=SweepConfig(
                enabled=True,
                temperature_c_min=300.0,
                temperature_c_max=400.0,
                temperature_points=2,
                pressure_bar_min=1.0,
                pressure_bar_max=2.0,
                pressure_points=2,
            )
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_sweep.xlsx"
            self._build_workbook(workbook)
            result = run_workflow(str(workbook), config)

        self.assertEqual(len(result.results), 4)

        temperatures = {round(row.temperature_k, 2) for row in result.results}
        pressures = {round(row.pressure_pa, 0) for row in result.results}
        self.assertEqual(temperatures, {573.15, 673.15})
        self.assertEqual(pressures, {100000.0, 200000.0})

    def test_reporting_contains_condition_columns(self):
        config = WorkflowConfig(
            sweep=SweepConfig(
                enabled=True,
                temperature_c_min=300.0,
                temperature_c_max=300.0,
                temperature_points=1,
                pressure_bar_min=1.0,
                pressure_bar_max=1.0,
                pressure_points=1,
            )
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_sweep_reporting.xlsx"
            self._build_workbook(workbook)
            result = run_workflow(str(workbook), config)

        frames = workflow_result_to_dataframes(result)
        self.assertIn("temperature_k", frames["results"].columns)
        self.assertIn("temperature_c", frames["results"].columns)
        self.assertIn("pressure_pa", frames["results"].columns)
        self.assertIn("pressure_bar", frames["results"].columns)


if __name__ == "__main__":
    unittest.main()
