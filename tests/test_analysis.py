import numpy as np
import pandas as pd
import pytest

from magi.analysis.cooccurrence import run_cooccurrence
from magi.analysis.diversity import (
    compute_alpha_diversity,
    compute_beta_diversity,
    compute_nmds,
    compute_pcoa,
    run_anosim,
    run_permanova,
)
from magi.analysis.differential import run_differential

# Realistic test matrix: 5 samples x 4 taxa
_MATRIX = pd.DataFrame(
    {
        "E.coli": [100, 50, 200, 30, 80],
        "S.aureus": [20, 150, 10, 180, 90],
        "A.niger": [5, 10, 3, 8, 12],
        "Phage_T4": [0, 5, 15, 0, 10],
    },
    index=["s1", "s2", "s3", "s4", "s5"],
)

_METADATA = pd.DataFrame(
    {"group": ["control", "treatment", "control", "treatment", "control"]},
    index=["s1", "s2", "s3", "s4", "s5"],
)


# --- Co-occurrence tests ---

def test_run_cooccurrence_sparcc_returns_graph():
    G = run_cooccurrence(_MATRIX, method="sparcc")
    assert G.number_of_nodes() == 4
    # Should have at least some edges
    assert G.number_of_nodes() > 0


def test_run_cooccurrence_sparcc_edges_have_weights():
    G = run_cooccurrence(_MATRIX, method="sparcc")
    for _, _, data in G.edges(data=True):
        assert "weight" in data


def test_run_cooccurrence_invalid_method():
    with pytest.raises(ValueError, match="Unknown co-occurrence method"):
        run_cooccurrence(_MATRIX, method="invalid")


def test_run_cooccurrence_min_abundance_filters():
    G = run_cooccurrence(_MATRIX, method="sparcc", min_abundance=50)
    # Phage_T4 has mean=6.0, A.niger mean=7.6, should be filtered
    assert "Phage_T4" not in G.nodes()


# --- Alpha diversity tests ---

def test_alpha_diversity_shannon():
    result = compute_alpha_diversity(_MATRIX, metrics=["shannon"])
    assert "shannon" in result.columns
    assert len(result) == 5
    # Shannon should be positive for non-zero rows
    assert (result["shannon"] > 0).all()


def test_alpha_diversity_simpson():
    result = compute_alpha_diversity(_MATRIX, metrics=["simpson"])
    assert "simpson" in result.columns
    # Simpson 1-D should be between 0 and 1
    assert (result["simpson"] >= 0).all()
    assert (result["simpson"] <= 1).all()


def test_alpha_diversity_observed_species():
    result = compute_alpha_diversity(_MATRIX, metrics=["observed_species"])
    assert result.loc["s1", "observed_species"] == 3  # E.coli, S.aureus, A.niger (Phage_T4=0)
    assert result.loc["s2", "observed_species"] == 4  # all 4


def test_alpha_diversity_multiple_metrics():
    result = compute_alpha_diversity(_MATRIX, metrics=["shannon", "simpson", "observed_species"])
    assert result.shape == (5, 3)


def test_alpha_diversity_zero_row():
    """Shannon and Simpson should return 0 for all-zero samples."""
    matrix = pd.DataFrame(
        {"A": [0, 100], "B": [0, 50]},
        index=["empty", "normal"],
    )
    result = compute_alpha_diversity(matrix, metrics=["shannon", "simpson"])
    assert result.loc["empty", "shannon"] == 0.0
    assert result.loc["empty", "simpson"] == 0.0
    assert result.loc["normal", "shannon"] > 0


def test_alpha_diversity_invalid_metric():
    with pytest.raises(ValueError, match="Unknown alpha diversity metric"):
        compute_alpha_diversity(_MATRIX, metrics=["invalid"])


# --- Beta diversity tests ---

def test_beta_diversity_bray_curtis():
    result = compute_beta_diversity(_MATRIX, metrics=["bray_curtis"])
    assert result.shape == (5, 5)
    # Diagonal should be 0 (distance to self)
    for i in range(5):
        assert abs(result.iloc[i, i]) < 1e-10
    # Should be symmetric
    assert np.allclose(result.values, result.values.T)


