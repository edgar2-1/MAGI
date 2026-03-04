"""Quality filtering of long reads using fastp."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def filter_reads(
    input_path: Path,
    output_path: Path,
    min_quality: int = 20,
    min_length: int = 1000,
    max_length: Optional[int] = None,
    platform: str = "hifi",
    threads: int = 4,
) -> None:
    """Filter reads by quality and length using fastp.

    Args:
        input_path: Path to input FASTQ file.
        output_path: Path to write filtered FASTQ file.
        min_quality: Minimum average quality score to keep a read.
        min_length: Minimum read length to keep.
        max_length: Maximum read length to keep. None means no upper limit.
        platform: Sequencing platform ("hifi" or "nanopore").
        threads: Number of threads for fastp to use.

    Raises:
        FileNotFoundError: If input file does not exist.
        RuntimeError: If fastp returns a non-zero exit code.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_report = output_path.with_suffix(".fastp.json")
    html_report = output_path.with_suffix(".fastp.html")

    cmd = [
        "fastp",
        "--in1", str(input_path),
        "--out1", str(output_path),
        "--json", str(json_report),
        "--html", str(html_report),
        "--qualified_quality_phred", str(min_quality),
        "--length_required", str(min_length),
        "--thread", str(threads),
        "--disable_adapter_trimming",
    ]

    if max_length is not None:
        cmd.extend(["--length_limit", str(max_length)])

    logger.info("Running fastp: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"fastp failed (exit {result.returncode}): {result.stderr}")

    logger.info("Filtered reads written to %s", output_path)
