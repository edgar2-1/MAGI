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

    # PCoA ordination scatter
    pcoa_path = results_dir / "pcoa_ordination.tsv"
    if pcoa_path.exists():
        pcoa = pd.read_csv(pcoa_path, sep="\t", index_col=0)
        if "PC1" in pcoa.columns and "PC2" in pcoa.columns:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(pcoa["PC1"], pcoa["PC2"], s=60, alpha=0.8, edgecolors="black", linewidth=0.5)
            for sample in pcoa.index:
                ax.annotate(sample, (pcoa.loc[sample, "PC1"], pcoa.loc[sample, "PC2"]),
                           fontsize=7, ha="left", va="bottom")
            ax.set_xlabel("PC1")
            ax.set_ylabel("PC2")
            ax.set_title("PCoA Ordination")
            ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
            ax.axvline(0, color="gray", linewidth=0.5, linestyle="--")
            plt.tight_layout()
            for fmt in formats:
                path = output_path / f"pcoa_ordination.{fmt}"
                fig.savefig(path, dpi=300)
                generated.append(path)
            plt.close(fig)
            logger.info("Generated PCoA ordination plot")

    # Log-ratio biplot (needs the unified matrix, check parent dir)
    matrix_path = results_dir.parent / "unified_matrix.tsv"
    if not matrix_path.exists():
        matrix_path = results_dir / "unified_matrix.tsv"
    if matrix_path.exists():
        generate_biplot(matrix_path, output_path, formats=formats)

    logger.info("Generated %d figures in %s", len(generated), output_path)


def generate_biplot(
    matrix_path: Path,
    output_path: Path,
    formats: Optional[List[str]] = None,
    n_top_taxa: int = 10,
) -> None:
    """Generate a log-ratio biplot showing samples and top taxa loadings.

    Args:
        matrix_path: Path to the unified feature matrix TSV.
        output_path: Directory to write the biplot figure.
        formats: Output formats. Defaults to ["png"].
        n_top_taxa: Number of top taxa to show as arrows.
    """
    import numpy as np

    if formats is None:
        formats = ["png"]

    matrix_path = Path(matrix_path)
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    if not matrix_path.exists():
        logger.warning("Matrix file not found for biplot: %s", matrix_path)
        return

    matrix = pd.read_csv(matrix_path, sep="\t", index_col=0)
    if matrix.shape[1] < 2:
        logger.warning("Need at least 2 taxa for biplot")
        return

    # CLR transform (add pseudocount to handle zeros)
    pseudo = matrix + 1
    log_data = np.log(pseudo)
    clr = log_data.subtract(log_data.mean(axis=1), axis=0)

    # SVD for PCA on CLR-transformed data
    centered = clr - clr.mean()
    U, S, Vt = np.linalg.svd(centered.values, full_matrices=False)

    # Sample scores (first 2 PCs)
    sample_scores = U[:, :2] * S[:2]

    # Taxa loadings (first 2 PCs)
    taxa_loadings = Vt[:2, :].T

    # Select top taxa by loading magnitude
    loading_magnitude = np.sqrt(taxa_loadings[:, 0]**2 + taxa_loadings[:, 1]**2)
    top_idx = np.argsort(loading_magnitude)[-n_top_taxa:]

    # Explained variance
    total_var = np.sum(S**2)
    var_explained = S[:2]**2 / total_var * 100

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Samples
    ax.scatter(sample_scores[:, 0], sample_scores[:, 1], s=60, alpha=0.8,
              edgecolors="black", linewidth=0.5, zorder=3, label="Samples")
    for i, sample in enumerate(matrix.index):
        ax.annotate(sample, (sample_scores[i, 0], sample_scores[i, 1]),
                   fontsize=7, ha="left", va="bottom")

    # Taxa arrows
    scale = np.max(np.abs(sample_scores)) / np.max(np.abs(taxa_loadings[top_idx])) * 0.8
    for idx in top_idx:
        ax.annotate(
            "",
            xy=(taxa_loadings[idx, 0] * scale, taxa_loadings[idx, 1] * scale),
            xytext=(0, 0),
            arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
        )
        ax.text(
            taxa_loadings[idx, 0] * scale * 1.1,
            taxa_loadings[idx, 1] * scale * 1.1,
            matrix.columns[idx],
            color="red", fontsize=8, ha="center", va="center",
        )

    ax.set_xlabel(f"PC1 ({var_explained[0]:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({var_explained[1]:.1f}% variance)")
    ax.set_title("Log-Ratio Biplot")
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.legend()
    plt.tight_layout()

    for fmt in formats:
        path = output_path / f"biplot.{fmt}"
        fig.savefig(path, dpi=300)
    plt.close(fig)
    logger.info("Generated log-ratio biplot")
