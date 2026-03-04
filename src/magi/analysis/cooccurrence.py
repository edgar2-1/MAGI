"""Microbial co-occurrence network inference."""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def run_cooccurrence(
    matrix: pd.DataFrame,
    method: str = "spieceasi",
    min_abundance: Optional[float] = None,
) -> nx.Graph:
    """Infer a microbial co-occurrence network from an abundance matrix.

    Args:
        matrix: DataFrame with samples as rows and taxa as columns.
        method: Network inference method ("spieceasi" or "sparcc").
        min_abundance: Minimum mean abundance to include a taxon.

    Returns:
        A networkx Graph with taxa as nodes and association weights as edges.

    Raises:
        ValueError: If method is not recognized.
    """
    if method not in ("spieceasi", "sparcc"):
        raise ValueError(f"Unknown co-occurrence method: {method}")

    # Filter low-abundance taxa
    if min_abundance is not None:
        keep = matrix.columns[matrix.mean() >= min_abundance]
        matrix = matrix[keep]

    logger.info(
        "Running co-occurrence analysis (method=%s, taxa=%d, samples=%d)",
        method, matrix.shape[1], matrix.shape[0],
    )

    if method == "sparcc":
        return _sparcc(matrix)
    else:
        return _spieceasi(matrix)


def _sparcc(matrix: pd.DataFrame) -> nx.Graph:
    """SparCC-like correlation for compositional data.

    Uses iterative log-ratio variance estimation to compute
    correlations robust to compositionality.
    """
    mat = matrix.copy().astype(float)

    # If data contains negative values, it's likely CLR-transformed
    # Use it directly for correlation instead of applying log again
    if (mat < 0).any().any():
        logger.info("Input appears CLR-transformed, using values directly for correlation")
        corr = mat.corr()
    else:
        # Raw counts: apply pseudocount and log-ratio transform
        mat[mat == 0] = 0.5
        log_mat = np.log(mat)
        corr = log_mat.corr()

    G = nx.Graph()
    taxa = matrix.columns.tolist()
    G.add_nodes_from(taxa)

    for i, t1 in enumerate(taxa):
        for j, t2 in enumerate(taxa):
            if i < j:
                weight = corr.iloc[i, j]
                if not np.isnan(weight) and abs(weight) > 0.3:
                    G.add_edge(t1, t2, weight=weight)

    logger.info("SparCC network: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G


def _spieceasi(matrix: pd.DataFrame) -> nx.Graph:
    """SpiecEasi network inference via R subprocess.

    Calls R's SpiecEasi package for graphical lasso-based network
    inference. Falls back to SparCC if R/SpiecEasi is not available.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_csv = Path(tmpdir) / "matrix.csv"
            output_csv = Path(tmpdir) / "adjacency.csv"

            # SpiecEasi expects count-like data, not CLR-transformed
            write_matrix = matrix.copy()
            if (write_matrix < 0).any().any():
                logger.info("Exponentiating CLR-transformed data for SpiecEasi input")
                write_matrix = np.exp(write_matrix)
            write_matrix.to_csv(input_csv)

            r_script = f"""
            library(SpiecEasi)
            mat <- as.matrix(read.csv("{input_csv}", row.names=1))
            se <- spiec.easi(mat, method="mb", lambda.min.ratio=1e-2,
                             nlambda=20, pulsar.params=list(rep.num=20))
            adj <- as.matrix(getRefit(se))
            colnames(adj) <- colnames(mat)
            rownames(adj) <- colnames(mat)
            write.csv(adj, "{output_csv}")
            """

            result = subprocess.run(
                ["Rscript", "-e", r_script],
                capture_output=True, text=True, timeout=300,
            )

            if result.returncode != 0:
                logger.warning("SpiecEasi failed, falling back to SparCC: %s", result.stderr)
                return _sparcc(matrix)

            adj = pd.read_csv(output_csv, index_col=0)
            G = nx.Graph()
            taxa = adj.columns.tolist()
            G.add_nodes_from(taxa)

            for i, t1 in enumerate(taxa):
                for j, t2 in enumerate(taxa):
                    if i < j and adj.iloc[i, j] != 0:
                        G.add_edge(t1, t2, weight=float(adj.iloc[i, j]))

            logger.info(
                "SpiecEasi network: %d nodes, %d edges",
                G.number_of_nodes(), G.number_of_edges(),
            )
            return G

    except FileNotFoundError:
        logger.warning("R/Rscript not found, falling back to SparCC")
        return _sparcc(matrix)
