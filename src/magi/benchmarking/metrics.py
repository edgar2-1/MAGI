"""Benchmarking metrics for comparing observed vs expected compositions."""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from scipy.spatial.distance import braycurtis, jensenshannon
from scipy.stats import pearsonr, spearmanr

logger = logging.getLogger(__name__)


def compute_benchmark_metrics(
    observed: pd.Series,
    expected: dict,
    name: Optional[str] = None,
) -> dict:
    """Compare observed abundances against expected mock community composition.

    Args:
        observed: Series with taxa as index and relative abundances as values.
        expected: Dict mapping taxon names to expected relative abundances.
        name: Optional name for the benchmark.

    Returns:
        Dict with benchmark metrics.
    """
    # Align taxa
    all_taxa = sorted(set(observed.index) | set(expected.keys()))
    obs_vec = np.array([observed.get(t, 0.0) for t in all_taxa])
    exp_vec = np.array([expected.get(t, 0.0) for t in all_taxa])

    # Normalize to relative abundances
    if obs_vec.sum() > 0:
        obs_vec = obs_vec / obs_vec.sum()
    if exp_vec.sum() > 0:
        exp_vec = exp_vec / exp_vec.sum()

    # Core metrics
    metrics = {"name": name or "benchmark"}

    # Bray-Curtis dissimilarity
    metrics["bray_curtis"] = float(braycurtis(obs_vec, exp_vec))

    # Jensen-Shannon divergence
    metrics["jensen_shannon"] = float(jensenshannon(obs_vec, exp_vec))

    # L1 distance (total absolute error)
    metrics["l1_distance"] = float(np.sum(np.abs(obs_vec - exp_vec)))

    # Pearson and Spearman correlations (only on shared taxa)
    shared_taxa = [t for t in all_taxa if t in expected and t in observed.index]
    if len(shared_taxa) >= 3:
        shared_obs = np.array([observed.get(t, 0.0) for t in shared_taxa])
        shared_exp = np.array([expected[t] for t in shared_taxa])
        if shared_obs.sum() > 0:
            shared_obs = shared_obs / shared_obs.sum()
        metrics["pearson_r"], metrics["pearson_p"] = pearsonr(shared_obs, shared_exp)
        metrics["spearman_r"], metrics["spearman_p"] = spearmanr(shared_obs, shared_exp)
    else:
        metrics["pearson_r"] = np.nan
        metrics["spearman_r"] = np.nan

    # Detection metrics
    expected_taxa = set(expected.keys())
    observed_taxa = set(observed[observed > 0].index)

    true_positives = expected_taxa & observed_taxa
    false_negatives = expected_taxa - observed_taxa
    false_positives = observed_taxa - expected_taxa

    metrics["true_positives"] = len(true_positives)
    metrics["false_negatives"] = len(false_negatives)
    metrics["false_positives"] = len(false_positives)

    if len(true_positives) + len(false_positives) > 0:
        metrics["precision"] = len(true_positives) / (len(true_positives) + len(false_positives))
    else:
        metrics["precision"] = 0.0

    if len(true_positives) + len(false_negatives) > 0:
        metrics["recall"] = len(true_positives) / (len(true_positives) + len(false_negatives))
    else:
        metrics["recall"] = 0.0

    if metrics["precision"] + metrics["recall"] > 0:
        metrics["f1_score"] = (
            2 * metrics["precision"] * metrics["recall"]
            / (metrics["precision"] + metrics["recall"])
        )
    else:
        metrics["f1_score"] = 0.0

    logger.info(
        "Benchmark %s: BC=%.3f, JSD=%.3f, F1=%.3f, Precision=%.3f, Recall=%.3f",
        metrics["name"], metrics["bray_curtis"], metrics["jensen_shannon"],
        metrics["f1_score"], metrics["precision"], metrics["recall"],
    )

    return metrics


def benchmark_report(metrics_list: list) -> pd.DataFrame:
    """Compile benchmark metrics into a summary DataFrame.

    Args:
        metrics_list: List of metric dicts from compute_benchmark_metrics.

    Returns:
        DataFrame with one row per benchmark.
    """
    return pd.DataFrame(metrics_list).set_index("name")
