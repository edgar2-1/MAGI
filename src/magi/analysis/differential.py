"""Differential abundance testing."""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def run_differential(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    method: str = "kruskal",
    group_col: Optional[str] = None,
) -> pd.DataFrame:
    """Run differential abundance testing between sample groups.

    Args:
        matrix: DataFrame with samples as rows and taxa as columns.
        metadata: DataFrame with sample metadata. Must share index with matrix.
        method: Testing method ("kruskal" for Kruskal-Wallis).
        group_col: Column in metadata defining groups. If None, uses the first column.

    Returns:
        DataFrame with taxa as rows and columns: statistic, p_value, p_adjusted, mean_group_*.

    Raises:
        ValueError: If method is not recognized or group_col not found.
    """
    if method not in ("kruskal",):
        raise ValueError(f"Unknown differential abundance method: {method}")

    if group_col is None:
        group_col = metadata.columns[0]

    if group_col not in metadata.columns:
        raise ValueError(f"Group column '{group_col}' not found in metadata")

    # Align samples
    shared = matrix.index.intersection(metadata.index)
    if len(shared) == 0:
        raise ValueError("No shared samples between matrix and metadata")

    matrix = matrix.loc[shared]
    groups = metadata.loc[shared, group_col]
    unique_groups = groups.unique()

    logger.info(
        "Running differential abundance (method=%s, groups=%s, taxa=%d, samples=%d)",
        method, list(unique_groups), matrix.shape[1], matrix.shape[0],
    )

    results = []
    for taxon in matrix.columns:
        group_values = [matrix.loc[groups == g, taxon].values for g in unique_groups]

        if method == "kruskal":
            # Need at least 2 groups with data
            non_empty = [gv for gv in group_values if len(gv) > 0]
            if len(non_empty) < 2:
                stat, pval = np.nan, np.nan
            else:
                stat, pval = stats.kruskal(*non_empty)

        row = {"taxon": taxon, "statistic": stat, "p_value": pval}
        for g in unique_groups:
            row[f"mean_{g}"] = float(matrix.loc[groups == g, taxon].mean())
        results.append(row)

    result = pd.DataFrame(results).set_index("taxon")

    # FDR correction (Benjamini-Hochberg)
    valid_pvals = result["p_value"].dropna()
    if len(valid_pvals) > 0:
        result["p_adjusted"] = _fdr_correction(result["p_value"])
    else:
        result["p_adjusted"] = np.nan

    logger.info("Differential abundance: %d taxa tested", len(result))
    return result


def _fdr_correction(pvals: pd.Series) -> pd.Series:
    """Benjamini-Hochberg FDR correction, handling NaN p-values."""
    valid = pvals.dropna()
    n = len(valid)
    if n == 0:
        return pvals.copy()
    ranked = valid.rank(method="first")
    adjusted = valid * n / ranked
    # Ensure monotonicity
    sorted_idx = valid.sort_values().index
    adjusted_sorted = adjusted.loc[sorted_idx]
    cummin = adjusted_sorted.iloc[::-1].cummin().iloc[::-1]
    adjusted.loc[sorted_idx] = cummin
    return adjusted.reindex(pvals.index).clip(upper=1.0)
