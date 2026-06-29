import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from biomass_pyrolysis_equilibrium.models import WorkflowRunResult
from biomass_pyrolysis_equilibrium.qa.artifacts import export_plot_artifacts, export_run_result


class TestArtifacts(unittest.TestCase):
    def _empty_result(self) -> WorkflowRunResult:
        return WorkflowRunResult(
            results=[],
            unmatched_mappings=[],
            parse_warnings=[],
            solver_warnings=[],
        )

    def test_export_xlsx_returns_timestamped_written_path(self):
        run_result = self._empty_result()
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "yield_results.xlsx"
            written = export_run_result(run_result, str(output))
            self.assertNotEqual(written, output)
            self.assertEqual(written.parent, output.parent)
            self.assertTrue(written.name.startswith("yield_results_"))
            self.assertEqual(written.suffix, ".xlsx")
            self.assertTrue(written.exists())

    def test_export_xlsx_does_not_swallow_permission_error(self):
        run_result = self._empty_result()
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "yield_results.xlsx"
            with patch(
                "biomass_pyrolysis_equilibrium.qa.artifacts._write_excel",
                side_effect=PermissionError("locked"),
            ):
                with self.assertRaises(PermissionError):
                    export_run_result(run_result, str(output))

    def test_export_plot_artifacts_returns_empty_for_empty_results(self):
        run_result = self._empty_result()
        with tempfile.TemporaryDirectory() as tmp_dir:
            paths = export_plot_artifacts(run_result, tmp_dir)
        self.assertEqual(paths, [])

    def test_export_run_result_include_plots_invokes_plot_export(self):
        run_result = self._empty_result()
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "yield_results.xlsx"
            with patch("biomass_pyrolysis_equilibrium.qa.artifacts.export_plot_artifacts") as mocked_plot_export:
                written = export_run_result(run_result, str(output), include_plots=True)
            self.assertTrue(written.name.startswith("yield_results_"))
            expected_plots_dir = str(written.with_suffix("")) + "_plots"
            mocked_plot_export.assert_called_once_with(run_result, expected_plots_dir)

    def test_export_run_result_include_plots_creates_timestamp_coupled_plot_dir(self):
        run_result = self._empty_result()
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "yield_results.xlsx"
            written = export_run_result(run_result, str(output), include_plots=True)
            expected_plots_dir = written.with_suffix("").with_name(f"{written.stem}_plots")
            self.assertTrue(expected_plots_dir.exists())
            self.assertTrue(expected_plots_dir.is_dir())

    def test_export_run_result_include_plots_respects_explicit_output_dir(self):
        run_result = self._empty_result()
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "yield_results.xlsx"
            custom_plots = Path(tmp_dir) / "custom_plots"
            with patch("biomass_pyrolysis_equilibrium.qa.artifacts.export_plot_artifacts") as mocked_plot_export:
                export_run_result(
                    run_result,
                    str(output),
                    include_plots=True,
                    plots_output_dir=str(custom_plots),
                )
            mocked_plot_export.assert_called_once_with(run_result, str(custom_plots))


if __name__ == "__main__":
    unittest.main()
