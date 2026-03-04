import pandas as pd
import pytest

from magi.metadata.correlation import run_correlation

_MATRIX = pd.DataFrame(
    {
        "E.coli": [100, 50, 200, 30, 80, 60],
        "S.aureus": [20, 150, 10, 180, 90, 40],
        "A.niger": [5, 10, 3, 8, 12, 7],
    },
    index=["s1", "s2", "s3", "s4", "s5", "s6"],
)

_METADATA = pd.DataFrame(
    {"group": ["control", "treatment", "control", "treatment", "control", "treatment"]},
    index=["s1", "s2", "s3", "s4", "s5", "s6"],
)


def test_run_correlation_returns_dict():
    result = run_correlation(_MATRIX, _METADATA, tools=["spearman"], random_forest=False)
    assert isinstance(result, dict)
    assert "correlations" in result


def test_spearman_correlations_have_pvalues():
    result = run_correlation(_MATRIX, _METADATA, tools=["spearman"], random_forest=False)
    corr = result["correlations"]
    assert "p_value" in corr.columns
    assert "rho" in corr.columns
    assert "p_adjusted" in corr.columns
    assert len(corr) == 3


def test_random_forest_importance():
    result = run_correlation(_MATRIX, _METADATA, random_forest=True)
    assert "feature_importance" in result
    imp = result["feature_importance"]
    assert "importance" in imp.columns
    assert len(imp) == 3
    # Importances should sum to ~1
    assert abs(imp["importance"].sum() - 1.0) < 0.1


def test_no_shared_samples():
    other_meta = pd.DataFrame({"group": ["a"]}, index=["x99"])
    with pytest.raises(ValueError, match="No shared samples"):
        run_correlation(_MATRIX, other_meta)


def test_fdr_correction_is_monotonic():
    """Adjusted p-values should be monotonically non-decreasing when sorted by raw p."""
    result = run_correlation(_MATRIX, _METADATA, tools=["spearman"], random_forest=False)
    corr = result["correlations"]
    sorted_corr = corr.sort_values("p_value")
    adjusted = sorted_corr["p_adjusted"].values
    # Check monotonicity
    for i in range(1, len(adjusted)):
        assert adjusted[i] >= adjusted[i - 1] - 1e-10, \
            f"FDR not monotonic at index {i}: {adjusted[i]} < {adjusted[i-1]}"
