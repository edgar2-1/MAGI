"""Alpha and beta diversity calculations."""

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from skbio import DistanceMatrix
from skbio.stats.distance import permanova as skbio_permanova
from skbio.stats.distance import anosim as skbio_anosim

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
    total = row.sum()
    if total == 0:
        return 0.0
    props = row[row > 0] / total
    return float(-np.sum(props * np.log(props)))


def _simpson(row: pd.Series) -> float:
    """Simpson diversity index (1 - D)."""
    total = row.sum()
    if total == 0:
        return 0.0
    props = row[row > 0] / total
    return float(1 - np.sum(props ** 2))


def _chao1(row: pd.Series) -> float:
    """Chao1 richness estimator."""
    observed = (row > 0).sum()
    singletons = (row == 1).sum()
    doubletons = (row == 2).sum()
    if doubletons == 0:
        return float(observed)
    return float(observed + (singletons ** 2) / (2 * doubletons))


def _resolve_group_col(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    group_col: Optional[str],
) -> tuple:
    """Resolve the grouping column and find shared samples.

    Args:
        matrix: Feature matrix (samples x taxa).
        metadata: Metadata DataFrame with group column.
        group_col: Column in metadata for grouping. Auto-detects if None.

    Returns:
        Tuple of (group_col, shared_samples list).

    Raises:
        ValueError: If group_col not found or no shared samples.
    """
    if group_col is None:
        group_col = metadata.columns[0]

    if group_col not in metadata.columns:
        raise ValueError(f"Group column '{group_col}' not found in metadata")

    shared = sorted(set(matrix.index) & set(metadata.index))
    if not shared:
        raise ValueError("No shared samples between matrix and metadata")

    return group_col, shared


def run_permanova(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    metric: str = "bray_curtis",
    group_col: Optional[str] = None,
    permutations: int = 999,
) -> dict:
    """Run PERMANOVA test on beta diversity distance matrix.

    Args:
        matrix: Feature matrix (samples x taxa).
        metadata: Metadata DataFrame with group column.
        metric: Distance metric to use.
        group_col: Column in metadata for grouping. Auto-detects if None.
        permutations: Number of permutations.

    Returns:
        Dict with keys: test_statistic, p_value, n_permutations, method, R2.
    """
    group_col, shared = _resolve_group_col(matrix, metadata, group_col)

    # Compute beta diversity distance matrix for shared samples
    dist_df = compute_beta_diversity(matrix.loc[shared], metrics=[metric])

    # Convert to skbio DistanceMatrix (ensure C-contiguous array for Cython)
    dm = DistanceMatrix(
        np.ascontiguousarray(dist_df.values), ids=dist_df.index.tolist()
    )

    # Build grouping vector aligned to shared samples
    grouping = metadata.loc[shared, group_col]

    # Run PERMANOVA
    result = skbio_permanova(dm, grouping, permutations=permutations)

    # R2 from F-statistic: F = (SS_between/(k-1)) / (SS_within/(n-k))
    # R2 = (F*(k-1)) / (F*(k-1) + (n-k))
    f_stat = float(result["test statistic"])
    k = int(result["number of groups"])
    n = len(shared)
    r2 = (f_stat * (k - 1)) / (f_stat * (k - 1) + (n - k))

    logger.info("PERMANOVA: F=%.4f, p=%.4f, R2=%.4f", f_stat, float(result["p-value"]), r2)

    return {
        "test_statistic": f_stat,
        "p_value": float(result["p-value"]),
        "n_permutations": permutations,
        "method": "PERMANOVA",
        "R2": r2,
    }


