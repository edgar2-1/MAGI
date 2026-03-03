"""Standardize classification outputs into a common schema."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def standardize_outputs(
    input_dir: Path,
    kingdom: str,
    method: str,
) -> pd.DataFrame:
    """Standardize classifier outputs into a unified tabular format.

    Reads the raw classification output for a given kingdom and method,
    parses it, and returns a DataFrame with a consistent schema suitable
    for downstream merging and analysis.

    Args:
        input_dir: Path to the directory containing raw classification outputs.
        kingdom: Target kingdom (e.g., "bacteria", "fungi", "virus").
        method: Classification method used (e.g., "kraken2", "genomad").

    Returns:
        A pandas DataFrame with columns:
            - SampleID: Identifier for the sample.
            - Kingdom: The biological kingdom.
            - Taxon: Taxonomic name.
            - NCBI_TaxID: NCBI taxonomy identifier.
            - Rank: Taxonomic rank (e.g., species, genus).
            - Abundance: Relative or absolute abundance value.
            - Method: The classification method used.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info(
        "Standardizing outputs from %s (kingdom=%s, method=%s)",
        input_dir, kingdom, method,
    )
    raise NotImplementedError("Module not yet implemented")
