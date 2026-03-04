"""Normalization methods for compositional abundance data."""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def normalize(matrix: pd.DataFrame, method: str = "clr") -> pd.DataFrame:
    """Normalize a feature abundance matrix.

    Args:
        matrix: DataFrame with samples as rows and features as columns.
        method: Normalization method — "clr", "relative", or "tss".

    Returns:
        Normalized DataFrame with the same shape as input.

    Raises:
        ValueError: If method is not recognized.
    """
    if method == "clr":
        return _clr(matrix)
    elif method in ("relative", "tss"):
        return _relative(matrix)
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def _clr(matrix: pd.DataFrame) -> pd.DataFrame:
    """Centered log-ratio transformation with pseudocount for zeros."""
    mat = matrix.copy().astype(float) + 0.5  # uniform pseudocount
    log_mat = np.log(mat)
    geometric_means = log_mat.mean(axis=1)
    clr_mat = log_mat.subtract(geometric_means, axis=0)
    return clr_mat


def _relative(matrix: pd.DataFrame) -> pd.DataFrame:
    """Convert to relative abundance (each row sums to 1)."""
    row_sums = matrix.sum(axis=1)
    row_sums = row_sums.replace(0, 1)  # Avoid division by zero for empty samples
    return matrix.div(row_sums, axis=0)
