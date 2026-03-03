"""Interactive HTML dashboard generation using Plotly."""

import json
import logging
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


def generate_dashboard(results_dir: Path, output_path: Path) -> None:
    """Generate an interactive HTML dashboard from analysis results.

    Reads analysis outputs (diversity, co-occurrence, differential abundance)
    and produces a self-contained HTML file with interactive Plotly charts.

    Args:
        results_dir: Directory containing analysis result files.
        output_path: Path to write the HTML dashboard.

    Raises:
        FileNotFoundError: If results_dir does not exist.
    """
    results_dir = Path(results_dir)
    output_path = Path(output_path)

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    figs = []

    # Alpha diversity bar chart
    alpha_path = results_dir / "alpha_diversity.tsv"
    if alpha_path.exists():
        alpha = pd.read_csv(alpha_path, sep="\t", index_col=0)
        alpha_reset = alpha.reset_index()
        x_col = alpha_reset.columns[0]
        fig = px.bar(
            alpha_reset,
            x=x_col,
            y=alpha.columns.tolist(),
            barmode="group",
            title="Alpha Diversity by Sample",
            labels={"index": "Sample", "value": "Diversity", "variable": "Metric"},
        )
        figs.append(fig)
        logger.info("Added alpha diversity chart")

    # Beta diversity heatmap
    beta_path = results_dir / "beta_diversity.tsv"
    if beta_path.exists():
        beta = pd.read_csv(beta_path, sep="\t", index_col=0)
        fig = px.imshow(
            beta,
            title="Beta Diversity (Bray-Curtis)",
            color_continuous_scale="Viridis",
            labels={"color": "Distance"},
        )
        figs.append(fig)
        logger.info("Added beta diversity heatmap")

    # Differential abundance volcano plot
    diff_path = results_dir / "differential_abundance.tsv"
    if diff_path.exists():
        diff = pd.read_csv(diff_path, sep="\t", index_col=0)
        if "p_adjusted" in diff.columns and "statistic" in diff.columns:
            import numpy as np
            diff["-log10_padj"] = -np.log10(diff["p_adjusted"].clip(lower=1e-300))
            fig = px.scatter(
                diff.reset_index(),
                x="statistic",
                y="-log10_padj",
                hover_name="taxon",
                title="Differential Abundance",
                labels={"statistic": "Test Statistic", "-log10_padj": "-log10(adjusted p-value)"},
            )
            fig.add_hline(y=-np.log10(0.05), line_dash="dash", line_color="red",
                          annotation_text="p=0.05")
            figs.append(fig)
            logger.info("Added differential abundance plot")

    # Co-occurrence network
    network_path = results_dir / "cooccurrence_network.json"
    if network_path.exists():
        import networkx as nx
        with open(network_path) as f:
            network_data = json.load(f)
        G = nx.node_link_graph(network_data)
        if G.number_of_nodes() > 0:
            pos = nx.spring_layout(G, seed=42)
            edge_x, edge_y = [], []
            for e in G.edges():
                x0, y0 = pos[e[0]]
                x1, y1 = pos[e[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            node_x = [pos[n][0] for n in G.nodes()]
            node_y = [pos[n][1] for n in G.nodes()]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y, mode="lines",
                line=dict(width=0.5, color="#888"),
                hoverinfo="none",
            ))
            fig.add_trace(go.Scatter(
                x=node_x, y=node_y, mode="markers+text",
                text=list(G.nodes()), textposition="top center",
                marker=dict(size=10, color="steelblue"),
                hoverinfo="text",
            ))
            fig.update_layout(title="Co-occurrence Network", showlegend=False,
                              xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
            figs.append(fig)
            logger.info("Added co-occurrence network visualization")

    # Combine into single HTML
    if not figs:
        logger.warning("No analysis results found to visualize")
        output_path.write_text("<html><body><h1>MAGI Report</h1><p>No results found.</p></body></html>")
        return

    html_parts = [
        "<html><head><title>MAGI Dashboard</title></head><body>",
        "<h1>MAGI - Multi-kingdom Analysis of Genomic Interactions</h1>",
    ]
    for fig in figs:
        html_parts.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))
    html_parts.append("</body></html>")

    output_path.write_text("\n".join(html_parts))
    logger.info("Dashboard written to %s", output_path)
