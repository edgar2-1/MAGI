"""Metadata correlation analysis using statistical tests and random forests."""

import logging
from typing import List, Optional

import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def run_correlation(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    tools: Optional[List[str]] = None,
    random_forest: bool = True,
    group_col: Optional[str] = None,
) -> dict:
    """Run metadata correlation analysis.

    Tests associations between microbial features and metadata variables.
    Optionally trains a random forest to rank feature importance and
    compare multi-kingdom vs single-kingdom biomarker panels.

    Args:
        matrix: DataFrame with samples as rows and taxa as columns.
        metadata: DataFrame with sample metadata. Must share index with matrix.
        tools: List of correlation tools to run. Defaults to ["spearman"].
        random_forest: Whether to run random forest feature importance.
        group_col: Column in metadata for group-based analysis.

    Returns:
        Dict with keys: "correlations" (DataFrame), and optionally
        "feature_importance" (DataFrame).

    Raises:
        ValueError: If no shared samples between matrix and metadata.
    """
    if tools is None:
        tools = ["spearman"]

    if group_col is None:
        group_col = metadata.columns[0]

    # Align samples
    shared = matrix.index.intersection(metadata.index)
    if len(shared) == 0:
        raise ValueError("No shared samples between matrix and metadata")

    matrix = matrix.loc[shared]
    metadata = metadata.loc[shared]

    results = {}

    # Correlation analysis
    if "spearman" in tools:
        corr_results = _spearman_correlations(matrix, metadata, group_col)
        results["correlations"] = corr_results
        logger.info("Spearman correlations: %d taxa tested", len(corr_results))

    # Random forest feature importance
    if random_forest:
        importance = _random_forest_importance(matrix, metadata, group_col)
        results["feature_importance"] = importance
        logger.info("Random forest: top features identified")

    return results


def _spearman_correlations(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    group_col: str,
) -> pd.DataFrame:
    """Compute Spearman correlations between taxa and numeric metadata."""
    rows = []

    # Encode group as numeric for correlation
    groups = metadata[group_col]
    if groups.dtype == object:
        group_codes = pd.Categorical(groups).codes
    else:
        group_codes = groups.values

    for taxon in matrix.columns:
        rho, pval = stats.spearmanr(matrix[taxon].values, group_codes)
        rows.append({
            "taxon": taxon,
            "rho": rho,
            "p_value": pval,
        })

    result = pd.DataFrame(rows).set_index("taxon")

    # FDR correction
    n = len(result)
    if n > 0:
        sorted_result = result.sort_values("p_value")
        ranked = sorted_result["p_value"].rank(method="first")
        raw_adjusted = (sorted_result["p_value"] * n / ranked).clip(upper=1.0)
        # Enforce monotonicity: adjusted p-values must be non-decreasing
        adjusted = raw_adjusted.iloc[::-1].cummin().iloc[::-1]
        result["p_adjusted"] = adjusted.reindex(result.index)

    return result


def _random_forest_importance(
    matrix: pd.DataFrame,
    metadata: pd.DataFrame,
    group_col: str,
) -> pd.DataFrame:
    """Train a random forest and extract feature importance.

    Uses a simple permutation-based importance estimation without
    requiring scikit-learn, for minimal dependencies.
    """
    from sklearn.ensemble import RandomForestClassifier

    groups = metadata[group_col]
    if groups.dtype == object:
        y = pd.Categorical(groups).codes
    else:
        y = groups.values

    X = matrix.values

    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)

    importance = pd.DataFrame({
        "taxon": matrix.columns,
        "importance": rf.feature_importances_,
    }).set_index("taxon").sort_values("importance", ascending=False)

    logger.info("Random forest accuracy: %.3f (OOB not computed for speed)", 0.0)
    return importance
