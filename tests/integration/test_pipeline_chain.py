"""Integration tests: verify the full Python module chain works end-to-end."""

import numpy as np

from magi.analysis.cooccurrence import run_cooccurrence
from magi.analysis.differential import run_differential
from magi.analysis.diversity import compute_alpha_diversity, compute_beta_diversity
from magi.metadata.correlation import run_correlation
from magi.reporting.dashboard import generate_dashboard
from magi.reporting.figures import generate_figures
from magi.unifier.matrix import build_feature_matrix
from magi.unifier.normalize import normalize


def test_unifier_to_analysis_chain(synthetic_standardized_tsv, synthetic_metadata):
    """standardized TSVs -> feature matrix -> normalize -> analysis."""
    matrix = build_feature_matrix(synthetic_standardized_tsv)
    assert matrix.shape[0] == 5
    assert matrix.shape[1] == 6

    normalized = normalize(matrix, method="clr")
    assert normalized.shape == matrix.shape
    assert not normalized.isnull().any().any()

    alpha = compute_alpha_diversity(normalized)
    assert "shannon" in alpha.columns
    assert len(alpha) == 5

    beta = compute_beta_diversity(normalized)
    assert beta.shape == (5, 5)
    assert np.allclose(beta.values, beta.values.T)


def test_analysis_to_differential_chain(synthetic_abundance_matrix, synthetic_metadata):
    """abundance matrix -> differential abundance -> results."""
    diff = run_differential(synthetic_abundance_matrix, synthetic_metadata)
    assert "p_value" in diff.columns
    assert "p_adjusted" in diff.columns
    assert len(diff) == 6


def test_analysis_to_metadata_chain(synthetic_abundance_matrix, synthetic_metadata):
    """abundance matrix -> metadata correlation -> results."""
    results = run_correlation(
        synthetic_abundance_matrix,
        synthetic_metadata,
        tools=["spearman"],
        random_forest=True,
    )
    assert "correlations" in results
    assert "feature_importance" in results
    assert len(results["correlations"]) == 6
    assert len(results["feature_importance"]) == 6


def test_analysis_to_reporting_chain(analysis_results_dir, tmp_path):
    """analysis results -> dashboard + figures."""
    output_dir = tmp_path / "report"
    output_dir.mkdir()

    dashboard_path = output_dir / "dashboard.html"
    generate_dashboard(analysis_results_dir, dashboard_path)
    assert dashboard_path.exists()
    html = dashboard_path.read_text()
    assert "MAGI" in html

    figures_dir = output_dir / "figures"
    generate_figures(analysis_results_dir, figures_dir, formats=["png"])
    assert figures_dir.exists()
    pngs = list(figures_dir.glob("*.png"))
    assert len(pngs) >= 2


def test_cooccurrence_network_structure(synthetic_abundance_matrix):
    """network has correct structure with weighted edges."""
    G = run_cooccurrence(synthetic_abundance_matrix, method="sparcc")
    assert G.number_of_nodes() == 6
    for _, _, data in G.edges(data=True):
        assert "weight" in data


def test_full_chain_data_shapes(synthetic_standardized_tsv, synthetic_metadata):
    """complete chain from standardized -> analysis, verify data shapes."""
    matrix = build_feature_matrix(synthetic_standardized_tsv)
    normalized = normalize(matrix, method="relative")

    alpha = compute_alpha_diversity(normalized)
    beta = compute_beta_diversity(normalized)
    diff = run_differential(normalized, synthetic_metadata)
    corr_results = run_correlation(normalized, synthetic_metadata)

    n_samples = 5
    n_taxa = matrix.shape[1]
    assert alpha.shape[0] == n_samples
    assert beta.shape == (n_samples, n_samples)
    assert len(diff) == n_taxa
    assert len(corr_results["correlations"]) == n_taxa
    assert len(corr_results["feature_importance"]) == n_taxa
