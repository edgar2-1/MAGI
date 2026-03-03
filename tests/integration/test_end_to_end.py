"""End-to-end test: simulate the full MAGI pipeline (Python modules only).

Uses the example dataset to run through unifier -> analysis -> metadata
correlation -> benchmarking -> reporting, validating outputs at each stage.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from magi.analysis.cooccurrence import run_cooccurrence
from magi.analysis.differential import run_differential
from magi.analysis.diversity import compute_alpha_diversity, compute_beta_diversity
from magi.benchmarking.metrics import compute_benchmark_metrics, benchmark_report
from magi.metadata.correlation import run_correlation
from magi.reporting.dashboard import generate_dashboard
from magi.reporting.figures import generate_figures
from magi.unifier.matrix import build_feature_matrix
from magi.unifier.normalize import normalize


@pytest.fixture
def example_data_dir():
    """Path to the example dataset."""
    path = Path(__file__).parent.parent.parent / "examples" / "data"
    if not path.exists():
        pytest.skip("Example data not found")
    return path


@pytest.fixture
def example_metadata(example_data_dir):
    """Load example metadata."""
    return pd.read_csv(
        example_data_dir / "metadata.tsv", sep="\t", index_col="sample_id"
    )


def test_e2e_full_pipeline(example_data_dir, example_metadata, tmp_path):
    """Run the complete pipeline chain on example data."""
    # --- Stage 1: Unification ---
    matrix = build_feature_matrix(example_data_dir)
    assert matrix.shape[0] == 10, f"Expected 10 samples, got {matrix.shape[0]}"
    assert matrix.shape[1] == 12, f"Expected 12 taxa, got {matrix.shape[1]}"

    # Normalize with CLR
    normalized_clr = normalize(matrix, method="clr")
    assert normalized_clr.shape == matrix.shape

    # Normalize with relative (for diversity, which needs non-negative)
    normalized_rel = normalize(matrix, method="relative")
    assert (normalized_rel >= 0).all().all()
    row_sums = normalized_rel.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-10)

    # --- Stage 2: Analysis ---
    # Alpha diversity
    alpha = compute_alpha_diversity(normalized_rel)
    assert alpha.shape == (10, 3)  # 3 default metrics
    assert (alpha["shannon"] > 0).all()
    assert (alpha["simpson"] >= 0).all() and (alpha["simpson"] <= 1).all()

    alpha.to_csv(tmp_path / "alpha_diversity.tsv", sep="\t")

    # Beta diversity
    beta = compute_beta_diversity(normalized_rel)
    assert beta.shape == (10, 10)
    assert np.allclose(beta.values, beta.values.T)
    for i in range(10):
        assert abs(beta.iloc[i, i]) < 1e-10

    beta.to_csv(tmp_path / "beta_diversity.tsv", sep="\t")

    # Co-occurrence network
    G = run_cooccurrence(normalized_rel, method="sparcc")
    assert G.number_of_nodes() == 12
    assert G.number_of_edges() > 0

    import networkx as nx
    network_data = nx.node_link_data(G)
    with open(tmp_path / "cooccurrence_network.json", "w") as f:
        json.dump(network_data, f)

    # Differential abundance
    diff = run_differential(normalized_rel, example_metadata, group_col="group")
    assert len(diff) == 12
    assert "p_value" in diff.columns
    assert "p_adjusted" in diff.columns
    assert "mean_healthy" in diff.columns
    assert "mean_disease" in diff.columns

    diff.to_csv(tmp_path / "differential_abundance.tsv", sep="\t")

    # --- Stage 3: Metadata correlation ---
    corr = run_correlation(
        normalized_rel, example_metadata, tools=["spearman"], random_forest=True
    )
    assert "correlations" in corr
    assert "feature_importance" in corr
    assert len(corr["correlations"]) == 12
    assert len(corr["feature_importance"]) == 12

    # --- Stage 4: Reporting ---
    dashboard_path = tmp_path / "dashboard.html"
    generate_dashboard(tmp_path, dashboard_path)
    assert dashboard_path.exists()
    html = dashboard_path.read_text()
    assert len(html) > 1000
    assert "MAGI" in html

    figures_dir = tmp_path / "figures"
    generate_figures(tmp_path, figures_dir, formats=["png"])
    pngs = list(figures_dir.glob("*.png"))
    assert len(pngs) >= 2


def test_e2e_benchmarking(example_data_dir):
    """Run benchmarking on example data against a synthetic 'expected' community."""
    matrix = build_feature_matrix(example_data_dir)

    # Create a synthetic "expected" community from the first sample
    sample_0 = matrix.iloc[0]
    total = sample_0.sum()
    expected = {taxon: float(val / total) for taxon, val in sample_0.items() if val > 0}

    # Benchmark the second sample against the first
    observed = matrix.iloc[1]
    metrics = compute_benchmark_metrics(observed, expected, name="e2e_bench")

    assert 0 <= metrics["bray_curtis"] <= 1.0
    assert 0 <= metrics["jensen_shannon"] <= 1.0
    assert metrics["true_positives"] >= 0
    assert 0 <= metrics["f1_score"] <= 1.0

    report = benchmark_report([metrics])
    assert len(report) == 1
    assert "bray_curtis" in report.columns


def test_e2e_normalization_methods(example_data_dir):
    """Verify all normalization methods produce valid output."""
    matrix = build_feature_matrix(example_data_dir)

    for method in ["clr", "relative", "tss"]:
        normalized = normalize(matrix, method=method)
        assert normalized.shape == matrix.shape
        assert not normalized.isnull().any().any(), f"{method} produced NaN values"
