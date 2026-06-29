import tempfile
from pathlib import Path
import unittest

import pandas as pd

from biomass_pyrolysis_equilibrium import WorkflowConfig, run_workflow


class TestWorkflowSmoke(unittest.TestCase):
    def test_end_to_end_smoke(self):
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
                "Reference": ["[1]"],
                "Pyrolysis suitability": ["High"],
                "Regionality": ["DK"],
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
                "LHV": ["17,0"],
                "HHV": ["19,0"],
                "Reference": ["[2]"],
                "Regionality": ["SE"],
                "Measurement or Calculation": ["TRUE"],
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

            result = run_workflow(str(workbook), WorkflowConfig())

        self.assertEqual(len(result.results), 1)
        self.assertGreaterEqual(len(result.parse_warnings), 0)


if __name__ == "__main__":
    unittest.main()
