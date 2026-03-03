"""Adapter trimming for sequencing reads."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def trim_adapters(input_path: Path, output_path: Path) -> None:
    """Trim adapter sequences from sequencing reads.

    Detects and removes residual adapter sequences from the input reads,
    writing the trimmed reads to the output path.

    Args:
        input_path: Path to the input FASTQ file.
        output_path: Path to write the trimmed FASTQ file.

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info("Trimming adapters from %s -> %s", input_path, output_path)
    raise NotImplementedError("Module not yet implemented")
