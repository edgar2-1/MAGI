"""Fungal taxonomic classification."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def classify_mycobiome(
    input_path: Path,
    output_path: Path,
    db_path: Path,
    confidence: float = 0.7,
) -> None:
    """Classify fungal taxa from metagenomic reads or contigs.

    Uses a fungal reference database to assign taxonomic labels
    to the input sequences at the specified confidence threshold.

    Args:
        input_path: Path to the input reads or contigs.
        output_path: Path to write classification results.
        db_path: Path to the fungal classification database.
        confidence: Minimum confidence score for taxonomic assignment.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info(
        "Classifying mycobiome from %s (db=%s, confidence=%.2f) -> %s",
        input_path, db_path, confidence, output_path,
    )
    raise NotImplementedError("Module not yet implemented")
