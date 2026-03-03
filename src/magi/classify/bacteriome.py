"""Bacterial taxonomic classification."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def classify_bacteriome(
    input_path: Path,
    output_path: Path,
    db_path: Path,
    confidence: float = 0.7,
) -> None:
    """Classify bacterial taxa from metagenomic reads or contigs.

    Uses a reference database (e.g., Kraken2/Bracken with a bacterial DB)
    to assign taxonomic labels to the input sequences at the specified
    confidence threshold.

    Args:
        input_path: Path to the input reads or contigs.
        output_path: Path to write classification results.
        db_path: Path to the bacterial classification database.
        confidence: Minimum confidence score for taxonomic assignment.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info(
        "Classifying bacteriome from %s (db=%s, confidence=%.2f) -> %s",
        input_path, db_path, confidence, output_path,
    )
    raise NotImplementedError("Module not yet implemented")
