import pandas as pd

from magi.benchmarking.metrics import compute_benchmark_metrics, benchmark_report
from magi.benchmarking.mock_communities import MOCK_COMMUNITIES, ZYMO_D6300


def test_mock_communities_registry():
    assert "zymo_d6300" in MOCK_COMMUNITIES
    assert "zymo_d6331" in MOCK_COMMUNITIES


def test_zymo_d6300_sums_to_one():
    total = sum(ZYMO_D6300["expected"].values()) + sum(ZYMO_D6300["expected_fungi"].values())
    assert abs(total - 1.0) < 0.01


def test_perfect_match():
    expected = {"A": 0.5, "B": 0.3, "C": 0.2}
    observed = pd.Series({"A": 50, "B": 30, "C": 20})
    metrics = compute_benchmark_metrics(observed, expected, name="perfect")
    assert metrics["bray_curtis"] < 0.01
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0


def test_partial_detection():
    expected = {"A": 0.5, "B": 0.3, "C": 0.2}
    observed = pd.Series({"A": 50, "B": 30})  # Missing C
    metrics = compute_benchmark_metrics(observed, expected, name="partial")
    assert metrics["recall"] < 1.0
    assert metrics["true_positives"] == 2
    assert metrics["false_negatives"] == 1


def test_false_positives():
    expected = {"A": 0.5, "B": 0.5}
    observed = pd.Series({"A": 50, "B": 50, "X": 10, "Y": 5})
    metrics = compute_benchmark_metrics(observed, expected, name="fp")
    assert metrics["false_positives"] == 2
    assert metrics["precision"] < 1.0


def test_correlation_metrics():
    expected = {"A": 0.5, "B": 0.3, "C": 0.2}
    observed = pd.Series({"A": 45, "B": 35, "C": 20})
    metrics = compute_benchmark_metrics(observed, expected)
    assert metrics["pearson_r"] > 0.9
    assert metrics["spearman_r"] > 0.9


def test_jensen_shannon_bounded():
    expected = {"A": 0.5, "B": 0.5}
    observed = pd.Series({"A": 100, "B": 0, "C": 50})
    metrics = compute_benchmark_metrics(observed, expected)
    assert 0 <= metrics["jensen_shannon"] <= 1.0


def test_benchmark_report():
    m1 = compute_benchmark_metrics(
        pd.Series({"A": 50, "B": 50}), {"A": 0.5, "B": 0.5}, name="test1"
    )
    m2 = compute_benchmark_metrics(
        pd.Series({"A": 100}), {"A": 0.5, "B": 0.5}, name="test2"
    )
    report = benchmark_report([m1, m2])
    assert len(report) == 2
    assert "bray_curtis" in report.columns
    assert "f1_score" in report.columns
