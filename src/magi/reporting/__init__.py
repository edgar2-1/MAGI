"""Reporting module for MAGI.

Provides interactive dashboard generation and publication-quality
figure export.
"""

from magi.reporting.dashboard import generate_dashboard
from magi.reporting.figures import generate_figures

__all__ = ["generate_dashboard", "generate_figures"]
