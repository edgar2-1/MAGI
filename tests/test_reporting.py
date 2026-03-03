from pathlib import Path

import pandas as pd
import pytest

from magi.reporting.dashboard import generate_dashboard
from magi.reporting.figures import generate_figures


def _create_test_results(results_dir: Path) -> None:
    """Helper to create mock analysis results."""
    alpha = pd.DataFrame(
        {"shannon": [2.1, 1.8, 2.3], "simpson": [0.8, 0.7, 0.85]},
        index=["s1", "s2", "s3"],
    )
    alpha.to_csv(results_dir / "alpha_diversity.tsv", sep="\t")

    beta = pd.DataFrame(
        [[0.0, 0.3, 0.5], [0.3, 0.0, 0.4], [0.5, 0.4, 0.0]],
        index=["s1", "s2", "s3"],
        columns=["s1", "s2", "s3"],
    )
    beta.to_csv(results_dir / "beta_diversity.tsv", sep="\t")


def test_generate_dashboard(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _create_test_results(results_dir)

    output = tmp_path / "dashboard.html"
    generate_dashboard(results_dir, output)

    assert output.exists()
    content = output.read_text()
    assert "MAGI" in content
    assert "Alpha Diversity" in content


def test_generate_dashboard_empty_results(tmp_path):
    results_dir = tmp_path / "empty_results"
    results_dir.mkdir()
    output = tmp_path / "dashboard.html"

    generate_dashboard(results_dir, output)
    assert output.exists()
    assert "No results found" in output.read_text()


def test_generate_dashboard_missing_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        generate_dashboard(tmp_path / "nonexistent", tmp_path / "out.html")


def test_generate_figures(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _create_test_results(results_dir)

    output_dir = tmp_path / "figures"
    generate_figures(results_dir, output_dir, formats=["png"])

    assert output_dir.exists()
    assert (output_dir / "alpha_diversity.png").exists()
    assert (output_dir / "beta_diversity.png").exists()


def test_generate_figures_svg(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _create_test_results(results_dir)

    output_dir = tmp_path / "figures"
    generate_figures(results_dir, output_dir, formats=["svg"])

    assert (output_dir / "alpha_diversity.svg").exists()


def test_generate_figures_missing_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        generate_figures(tmp_path / "nonexistent", tmp_path / "figs")
