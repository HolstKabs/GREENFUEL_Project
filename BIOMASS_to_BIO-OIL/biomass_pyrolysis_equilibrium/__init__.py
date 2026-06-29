"""Biomass pyrolysis equilibrium package.

Provides a configurable workflow for:
- Reading feedstock and bio-oil data from Excel.
- Normalizing locale/range values.
- Computing thermodynamic properties.
- Solving Gibbs free energy minimization.
"""

from .config import WorkflowConfig
from .workflow.orchestrator import run_workflow

__all__ = ["WorkflowConfig", "run_workflow"]