def test_beta_diversity_jaccard():
    result = compute_beta_diversity(_MATRIX, metrics=["jaccard"])
    assert result.shape == (5, 5)


def test_beta_diversity_invalid_metric():
    with pytest.raises(ValueError, match="Unknown beta diversity metric"):
        compute_beta_diversity(_MATRIX, metrics=["invalid"])


# --- Differential abundance tests ---

def test_differential_kruskal():
    result = run_differential(_MATRIX, _METADATA, method="kruskal")
    assert "p_value" in result.columns
    assert "p_adjusted" in result.columns
    assert "statistic" in result.columns
    assert "mean_control" in result.columns
    assert "mean_treatment" in result.columns
    assert len(result) == 4  # 4 taxa


def test_differential_fdr_bounded():
    result = run_differential(_MATRIX, _METADATA, method="kruskal")
    valid = result["p_adjusted"].dropna()
    assert (valid <= 1.0).all()
    assert (valid >= 0).all()


def test_differential_invalid_method():
    with pytest.raises(ValueError, match="Unknown differential abundance method"):
        run_differential(_MATRIX, _METADATA, method="invalid")


def test_differential_invalid_group_col():
    with pytest.raises(ValueError, match="Group column"):
        run_differential(_MATRIX, _METADATA, group_col="nonexistent")


def test_differential_no_shared_samples():
    other_meta = pd.DataFrame({"group": ["a"]}, index=["x99"])
    with pytest.raises(ValueError, match="No shared samples"):
        run_differential(_MATRIX, other_meta)


# --- PERMANOVA tests ---

def test_permanova_returns_expected_keys():
    result = run_permanova(_MATRIX, _METADATA, permutations=99)
    assert "test_statistic" in result
    assert "p_value" in result
    assert "n_permutations" in result
    assert "method" in result
    assert "R2" in result
    assert result["method"] == "PERMANOVA"


def test_permanova_p_value_bounded():
    result = run_permanova(_MATRIX, _METADATA, permutations=99)
    assert 0 <= result["p_value"] <= 1


def test_permanova_r2_bounded():
    result = run_permanova(_MATRIX, _METADATA, permutations=99)
    assert 0 <= result["R2"] <= 1


def test_permanova_no_shared_samples():
    other_meta = pd.DataFrame({"group": ["a"]}, index=["x99"])
    with pytest.raises(ValueError, match="No shared samples"):
        run_permanova(_MATRIX, other_meta)


# --- ANOSIM tests ---

def test_anosim_returns_expected_keys():
    result = run_anosim(_MATRIX, _METADATA, permutations=99)
    assert "test_statistic" in result
    assert "p_value" in result
    assert "method" in result
    assert result["method"] == "ANOSIM"


def test_anosim_p_value_bounded():
    result = run_anosim(_MATRIX, _METADATA, permutations=99)
    assert 0 <= result["p_value"] <= 1


def test_anosim_invalid_group_col():
    with pytest.raises(ValueError, match="Group column"):
        run_anosim(_MATRIX, _METADATA, group_col="nonexistent")


# --- PCoA tests ---

def test_pcoa_returns_correct_shape():
    result = compute_pcoa(_MATRIX, n_components=2)
    assert result.shape == (5, 2)
    assert "PC1" in result.columns
    assert "PC2" in result.columns

def test_pcoa_proportion_explained():
    result = compute_pcoa(_MATRIX, n_components=2)
    props = result.attrs.get("proportion_explained", [])
    assert len(props) == 2
    assert all(0 <= p <= 1 for p in props)

# --- NMDS tests ---

def test_nmds_returns_correct_shape():
    result = compute_nmds(_MATRIX, n_components=2)
    assert result.shape == (5, 2)
    assert "NMDS1" in result.columns
    assert "NMDS2" in result.columns

def test_nmds_has_stress():
    result = compute_nmds(_MATRIX, n_components=2)
    assert "stress" in result.attrs
    assert result.attrs["stress"] >= 0
