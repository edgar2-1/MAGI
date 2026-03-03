"""Alpha and beta diversity calculations."""

import logging
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def compute_alpha_diversity(
    matrix: pd.DataFrame,
    metrics: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute alpha diversity metrics for each sample.

    Calculates within-sample diversity using one or more ecological
    diversity indices (e.g., Shannon, Simpson, observed species).

    Args:
        matrix: A pandas DataFrame with samples as rows and taxa as
            columns (abundance values).
        metrics: List of alpha diversity metrics to compute. Defaults
            to ["shannon", "simpson", "observed_species"] if None.

    Returns:
        A pandas DataFrame with samples as rows and diversity metrics
        as columns.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    if metrics is None:
        metrics = ["shannon", "simpson", "observed_species"]
    logger.info(
        "Computing alpha diversity (metrics=%s, samples=%d)",
        metrics, matrix.shape[0],
    )
    raise NotImplementedError("Module not yet implemented")


def compute_beta_diversity(
    matrix: pd.DataFrame,
    metrics: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute beta diversity distance matrices between samples.

    Calculates between-sample dissimilarity using one or more distance
    metrics (e.g., Bray-Curtis, Jaccard, UniFrac).

    Args:
        matrix: A pandas DataFrame with samples as rows and taxa as
            columns (abundance values).
        metrics: List of beta diversity metrics to compute. Defaults
            to ["bray_curtis", "jaccard"] if None.

    Returns:
        A pandas DataFrame representing the pairwise distance matrix
        (samples x samples) for the first metric. If multiple metrics
        are requested, returns the result for the first metric.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    if metrics is None:
        metrics = ["bray_curtis", "jaccard"]
    logger.info(
        "Computing beta diversity (metrics=%s, samples=%d)",
        metrics, matrix.shape[0],
    )
    raise NotImplementedError("Module not yet implemented")
