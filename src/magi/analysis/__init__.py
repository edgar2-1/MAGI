"""Analysis module for MAGI.

Provides co-occurrence network inference, diversity calculations,
and differential abundance testing.
"""

from magi.analysis.cooccurrence import run_cooccurrence
from magi.analysis.diversity import compute_alpha_diversity, compute_beta_diversity
from magi.analysis.differential import run_differential

__all__ = [
    "run_cooccurrence",
    "compute_alpha_diversity",
    "compute_beta_diversity",
    "run_differential",
]