def run_anosim(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    metric: str = "bray_curtis",
    group_col: Optional[str] = None,
    permutations: int = 999,
) -> dict:
    """Run ANOSIM test on beta diversity distance matrix.

    Args:
        matrix: Feature matrix (samples x taxa).
        metadata: Metadata DataFrame with group column.
        metric: Distance metric to use.
        group_col: Column in metadata for grouping. Auto-detects if None.
        permutations: Number of permutations.

    Returns:
        Dict with keys: test_statistic (R), p_value, n_permutations, method.
    """
    group_col, shared = _resolve_group_col(matrix, metadata, group_col)

    # Compute beta diversity distance matrix for shared samples
    dist_df = compute_beta_diversity(matrix.loc[shared], metrics=[metric])

    # Convert to skbio DistanceMatrix (ensure C-contiguous array for Cython)
    dm = DistanceMatrix(
        np.ascontiguousarray(dist_df.values), ids=dist_df.index.tolist()
    )

    # Build grouping vector aligned to shared samples
    grouping = metadata.loc[shared, group_col]

    # Run ANOSIM
    result = skbio_anosim(dm, grouping, permutations=permutations)

    r_stat = float(result["test statistic"])
    p_val = float(result["p-value"])

    logger.info("ANOSIM: R=%.4f, p=%.4f", r_stat, p_val)

    return {
        "test_statistic": r_stat,
        "p_value": p_val,
        "n_permutations": permutations,
        "method": "ANOSIM",
    }


def compute_pcoa(
    matrix: pd.DataFrame,
    metric: str = "bray_curtis",
    n_components: int = 3,
) -> pd.DataFrame:
    """Compute PCoA ordination from a feature matrix.

    Args:
        matrix: Feature matrix (samples x taxa).
        metric: Distance metric for beta diversity.
        n_components: Number of PCoA axes to return.

    Returns:
        DataFrame with samples as rows and PC1, PC2, ... as columns.
        The proportion_explained is stored as an attribute.
    """
    if matrix.shape[0] < 3:
        logger.warning("Need at least 3 samples for PCoA, got %d", matrix.shape[0])
        cols = [f"PC{i+1}" for i in range(n_components)]
        return pd.DataFrame(columns=cols, index=matrix.index, dtype=float)

    dist_df = compute_beta_diversity(matrix, metrics=[metric])
    dm = DistanceMatrix(np.ascontiguousarray(dist_df.values), ids=dist_df.index.tolist())

    from skbio.stats.ordination import pcoa as skbio_pcoa
    pcoa_results = skbio_pcoa(dm)

    coords = pcoa_results.samples.iloc[:, :n_components].copy()
    coords.columns = [f"PC{i+1}" for i in range(coords.shape[1])]
    coords.index = dist_df.index

    # Store proportion explained as an attribute
    coords.attrs["proportion_explained"] = pcoa_results.proportion_explained.iloc[:n_components].tolist()

    logger.info("Computed PCoA (%d components) for %d samples", n_components, len(coords))
    return coords


def compute_nmds(
    matrix: pd.DataFrame,
    metric: str = "bray_curtis",
    n_components: int = 2,
    random_state: int = 42,
) -> pd.DataFrame:
    """Compute NMDS ordination from a feature matrix.

    Args:
        matrix: Feature matrix (samples x taxa).
        metric: Distance metric for beta diversity.
        n_components: Number of NMDS axes.
        random_state: Random seed for reproducibility.

    Returns:
        DataFrame with samples as rows and NMDS1, NMDS2, ... as columns.
        The stress value is stored as an attribute.
    """
    if matrix.shape[0] < n_components + 1:
        logger.warning(
            "Need at least %d samples for %d-component NMDS, got %d",
            n_components + 1, n_components, matrix.shape[0],
        )
        cols = [f"NMDS{i+1}" for i in range(n_components)]
        return pd.DataFrame(columns=cols, index=matrix.index, dtype=float)

    from sklearn.manifold import MDS

    dist_df = compute_beta_diversity(matrix, metrics=[metric])

    mds = MDS(
        n_components=n_components,
        dissimilarity="precomputed",
        random_state=random_state,
        normalized_stress="auto",
    )
    coords_array = mds.fit_transform(dist_df.values)

    coords = pd.DataFrame(
        coords_array,
        index=dist_df.index,
        columns=[f"NMDS{i+1}" for i in range(n_components)],
    )
    coords.attrs["stress"] = float(mds.stress_)

    logger.info("Computed NMDS (%d components, stress=%.4f) for %d samples",
                n_components, mds.stress_, len(coords))
    return coords
