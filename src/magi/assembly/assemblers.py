"""Metagenomic assembly using long-read assemblers."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run_assembly(
    input_path: Path,
    output_path: Path,
    tool: str = "metaflye",
) -> None:
    """Assemble metagenomic reads into contigs.

    Runs the specified assembler on the input reads to produce
    assembled contigs for downstream analysis.

    Args:
        input_path: Path to the input FASTQ file with quality-filtered reads.
        output_path: Path to write the assembled contigs (FASTA).
        tool: Assembly tool to use (e.g., "metaflye", "hifiasm-meta").

    Raises:
        NotImplementedError: This module is not yet implemented.
    """
    logger.info(
        "Running assembly with %s on %s -> %s",
        tool, input_path, output_path,
    )
    raise NotImplementedError("Module not yet implemented")
