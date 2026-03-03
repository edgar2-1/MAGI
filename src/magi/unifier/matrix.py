"""Build a unified feature matrix from standardized outputs."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def build_feature_matrix(input_dir: Path) -> pd.DataFrame:
    """Build a samples-by-features abundance matrix.

    Aggregates all standardized classification outputs into a single
    matrix where rows are samples and columns are taxonomic features,
    suitable for normalization and downstream statistical analysis.

    Args:
        input_dir: Path to the directory containing standardized TSV files.

    Returns:
        A pandas DataFrame with samples as rows and taxonomic features
        as columns, with abundance values as entries.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info("Building feature matrix from %s", input_dir)
    raise NotImplementedError("Module not yet implemented")
