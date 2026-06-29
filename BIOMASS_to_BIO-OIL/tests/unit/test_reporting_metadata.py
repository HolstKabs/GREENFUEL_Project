import unittest

from biomass_pyrolysis_equilibrium.models import RowWarning, WorkflowRowResult, WorkflowRunResult
from biomass_pyrolysis_equilibrium.qa.reporting import workflow_result_to_dataframes


class TestReportingMetadata(unittest.TestCase):
    def test_results_include_parser_assist_columns(self):
        row = WorkflowRowResult(
            feedstock_id="wood test",
            category="Wood",
            subcategory="Test",
            oil_yield_kg_per_kg=0.1,
            gas_yield_kg_per_kg=0.2,
            char_yield_kg_per_kg=0.3,
            efficiency_ratio=0.4,
            converged=True,
            max_residual=1e-8,
            warnings=[RowWarning("FEED_N_DEFAULT_0", "N defaulted")],
            metadata={
                "reference": "[1]",
                "regionality": "DK",
                "pyrolysis_suitability": "High",
                "parser_assist_count": "1",
                "parser_assist_codes": "FEED_N_DEFAULT_0",
                "parser_assist_messages": "N defaulted",
            },
        )

        run = WorkflowRunResult(
            results=[row],
            unmatched_mappings=[],
            parse_warnings=[],
            solver_warnings=[],
        )

        frames = workflow_result_to_dataframes(run)
        self.assertIn("parser_assist_count", frames["results"].columns)
        self.assertIn("parser_assist_codes", frames["results"].columns)
        self.assertIn("parser_assist_messages", frames["results"].columns)
        self.assertIn("acceptance_flag", frames["results"].columns)
        self.assertIn("acceptance_reason", frames["results"].columns)
        self.assertEqual(frames["results"].loc[0, "acceptance_flag"], "PASS")

    def test_results_include_dry_and_daf_yield_columns(self):
        row = WorkflowRowResult(
            feedstock_id="wood basis",
            category="Wood",
            subcategory="Basis",
            oil_yield_kg_per_kg=0.25,
            gas_yield_kg_per_kg=0.35,
            char_yield_kg_per_kg=0.40,
            efficiency_ratio=0.5,
            converged=True,
            max_residual=1e-8,
            metadata={
                "feedstock_moisture_pct_ar": "10.0",
                "feedstock_ash_pct_ar": "5.0",
            },
        )

        run = WorkflowRunResult(
            results=[row],
            unmatched_mappings=[],
            parse_warnings=[],
            solver_warnings=[],
        )

        frames = workflow_result_to_dataframes(run)
        df = frames["results"]

        self.assertIn("oil_yield_kg_per_kg_dry", df.columns)
        self.assertIn("gas_yield_kg_per_kg_dry", df.columns)
        self.assertIn("char_yield_kg_per_kg_dry", df.columns)
        self.assertIn("oil_yield_kg_per_kg_daf", df.columns)
        self.assertIn("gas_yield_kg_per_kg_daf", df.columns)
        self.assertIn("char_yield_kg_per_kg_daf", df.columns)

        # dry factor = (1 - 0.10) = 0.90
        self.assertAlmostEqual(df.loc[0, "oil_yield_kg_per_kg_dry"], 0.25 / 0.90, places=8)
        self.assertAlmostEqual(df.loc[0, "gas_yield_kg_per_kg_dry"], 0.35 / 0.90, places=8)
        self.assertAlmostEqual(df.loc[0, "char_yield_kg_per_kg_dry"], 0.40 / 0.90, places=8)

        # daf factor = 0.90 * (1 - 0.05) = 0.855
        self.assertAlmostEqual(df.loc[0, "oil_yield_kg_per_kg_daf"], 0.25 / 0.855, places=8)
        self.assertAlmostEqual(df.loc[0, "gas_yield_kg_per_kg_daf"], 0.35 / 0.855, places=8)

        # char daf is organic char only: (0.40 - 0.05) / 0.855
        self.assertAlmostEqual(df.loc[0, "char_yield_kg_per_kg_daf"], 0.35 / 0.855, places=8)

    def test_results_include_cp_and_energy_columns(self):
        row = WorkflowRowResult(
            feedstock_id="wood cp",
            category="Wood",
            subcategory="CP",
            oil_yield_kg_per_kg=0.2,
            gas_yield_kg_per_kg=0.3,
            char_yield_kg_per_kg=0.4,
            efficiency_ratio=0.5,
            converged=True,
            max_residual=1e-8,
            metadata={
                "cp_feedstock_dry_kj_per_kg_k": "1.8",
                "cp_feedstock_dry_source": "correlation:feedstock_dry_v1",
                "cp_feedstock_ar_kj_per_kg_k": "2.0",
                "cp_feedstock_ar_source": "correlation:feedstock_moisture_mix_v1",
                "cp_bio_oil_kj_per_kg_k": "2.3",
                "cp_bio_oil_source": "correlation:bio_oil_pseudocomp_v1",
                "cp_char_kj_per_kg_k": "1.0",
                "cp_char_source": "correlation:char_linear_v1",
                "cp_gas_molar_j_per_mol_k": "35.0",
                "cp_gas_mass_kj_per_kg_k": "1.2",
                "gas_mixture_mw_g_per_mol": "29.0",
                "cp_gas_source": "chemicals:webbook_shomate",
                "cp_gas_source_counts": "chemicals:webbook_shomate=2|fallback:constant=1",
                "cp_gas_fallback_fraction": "0.1",
                "delta_t_from_ref_k": "475.0",
                "input_feedstock_hhv_mj_per_kg": "15.0",
                "sensible_heat_feedstock_mj_per_kg": "0.95",
                "sensible_heat_products_mj_per_kg": "0.82",
                "output_fuel_energy_mj_per_kg": "6.0",
                "gross_energy_efficiency_ratio": "0.4",
                "gross_efficiency_consistency_abs_error": "0.0",
                "net_fuel_energy_mj_per_kg": "5.05",
                "net_energy_efficiency_ratio": "0.42",
                "net_minus_gross_efficiency_ratio": "0.02",
                "energy_accounting_status": "OK",
            },
        )

        run = WorkflowRunResult(
            results=[row],
            unmatched_mappings=[],
            parse_warnings=[],
            solver_warnings=[],
        )

        frames = workflow_result_to_dataframes(run)
        df = frames["results"]

        self.assertIn("cp_gas_molar_j_per_mol_k", df.columns)
        self.assertIn("cp_gas_mass_kj_per_kg_k", df.columns)
        self.assertIn("cp_gas_source", df.columns)
        self.assertIn("cp_feedstock_dry_source", df.columns)
        self.assertIn("cp_feedstock_ar_source", df.columns)
        self.assertIn("cp_bio_oil_source", df.columns)
        self.assertIn("cp_char_source", df.columns)
        self.assertIn("cp_gas_source_counts", df.columns)
        self.assertIn("cp_gas_fallback_fraction", df.columns)
        self.assertIn("sensible_heat_feedstock_mj_per_kg", df.columns)
        self.assertIn("input_feedstock_hhv_mj_per_kg", df.columns)
        self.assertIn("gross_energy_efficiency_ratio", df.columns)
        self.assertIn("gross_efficiency_consistency_abs_error", df.columns)
        self.assertIn("net_energy_efficiency_ratio", df.columns)
        self.assertIn("net_minus_gross_efficiency_ratio", df.columns)
        self.assertIn("energy_accounting_status", df.columns)

        self.assertAlmostEqual(df.loc[0, "cp_feedstock_ar_kj_per_kg_k"], 2.0, places=8)
        self.assertAlmostEqual(df.loc[0, "cp_gas_molar_j_per_mol_k"], 35.0, places=8)
        self.assertEqual(df.loc[0, "cp_gas_source"], "chemicals:webbook_shomate")
        self.assertAlmostEqual(df.loc[0, "cp_gas_fallback_fraction"], 0.1, places=8)
        self.assertEqual(df.loc[0, "energy_accounting_status"], "OK")

    def test_acceptance_summary_sheet_is_generated(self):
        run = WorkflowRunResult(
            results=[
                WorkflowRowResult(
                    feedstock_id="row-pass",
                    category="Wood",
                    subcategory="A",
                    oil_yield_kg_per_kg=0.2,
                    gas_yield_kg_per_kg=0.3,
                    char_yield_kg_per_kg=0.4,
                    efficiency_ratio=0.5,
                    converged=True,
                    max_residual=1e-8,
                ),
                WorkflowRowResult(
                    feedstock_id="row-review",
                    category="Wood",
                    subcategory="B",
                    oil_yield_kg_per_kg=0.2,
                    gas_yield_kg_per_kg=0.3,
                    char_yield_kg_per_kg=0.4,
                    efficiency_ratio=0.5,
                    converged=False,
                    max_residual=1e-3,
                ),
            ],
            unmatched_mappings=[],
            parse_warnings=[],
            solver_warnings=[],
        )

        frames = workflow_result_to_dataframes(run)
        self.assertIn("acceptance_summary", frames)
        summary = frames["acceptance_summary"]
        self.assertEqual(float(summary.loc[0, "pass_count"]), 1.0)
        self.assertEqual(float(summary.loc[0, "review_count"]), 1.0)

    def test_realism_summary_and_oil_percentiles_are_generated(self):
        run = WorkflowRunResult(
            results=[
                WorkflowRowResult(
                    feedstock_id="wood realist",
                    category="Wood",
                    subcategory="Realist",
                    oil_yield_kg_per_kg=0.35,
                    gas_yield_kg_per_kg=0.40,
                    char_yield_kg_per_kg=0.25,
                    efficiency_ratio=0.55,
                    converged=True,
                    max_residual=1e-8,
                    warnings=[RowWarning("BIO_OIL_GENERIC_FALLBACK", "generic oil used")],
                ),
                WorkflowRowResult(
                    feedstock_id="wood realist",
                    category="Wood",
                    subcategory="Realist",
                    oil_yield_kg_per_kg=0.40,
                    gas_yield_kg_per_kg=0.35,
                    char_yield_kg_per_kg=0.25,
                    efficiency_ratio=0.57,
                    converged=True,
                    max_residual=1e-8,
                ),
                WorkflowRowResult(
                    feedstock_id="wood realist",
                    category="Wood",
                    subcategory="Realist",
                    oil_yield_kg_per_kg=0.10,
                    gas_yield_kg_per_kg=0.60,
                    char_yield_kg_per_kg=0.30,
                    efficiency_ratio=0.20,
                    converged=False,
                    max_residual=1e-2,
                    warnings=[RowWarning("SOLVER_DID_NOT_CONVERGE", "failed")],
                ),
            ],
            unmatched_mappings=["wood unmatched"],
            parse_warnings=[],
            solver_warnings=[],
        )

        frames = workflow_result_to_dataframes(run)

        self.assertIn("realism_summary", frames)
        self.assertIn("oil_percentiles", frames)

        realism = frames["realism_summary"]
        self.assertEqual(float(realism.loc[0, "total_rows"]), 3.0)
        self.assertEqual(float(realism.loc[0, "converged_rows"]), 2.0)
        self.assertEqual(float(realism.loc[0, "unmatched_mappings_count"]), 1.0)
        self.assertGreater(float(realism.loc[0, "generic_bio_oil_fraction"]), 0.0)

        percentiles = frames["oil_percentiles"]
        self.assertFalse(percentiles.empty)
        self.assertIn("basis", percentiles.columns)
        self.assertIn("oil_yield_p10", percentiles.columns)
        self.assertIn("oil_yield_p90", percentiles.columns)
        self.assertTrue((percentiles["runs"] >= 2).any())

    def test_oil_yield_mismatch_sheet_is_generated_with_metrics(self):
        row = WorkflowRowResult(
            feedstock_id="wood mismatch",
            category="Wood",
            subcategory="Mismatch",
            oil_yield_kg_per_kg=0.40,
            gas_yield_kg_per_kg=0.35,
            char_yield_kg_per_kg=0.25,
            efficiency_ratio=0.50,
            converged=True,
            max_residual=1e-8,
            metadata={
                "feedstock_moisture_pct_ar": "10.0",
                "feedstock_ash_pct_ar": "5.0",
                "literature_oil_yield_ar_kg_per_kg": "0.35",
                "literature_oil_yield_ar_min_kg_per_kg": "0.30",
                "literature_oil_yield_ar_max_kg_per_kg": "0.38",
                "literature_oil_yield_dry_kg_per_kg": "0.40",
                "literature_oil_yield_dry_min_kg_per_kg": "0.37",
                "literature_oil_yield_dry_max_kg_per_kg": "0.45",
                "literature_oil_yield_daf_kg_per_kg": "0.43",
                "literature_oil_yield_daf_min_kg_per_kg": "0.40",
                "literature_oil_yield_daf_max_kg_per_kg": "0.50",
            },
        )

        run = WorkflowRunResult(
            results=[row],
            unmatched_mappings=[],
            parse_warnings=[],
            solver_warnings=[],
        )

        frames = workflow_result_to_dataframes(run)
        self.assertIn("oil_yield_mismatch", frames)
        mismatch = frames["oil_yield_mismatch"]
        self.assertFalse(mismatch.empty)
        self.assertTrue(set(["as_received", "dry", "daf"]).issubset(set(mismatch["basis"].unique())))

        ar_row = mismatch[mismatch["basis"] == "as_received"].iloc[0]
        self.assertAlmostEqual(ar_row["predicted_oil_yield_kg_per_kg"], 0.40, places=8)
        self.assertAlmostEqual(ar_row["benchmark_oil_yield_kg_per_kg"], 0.35, places=8)
        self.assertAlmostEqual(ar_row["absolute_error_kg_per_kg"], 0.05, places=8)
        self.assertAlmostEqual(ar_row["relative_error_fraction"], 0.05 / 0.35, places=8)
        self.assertFalse(bool(ar_row["in_range"]))
        self.assertAlmostEqual(ar_row["out_of_range_distance_kg_per_kg"], 0.02, places=8)


if __name__ == "__main__":
    unittest.main()
