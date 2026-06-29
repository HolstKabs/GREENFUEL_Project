"""Custom exceptions for the biomass pyrolysis equilibrium workflow."""


class WorkflowError(Exception):
    """Base exception type for workflow failures."""


class DataValidationError(WorkflowError):
    """Raised when required input columns or rows are invalid."""


class MappingError(WorkflowError):
    """Raised when feedstock to bio-oil mapping fails critically."""


class ThermoComputationError(WorkflowError):
    """Raised when thermodynamic calculations cannot proceed."""


class SolverError(WorkflowError):
    """Raised when equilibrium minimization fails irrecoverably."""
