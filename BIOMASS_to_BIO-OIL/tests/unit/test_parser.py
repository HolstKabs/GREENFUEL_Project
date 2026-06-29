import tempfile
from pathlib import Path
import unittest

import pandas as pd

from biomass_pyrolysis_equilibrium.config import ProcessingConfig, WorkflowConfig
from biomass_pyrolysis_equilibrium.data.parser import parse_input_workbook


class TestParser(unittest.TestCase):
    def test_parse_minimal_workbook(self):
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
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

            parsed = parse_input_workbook(str(workbook), WorkflowConfig())

        self.assertEqual(len(parsed.feedstocks), 1)
        self.assertEqual(len(parsed.bio_oils), 1)
        self.assertEqual(len(parsed.unmatched_feedstocks), 0)

    def test_parse_with_variant_sheet_names(self):
        feed_df = pd.DataFrame(
            {
                "Feedstock Category": ["Wood"],
                "Feedstock Subcategory": ["Oak wood 2"],
                "M": ["6,0"],
                "VM": ["74,0"],
                "FC": ["18,0"],
                "Ash": ["2,0"],
                "C": ["51,0"],
                "H": ["6,1"],
                "O": ["41,4"],
                "N": ["1,0"],
                "S": ["0,5"],
            }
        )

        oil_df = pd.DataFrame(
            {
                "Bio-oil Category": ["Wood"],
                "Bio-oil Subcategory": ["Oak wood 2"],
                "M": ["9,0"],
                "Ash": ["1,0"],
                "C": ["61,0"],
                "H": ["7,2"],
                "O": ["30,0"],
                "N": ["1,0"],
                "S": ["0,8"],
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_variant_sheets.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="W.Proximate+Ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="Bio-oil Values")

            parsed = parse_input_workbook(str(workbook), WorkflowConfig())

        self.assertEqual(len(parsed.feedstocks), 1)
        self.assertEqual(len(parsed.bio_oils), 1)
        self.assertTrue(any(w.code.startswith("SHEET_NAME_") for w in parsed.parse_warnings))

    def test_feedstock_optional_fields_and_ns_defaults(self):
        feed_df = pd.DataFrame(
            {
                "Feedstock Category": ["Wood"],
                "Feedstock Subcategory": ["Sparse feed"],
                "M": [None],
                "VM": [None],
                "FC": [None],
                "Ash": ["2,0"],
                "C": ["50,0"],
                "H": ["6,0"],
                "O": ["42,0"],
                "N": [None],
                "S": [None],
            }
        )

        oil_df = pd.DataFrame(
            {
                "Bio-oil Category": ["Wood"],
                "Bio-oil Subcategory": ["Sparse feed"],
                "M": [None],
                "Ash": [None],
                "C": ["60,0"],
                "H": ["7,0"],
                "O": ["31,0"],
                "N": [None],
                "S": [None],
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_sparse.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

            parsed = parse_input_workbook(str(workbook), WorkflowConfig())

        self.assertEqual(len(parsed.feedstocks), 1)
        feed_codes = {w.code for w in parsed.feedstocks[0].warnings}
        self.assertIn("FEED_M_DEFAULT_0", feed_codes)
        self.assertIn("FEED_N_DEFAULT_0", feed_codes)
        self.assertIn("FEED_S_DEFAULT_0", feed_codes)

    def test_category_level_mapping_fallback(self):
        feed_df = pd.DataFrame(
            {
                "Feedstock Category": ["Wood"],
                "Feedstock Subcategory": ["Completely unmatched name"],
                "M": ["5,0"],
                "VM": ["70,0"],
                "FC": ["23,0"],
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
                "Bio-oil Subcategory": ["Different oil name"],
                "M": [None],
                "Ash": [None],
                "C": ["60,0"],
                "H": ["7,0"],
                "O": ["31,0"],
                "N": [None],
                "S": [None],
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_category_fallback.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

            parsed = parse_input_workbook(str(workbook), WorkflowConfig())

        self.assertEqual(len(parsed.unmatched_feedstocks), 0)
        feed_codes = {w.code for w in parsed.feedstocks[0].warnings}
        self.assertIn("MAP_CATEGORY_FALLBACK", feed_codes)

    def test_synonym_normalized_mapping(self):
        feed_df = pd.DataFrame(
            {
                "Feedstock Category": ["Timber"],
                "Feedstock Subcategory": ["Pine sawdust"],
                "M": ["5,0"],
                "VM": ["70,0"],
                "FC": ["23,0"],
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
                "Bio-oil Subcategory": ["Pine wood"],
                "M": [None],
                "Ash": [None],
                "C": ["60,0"],
                "H": ["7,0"],
                "O": ["31,0"],
                "N": [None],
                "S": [None],
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_synonym_match.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

            parsed = parse_input_workbook(str(workbook), WorkflowConfig())

        self.assertEqual(len(parsed.unmatched_feedstocks), 0)
        feed_codes = {w.code for w in parsed.feedstocks[0].warnings}
        self.assertIn("MAP_SYNONYM_NORMALIZED", feed_codes)

    def test_levenshtein_mapping_fallback(self):
        feed_df = pd.DataFrame(
            {
                "Feedstock Category": ["Wood"],
                "Feedstock Subcategory": ["Eucalyptusshell"],
                "M": ["5,0"],
                "VM": ["70,0"],
                "FC": ["23,0"],
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
                "Bio-oil Subcategory": ["Eucalyptus shell"],
                "M": [None],
                "Ash": [None],
                "C": ["60,0"],
                "H": ["7,0"],
                "O": ["31,0"],
                "N": [None],
                "S": [None],
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_levenshtein_match.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

            parsed = parse_input_workbook(str(workbook), WorkflowConfig())

        self.assertEqual(len(parsed.unmatched_feedstocks), 0)
        feed_codes = {w.code for w in parsed.feedstocks[0].warnings}
        self.assertIn("MAP_SUBCATEGORY_LEVENSHTEIN", feed_codes)
        self.assertNotIn("MAP_CATEGORY_FALLBACK", feed_codes)

    def test_levenshtein_can_be_disabled(self):
        feed_df = pd.DataFrame(
            {
                "Feedstock Category": ["Wood"],
                "Feedstock Subcategory": ["Eucalyptusshell"],
                "M": ["5,0"],
                "VM": ["70,0"],
                "FC": ["23,0"],
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
                "Bio-oil Subcategory": ["Eucalyptus shell"],
                "M": [None],
                "Ash": [None],
                "C": ["60,0"],
                "H": ["7,0"],
                "O": ["31,0"],
                "N": [None],
                "S": [None],
            }
        )

        config = WorkflowConfig(
            processing=ProcessingConfig(enable_levenshtein_matching=False)
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_levenshtein_disabled.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

            parsed = parse_input_workbook(str(workbook), config)

        self.assertEqual(len(parsed.unmatched_feedstocks), 0)
        feed_codes = {w.code for w in parsed.feedstocks[0].warnings}
        self.assertNotIn("MAP_SUBCATEGORY_LEVENSHTEIN", feed_codes)
        self.assertIn("MAP_CATEGORY_FALLBACK", feed_codes)

    def test_optional_literature_oil_benchmark_columns_are_parsed(self):
        feed_df = pd.DataFrame(
            {
                "Feedstock Category": ["Wood"],
                "Feedstock Subcategory": ["Benchmark feed"],
                "M": ["10,0"],
                "VM": ["70,0"],
                "FC": ["18,0"],
                "Ash": ["2,0"],
                "C": ["50,0"],
                "H": ["6,0"],
                "O": ["42,0"],
                "N": ["1,5"],
                "S": ["0,5"],
                "Oil yield (as-received)": ["45-55"],
                "Oil yield min (dry)": ["0.50"],
                "Oil yield max (dry)": ["0.60"],
                "Oil yield daf": ["0.65"],
            }
        )

        oil_df = pd.DataFrame(
            {
                "Bio-oil Category": ["Wood"],
                "Bio-oil Subcategory": ["Benchmark feed"],
                "M": ["10,0"],
                "Ash": ["1,0"],
                "C": ["60,0"],
                "H": ["7,0"],
                "O": ["31,0"],
                "N": ["1,0"],
                "S": ["1,0"],
            }
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            workbook = Path(tmp_dir) / "test_input_benchmark_columns.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                feed_df.to_excel(writer, index=False, sheet_name="w.proximate+ultimate")
                oil_df.to_excel(writer, index=False, sheet_name="bio-oil values")

            parsed = parse_input_workbook(str(workbook), WorkflowConfig())

        self.assertEqual(len(parsed.feedstocks), 1)
        feed = parsed.feedstocks[0]

        self.assertAlmostEqual(feed.literature_oil_yield_ar_kg_per_kg, 0.50, places=8)
        self.assertAlmostEqual(feed.literature_oil_yield_ar_min_kg_per_kg, 0.45, places=8)
        self.assertAlmostEqual(feed.literature_oil_yield_ar_max_kg_per_kg, 0.55, places=8)

        self.assertAlmostEqual(feed.literature_oil_yield_dry_kg_per_kg, 0.55, places=8)
        self.assertAlmostEqual(feed.literature_oil_yield_dry_min_kg_per_kg, 0.50, places=8)
        self.assertAlmostEqual(feed.literature_oil_yield_dry_max_kg_per_kg, 0.60, places=8)

        self.assertAlmostEqual(feed.literature_oil_yield_daf_kg_per_kg, 0.65, places=8)
        self.assertAlmostEqual(feed.literature_oil_yield_daf_min_kg_per_kg, 0.65, places=8)
        self.assertAlmostEqual(feed.literature_oil_yield_daf_max_kg_per_kg, 0.65, places=8)


if __name__ == "__main__":
    unittest.main()
