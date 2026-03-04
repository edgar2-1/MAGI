"""Shared CLR+SVD biplot computation for dashboard and static figures."""

import logging
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BiplotData:
    """Computed biplot data for visualization."""
    sample_scores: np.ndarray  # (n_samples, 2)
    taxa_loadings: np.ndarray  # (n_taxa, 2)
    sample_names: List[str]
    taxa_names: List[str]
    top_taxa_indices: np.ndarray
    var_explained: np.ndarray  # (2,) percentages
    scale: float  # arrow scaling factor


def compute_biplot_data(
    matrix: pd.DataFrame,
    n_top_taxa: int = 10,
) -> BiplotData:
    """Compute CLR-transformed PCA biplot data from a feature matrix.

    Args:
        matrix: Feature matrix (samples x taxa), raw counts or abundances.
        n_top_taxa: Number of top taxa to highlight by loading magnitude.

    Returns:
        BiplotData with sample scores, taxa loadings, and metadata.
    """
    # CLR transform (add pseudocount to handle zeros)
    pseudo = matrix + 0.5  # same pseudocount as normalize._clr
    log_data = np.log(pseudo)
    clr = log_data.subtract(log_data.mean(axis=1), axis=0)

    # SVD for PCA on CLR-transformed data
    centered = clr - clr.mean()
    U, S, Vt = np.linalg.svd(centered.values, full_matrices=False)

    # Sample scores (first 2 PCs)
    sample_scores = U[:, :2] * S[:2]

    # Taxa loadings (first 2 PCs)
    taxa_loadings = Vt[:2, :].T

    # Select top taxa by loading magnitude
    loading_magnitude = np.sqrt(taxa_loadings[:, 0]**2 + taxa_loadings[:, 1]**2)
    n_top = min(n_top_taxa, len(loading_magnitude))
    top_idx = np.argsort(loading_magnitude)[-n_top:]

    # Explained variance
    total_var = np.sum(S**2)
    var_explained = S[:2]**2 / total_var * 100

    # Arrow scaling factor
    scale = np.max(np.abs(sample_scores)) / np.max(np.abs(taxa_loadings[top_idx])) * 0.8

    return BiplotData(
        sample_scores=sample_scores,
        taxa_loadings=taxa_loadings,
        sample_names=list(matrix.index),
        taxa_names=list(matrix.columns),
        top_taxa_indices=top_idx,
        var_explained=var_explained,
        scale=scale,
    )
