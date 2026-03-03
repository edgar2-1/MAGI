"""Shared fixtures for integration tests."""

import json

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_abundance_matrix():
    """5 samples x 6 taxa abundance matrix spanning 3 kingdoms."""
    np.random.seed(42)
    taxa = [
        "k__Bacteria;s__E.coli",
        "k__Bacteria;s__S.aureus",
        "k__Fungi;s__C.albicans",
        "k__Fungi;s__A.niger",
        "k__Virus;s__PhageT4",
        "k__Virus;s__SARS_CoV2",
    ]
    data = np.random.randint(0, 500, size=(5, 6)).astype(float)
    data[0, 4] = 0
    data[3, 5] = 0
    return pd.DataFrame(data, index=[f"sample_{i}" for i in range(5)], columns=taxa)


@pytest.fixture
def synthetic_metadata():
    """Metadata for 5 samples with group assignments."""
    return pd.DataFrame(
        {
            "group": ["control", "treatment", "control", "treatment", "control"],
            "age": [25, 30, 45, 28, 55],
            "bmi": [22.1, 28.5, 24.0, 31.2, 26.8],
        },
        index=[f"sample_{i}" for i in range(5)],
    )


@pytest.fixture
def synthetic_standardized_tsv(tmp_path):
    """Write synthetic standardized TSV files as if from the unifier."""
    np.random.seed(42)
    for kingdom in ["bacteria", "fungi", "virus"]:
        rows = []
        for i in range(5):
            for j in range(1, 3):
                rows.append({
                    "SampleID": f"sample_{i}",
                    "Kingdom": kingdom,
                    "Taxon": f"{kingdom}_taxon_{j}",
                    "NCBI_TaxID": 100 * j + i,
                    "Rank": "species",
                    "Abundance": float(np.random.randint(10, 200)),
                    "Method": "kraken2" if kingdom != "virus" else "genomad",
                })
        df = pd.DataFrame(rows)
        df.to_csv(tmp_path / f"standardized_{kingdom}.tsv", sep="\t", index=False)
    return tmp_path


@pytest.fixture
def analysis_results_dir(tmp_path, synthetic_abundance_matrix, synthetic_metadata):
    """Run the full analysis chain and return the results directory."""
    import networkx as nx

    from magi.analysis.cooccurrence import run_cooccurrence
    from magi.analysis.differential import run_differential
    from magi.analysis.diversity import compute_alpha_diversity, compute_beta_diversity

    matrix = synthetic_abundance_matrix

    alpha = compute_alpha_diversity(matrix)
    alpha.to_csv(tmp_path / "alpha_diversity.tsv", sep="\t")

    beta = compute_beta_diversity(matrix)
    beta.to_csv(tmp_path / "beta_diversity.tsv", sep="\t")

    G = run_cooccurrence(matrix, method="sparcc")
    network_data = nx.node_link_data(G)
    with open(tmp_path / "cooccurrence_network.json", "w") as f:
        json.dump(network_data, f)

    diff = run_differential(matrix, synthetic_metadata)
    diff.to_csv(tmp_path / "differential_abundance.tsv", sep="\t")

    return tmp_path
