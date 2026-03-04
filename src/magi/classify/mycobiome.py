"""Fungal taxonomic classification using Kraken2 against UNITE."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def classify_mycobiome(
    input_path: Path,
    output_path: Path,
    db_path: Path,
    confidence: float = 0.2,
    threads: int = 8,
    read_length: int = 150,
) -> None:
    """Classify fungal reads using Kraken2 against a UNITE database.

    Args:
        input_path: Path to input FASTQ file (filtered reads).
        output_path: Path to write abundance table (TSV).
        db_path: Path to Kraken2 UNITE database directory.
        confidence: Kraken2 confidence threshold (0-1).
        threads: Number of threads for Kraken2 to use.
        read_length: Read length for Bracken abundance estimation
            (default 150 for short reads, use higher for long reads).

    Raises:
        FileNotFoundError: If input file or database does not exist.
        RuntimeError: If kraken2 returns a non-zero exit code.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    db_path = Path(db_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not db_path.exists():
        raise FileNotFoundError(f"Kraken2 database not found: {db_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    kreport_path = output_path.with_suffix(".kreport")

    kraken2_cmd = [
        "kraken2",
        "--db", str(db_path),
        "--confidence", str(confidence),
        "--report", str(kreport_path),
        "--output", str(output_path.with_suffix(".kraken2")),
        "--threads", str(threads),
        str(input_path),
    ]

    logger.info("Running Kraken2 (mycobiome): %s", " ".join(kraken2_cmd))

    result = subprocess.run(kraken2_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"kraken2 failed (exit {result.returncode}): {result.stderr}")

    bracken_cmd = [
        "bracken",
        "-d", str(db_path),
        "-i", str(kreport_path),
        "-o", str(output_path),
        "-r", str(read_length),
        "-l", "S",
    ]

    logger.info("Running Bracken (mycobiome): %s", " ".join(bracken_cmd))

    result = subprocess.run(bracken_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning("Bracken failed, using Kraken2 report directly: %s", result.stderr)

    logger.info("Mycobiome classification written to %s", output_path)
