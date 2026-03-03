"""Viral taxonomic classification."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def classify_virome(
    input_path: Path,
    output_path: Path,
    db_path: Path,
    tool: str = "genomad",
) -> None:
    """Classify viral taxa from metagenomic reads or contigs.

    Uses a viral identification tool (e.g., geNomad, VirSorter2) and
    reference database to detect and classify viral sequences.

    Args:
        input_path: Path to the input reads or contigs.
        output_path: Path to write classification results.
        db_path: Path to the viral classification database.
        tool: Viral classification tool to use (e.g., "genomad", "virsorter2").

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info(
        "Classifying virome from %s (db=%s, tool=%s) -> %s",
        input_path, db_path, tool, output_path,
    )
    raise NotImplementedError("Module not yet implemented")
