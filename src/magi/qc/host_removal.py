"""Host genome removal from metagenomic reads."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def remove_host(
    input_path: Path,
    output_path: Path,
    host_reference: Path,
) -> None:
    """Remove host-derived reads by mapping against a reference genome.

    Aligns the input reads to the host reference genome and discards
    any reads that map, retaining only non-host metagenomic reads.

    Args:
        input_path: Path to the input FASTQ file.
        output_path: Path to write the decontaminated FASTQ file.
        host_reference: Path to the host reference genome (FASTA).

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info(
        "Removing host reads from %s using reference %s -> %s",
        input_path, host_reference, output_path,
    )
    raise NotImplementedError("Module not yet implemented")
