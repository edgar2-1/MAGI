"""Differential abundance testing."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def run_differential(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    method: str = "aldex2",
) -> pd.DataFrame:
    """Run differential abundance testing between sample groups.

    Identifies taxa with significantly different abundances across
    experimental conditions or groups defined in the metadata.

    Args:
        matrix: A pandas DataFrame with samples as rows and taxa as
            columns (normalized abundances).
        metadata: A pandas DataFrame with sample metadata, including a
            grouping variable for comparison.
        method: Differential abundance method to use (e.g., "aldex2",
            "ancombc", "maaslin2").

    Returns:
        A pandas DataFrame with taxa as rows and columns including
        effect size, p-value, and adjusted p-value.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info(
        "Running differential abundance (method=%s, taxa=%d, samples=%d)",
        method, matrix.shape[1], matrix.shape[0],
    )
    raise NotImplementedError("Module not yet implemented")
