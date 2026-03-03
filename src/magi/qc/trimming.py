"""Adapter trimming for long reads using fastp."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def trim_adapters(input_path: Path, output_path: Path) -> None:
    """Trim adapters from reads using fastp's auto-detection.

    Args:
        input_path: Path to input FASTQ file.
        output_path: Path to write trimmed FASTQ file.

    Raises:
        FileNotFoundError: If input file does not exist.
        RuntimeError: If fastp returns a non-zero exit code.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "fastp",
        "--in1", str(input_path),
        "--out1", str(output_path),
        "--detect_adapter_for_pe",
        "--thread", "4",
    ]

    logger.info("Trimming adapters: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"fastp failed (exit {result.returncode}): {result.stderr}")

    logger.info("Trimmed reads written to %s", output_path)
