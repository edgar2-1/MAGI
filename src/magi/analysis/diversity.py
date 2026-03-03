"""Alpha and beta diversity calculations."""

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

logger = logging.getLogger(__name__)


def compute_alpha_diversity(
    matrix: pd.DataFrame,
    metrics: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute alpha diversity metrics for each sample.

    Args:
        matrix: DataFrame with samples as rows and taxa as columns.
        metrics: List of metrics. Defaults to ["shannon", "simpson", "observed_species"].

    Returns:
        DataFrame with samples as rows and metrics as columns.
    """
    if metrics is None:
        metrics = ["shannon", "simpson", "observed_species"]

    results = {}

    for metric in metrics:
        if metric == "shannon":
            results[metric] = matrix.apply(_shannon, axis=1)
        elif metric == "simpson":
            results[metric] = matrix.apply(_simpson, axis=1)
        elif metric == "observed_species":
            results[metric] = (matrix > 0).sum(axis=1)
        elif metric == "chao1":
            results[metric] = matrix.apply(_chao1, axis=1)
        else:
            raise ValueError(f"Unknown alpha diversity metric: {metric}")

    result = pd.DataFrame(results, index=matrix.index)
    logger.info("Computed alpha diversity (%s) for %d samples", metrics, len(result))
    return result


def compute_beta_diversity(
    matrix: pd.DataFrame,
    metrics: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute beta diversity distance matrix between samples.

    Args:
        matrix: DataFrame with samples as rows and taxa as columns.
        metrics: List of metrics. Defaults to ["bray_curtis"].

    Returns:
        DataFrame (samples x samples) distance matrix for the first metric.
    """
    if metrics is None:
        metrics = ["bray_curtis"]

    metric = metrics[0]

    if metric == "bray_curtis":
        dist_matrix = squareform(pdist(matrix.values, metric="braycurtis"))
    elif metric == "jaccard":
        binary = (matrix > 0).astype(float)
        dist_matrix = squareform(pdist(binary.values, metric="jaccard"))
    else:
        raise ValueError(f"Unknown beta diversity metric: {metric}")

    result = pd.DataFrame(dist_matrix, index=matrix.index, columns=matrix.index)
    logger.info("Computed %s beta diversity for %d samples", metric, len(result))
    return result


def _shannon(row: pd.Series) -> float:
    """Shannon diversity index H'."""
    props = row[row > 0] / row.sum()
    return float(-np.sum(props * np.log(props)))


def _simpson(row: pd.Series) -> float:
    """Simpson diversity index (1 - D)."""
    props = row[row > 0] / row.sum()
    return float(1 - np.sum(props ** 2))


def _chao1(row: pd.Series) -> float:
    """Chao1 richness estimator."""
    observed = (row > 0).sum()
    singletons = (row == 1).sum()
    doubletons = (row == 2).sum()
    if doubletons == 0:
        return float(observed)
    return float(observed + (singletons ** 2) / (2 * doubletons))
