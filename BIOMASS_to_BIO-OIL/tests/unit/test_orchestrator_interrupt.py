import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from biomass_pyrolysis_equilibrium import WorkflowConfig
from biomass_pyrolysis_equilibrium.workflow.orchestrator import run_workflow


class TestOrchestratorInterrupt(unittest.TestCase):
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

    def test_keyboard_interrupt_returns_partial_result(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "interrupt_input.xlsx"
            self._build_workbook(workbook)

            with patch(
                "biomass_pyrolysis_equilibrium.workflow.orchestrator.solve_feedstock_equilibrium",
                side_effect=KeyboardInterrupt(),
            ):
                result = run_workflow(str(workbook), WorkflowConfig())

        self.assertEqual(len(result.results), 0)
        warning_codes = {warning.code for warning in result.parse_warnings}
        self.assertIn("RUN_INTERRUPTED", warning_codes)


if __name__ == "__main__":
    unittest.main()
