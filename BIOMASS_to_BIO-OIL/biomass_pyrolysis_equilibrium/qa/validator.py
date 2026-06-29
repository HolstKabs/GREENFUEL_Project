"""Validation helpers for workflow outputs."""

from __future__ import annotations

from ..models import WorkflowRunResult


PASS_RESIDUAL_THRESHOLD = 1e-6
ACCEPT_RESIDUAL_THRESHOLD = 1e-4


def classify_acceptance(
    converged: bool,
    max_residual: float,
    pass_threshold: float = PASS_RESIDUAL_THRESHOLD,
    accept_threshold: float = ACCEPT_RESIDUAL_THRESHOLD,
) -> tuple[str, str]:
    """Classify row acceptance from convergence and residual quality."""

    if not converged:
        return "REVIEW", "solver_not_converged"
    if max_residual <= pass_threshold:
        return "PASS", "residual_within_pass_threshold"
    if max_residual <= accept_threshold:
        return "ACCEPT", "residual_within_accept_threshold"
    return "REVIEW", "residual_above_accept_threshold"


def acceptance_summary(
    run_result: WorkflowRunResult,
    pass_threshold: float = PASS_RESIDUAL_THRESHOLD,
    accept_threshold: float = ACCEPT_RESIDUAL_THRESHOLD,
) -> dict[str, float]:
    """Summarize acceptance labels across all workflow rows."""

    pass_count = 0
    accept_count = 0
    review_count = 0

    for row in run_result.results:
        label, _ = classify_acceptance(
            row.converged,
            row.max_residual,
            pass_threshold=pass_threshold,
            accept_threshold=accept_threshold,
        )
        if label == "PASS":
            pass_count += 1
        elif label == "ACCEPT":
            accept_count += 1
        else:
            review_count += 1

    total = len(run_result.results)
    denom = max(total, 1)
    return {
        "pass_threshold": pass_threshold,
        "accept_threshold": accept_threshold,
        "pass_count": float(pass_count),
        "accept_count": float(accept_count),
        "review_count": float(review_count),
        "total_rows": float(total),
        "pass_fraction": pass_count / denom,
        "accept_fraction": accept_count / denom,
        "review_fraction": review_count / denom,
    }


def count_non_converged(run_result: WorkflowRunResult) -> int:
    """Count row results where solver did not converge."""

    return sum(1 for row in run_result.results if not row.converged)


def max_observed_residual(run_result: WorkflowRunResult) -> float:
    """Return maximum residual observed across all rows."""

    if not run_result.results:
        return 0.0
    return max(row.max_residual for row in run_result.results)
