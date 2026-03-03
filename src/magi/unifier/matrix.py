"""Build unified sample x feature abundance matrices."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def build_feature_matrix(input_dir: Path) -> pd.DataFrame:
    """Build a sample-by-feature abundance matrix from standardized TSVs.

    Reads all standardized TSV files from input_dir and pivots them
    into a matrix where rows are samples and columns are taxa.

    Args:
        input_dir: Directory containing standardized TSV files with
            columns [SampleID, Kingdom, Taxon, NCBI_TaxID, Rank,
            Abundance, Method].

    Returns:
        A pandas DataFrame with samples as rows and taxa as columns,
        filled with abundance values. Missing values are filled with 0.

    Raises:
        FileNotFoundError: If no standardized files are found.
    """
    input_dir = Path(input_dir)
    frames = []

    for tsv_file in input_dir.glob("standardized_*.tsv"):
        df = pd.read_csv(tsv_file, sep="\t")
        frames.append(df)

    if not frames:
        raise FileNotFoundError(
            f"No standardized_*.tsv files found in {input_dir}"
        )

    combined = pd.concat(frames, ignore_index=True)

    matrix = combined.pivot_table(
        index="SampleID",
        columns="Taxon",
        values="Abundance",
        aggfunc="sum",
        fill_value=0.0,
    )

    logger.info(
        "Built feature matrix: %d samples x %d features",
        matrix.shape[0], matrix.shape[1],
    )
    return matrix
