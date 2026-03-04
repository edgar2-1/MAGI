"""Benchmarking tools for evaluating MAGI classification accuracy."""

from magi.benchmarking.metrics import compute_benchmark_metrics, benchmark_report
from magi.benchmarking.mock_communities import MOCK_COMMUNITIES

__all__ = ["compute_benchmark_metrics", "benchmark_report", "MOCK_COMMUNITIES"]
