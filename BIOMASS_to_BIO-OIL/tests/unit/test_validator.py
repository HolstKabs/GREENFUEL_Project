import unittest

from biomass_pyrolysis_equilibrium.models import WorkflowRowResult, WorkflowRunResult
from biomass_pyrolysis_equilibrium.qa.validator import acceptance_summary, classify_acceptance


class TestValidator(unittest.TestCase):
    def test_classify_acceptance_thresholds(self):
        label, reason = classify_acceptance(converged=True, max_residual=1e-8)
        self.assertEqual(label, "PASS")
        self.assertEqual(reason, "residual_within_pass_threshold")

        label, reason = classify_acceptance(converged=True, max_residual=5e-5)
        self.assertEqual(label, "ACCEPT")
        self.assertEqual(reason, "residual_within_accept_threshold")

        label, reason = classify_acceptance(converged=True, max_residual=2e-3)
        self.assertEqual(label, "REVIEW")
        self.assertEqual(reason, "residual_above_accept_threshold")

        label, reason = classify_acceptance(converged=False, max_residual=1e-10)
        self.assertEqual(label, "REVIEW")
        self.assertEqual(reason, "solver_not_converged")

    def test_acceptance_summary_counts(self):
        run = WorkflowRunResult(
            results=[
                WorkflowRowResult(
                    feedstock_id="pass",
                    category="Wood",
                    subcategory="A",
                    oil_yield_kg_per_kg=0.1,
                    gas_yield_kg_per_kg=0.2,
                    char_yield_kg_per_kg=0.3,
                    efficiency_ratio=0.4,
                    converged=True,
                    max_residual=1e-8,
                ),
                WorkflowRowResult(
                    feedstock_id="accept",
                    category="Wood",
                    subcategory="B",
                    oil_yield_kg_per_kg=0.1,
                    gas_yield_kg_per_kg=0.2,
                    char_yield_kg_per_kg=0.3,
                    efficiency_ratio=0.4,
                    converged=True,
                    max_residual=5e-5,
                ),
                WorkflowRowResult(
                    feedstock_id="review",
                    category="Wood",
                    subcategory="C",
                    oil_yield_kg_per_kg=0.1,
                    gas_yield_kg_per_kg=0.2,
                    char_yield_kg_per_kg=0.3,
                    efficiency_ratio=0.4,
                    converged=False,
                    max_residual=1e-3,
                ),
            ],
            unmatched_mappings=[],
            parse_warnings=[],
            solver_warnings=[],
        )

        summary = acceptance_summary(run)
        self.assertEqual(summary["pass_count"], 1.0)
        self.assertEqual(summary["accept_count"], 1.0)
        self.assertEqual(summary["review_count"], 1.0)
        self.assertEqual(summary["total_rows"], 3.0)


if __name__ == "__main__":
    unittest.main()
