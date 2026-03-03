"""Static publication-ready figure generation using matplotlib and seaborn."""

import logging
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)


def generate_figures(
    results_dir: Path,
    output_path: Path,
    formats: Optional[List[str]] = None,
) -> None:
    """Generate static publication-quality figures from analysis results.

    Args:
        results_dir: Directory containing analysis result files.
        output_path: Directory to write figures.
        formats: Output formats (e.g., ["png", "svg"]). Defaults to ["png"].

    Raises:
        FileNotFoundError: If results_dir does not exist.
    """
    results_dir = Path(results_dir)
    output_path = Path(output_path)

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    if formats is None:
        formats = ["png"]

    output_path.mkdir(parents=True, exist_ok=True)
    generated = []

    # Alpha diversity box plot
    alpha_path = results_dir / "alpha_diversity.tsv"
    if alpha_path.exists():
        alpha = pd.read_csv(alpha_path, sep="\t", index_col=0)
        fig, ax = plt.subplots(figsize=(8, 5))
        alpha.plot(kind="bar", ax=ax)
        ax.set_title("Alpha Diversity")
        ax.set_xlabel("Sample")
        ax.set_ylabel("Diversity Index")
        ax.legend(title="Metric")
        plt.tight_layout()
        for fmt in formats:
            path = output_path / f"alpha_diversity.{fmt}"
            fig.savefig(path, dpi=300)
            generated.append(path)
        plt.close(fig)
        logger.info("Generated alpha diversity figure")

    # Beta diversity heatmap
    beta_path = results_dir / "beta_diversity.tsv"
    if beta_path.exists():
        beta = pd.read_csv(beta_path, sep="\t", index_col=0)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(beta, annot=True, fmt=".2f", cmap="viridis", ax=ax)
        ax.set_title("Beta Diversity (Bray-Curtis)")
        plt.tight_layout()
        for fmt in formats:
            path = output_path / f"beta_diversity.{fmt}"
            fig.savefig(path, dpi=300)
            generated.append(path)
        plt.close(fig)
        logger.info("Generated beta diversity heatmap")

    # Differential abundance
    diff_path = results_dir / "differential_abundance.tsv"
    if diff_path.exists():
        diff = pd.read_csv(diff_path, sep="\t", index_col=0)
        if "p_adjusted" in diff.columns:
            import numpy as np
            fig, ax = plt.subplots(figsize=(8, 5))
            sig = diff["p_adjusted"] < 0.05
            ax.scatter(
                diff.loc[~sig, "statistic"],
                -np.log10(diff.loc[~sig, "p_adjusted"].clip(lower=1e-300)),
                color="gray", alpha=0.6, label="Not significant",
            )
            ax.scatter(
                diff.loc[sig, "statistic"],
                -np.log10(diff.loc[sig, "p_adjusted"].clip(lower=1e-300)),
                color="red", alpha=0.8, label="Significant (p<0.05)",
            )
            ax.axhline(-np.log10(0.05), color="red", linestyle="--", alpha=0.5)
            ax.set_xlabel("Test Statistic")
            ax.set_ylabel("-log10(adjusted p-value)")
            ax.set_title("Differential Abundance")
            ax.legend()
            plt.tight_layout()
            for fmt in formats:
                path = output_path / f"differential_abundance.{fmt}"
                fig.savefig(path, dpi=300)
                generated.append(path)
            plt.close(fig)
            logger.info("Generated differential abundance plot")

    logger.info("Generated %d figures in %s", len(generated), output_path)
