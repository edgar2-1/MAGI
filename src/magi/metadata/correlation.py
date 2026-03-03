"""Metadata-microbiome correlation analysis."""

import logging
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def run_correlation(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    tools: Optional[List[str]] = None,
    random_forest: bool = False,
) -> pd.DataFrame:
    """Correlate microbial features with sample metadata variables.

    Tests for associations between microbial abundances and continuous
    or categorical metadata variables using one or more statistical
    methods. Optionally runs a random forest model to rank feature
    importance.

    Args:
        matrix: A pandas DataFrame with samples as rows and taxa as
            columns (normalized abundances).
        metadata: A pandas DataFrame with sample metadata variables.
        tools: List of correlation tools or methods to apply (e.g.,
            ["spearman", "maaslin2"]). Defaults to ["spearman"] if None.
        random_forest: Whether to additionally run a random forest
            feature importance analysis.

    Returns:
        A pandas DataFrame with correlation results including feature
        names, metadata variables, correlation coefficients, and
        p-values.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    if tools is None:
        tools = ["spearman"]
    logger.info(
        "Running metadata correlation (tools=%s, random_forest=%s, "
        "features=%d, samples=%d)",
        tools, random_forest, matrix.shape[1], matrix.shape[0],
    )
    raise NotImplementedError("Module not yet implemented")
