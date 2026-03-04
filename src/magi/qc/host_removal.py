"""Host read removal via minimap2 alignment and samtools filtering."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def remove_host(
    input_path: Path,
    output_path: Path,
    host_reference: Path,
    threads: int = 4,
    platform: str = "hifi",
) -> None:
    """Remove host-derived reads by aligning to a host reference genome.

    Aligns reads to the host reference with minimap2, then extracts
    unmapped reads (non-host) using samtools.

    Args:
        input_path: Path to input FASTQ file.
        output_path: Path to write host-free FASTQ file.
        host_reference: Path to host reference genome (FASTA).
        threads: Number of threads for minimap2 to use.
        platform: Sequencing platform ("hifi" or "nanopore") to select
            the minimap2 alignment preset.

    Raises:
        FileNotFoundError: If input or host reference file does not exist.
        RuntimeError: If minimap2 or samtools returns a non-zero exit code.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    host_reference = Path(host_reference)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not host_reference.exists():
        raise FileNotFoundError(f"Host reference not found: {host_reference}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    bam_path = output_path.with_suffix(".host_aligned.bam")

    # Step 1: Align reads to host reference and convert to BAM
    # minimap2 outputs SAM to stdout, so we pipe it into samtools view
    preset = "map-hifi" if platform == "hifi" else "map-ont"
    minimap2_cmd = [
        "minimap2",
        "-a",
        "-x", preset,
        "-t", str(threads),
        str(host_reference),
        str(input_path),
    ]
    samtools_view_cmd = [
        "samtools", "view", "-b", "-o", str(bam_path), "-",
    ]

    logger.info("Aligning to host reference: %s | %s",
                " ".join(minimap2_cmd), " ".join(samtools_view_cmd))

    minimap2_proc = subprocess.Popen(
        minimap2_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    view_proc = subprocess.Popen(
        samtools_view_cmd,
        stdin=minimap2_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    minimap2_proc.stdout.close()  # Allow minimap2 to receive SIGPIPE
    _, view_stderr = view_proc.communicate()
    minimap2_proc.wait()

    if minimap2_proc.returncode != 0:
        raise RuntimeError(f"minimap2 failed (exit {minimap2_proc.returncode})")
    if view_proc.returncode != 0:
        raise RuntimeError(
            f"samtools view failed (exit {view_proc.returncode}): "
            f"{view_stderr.decode()}"
        )

    # Step 2: Extract unmapped reads (non-host)
    samtools_fastq_cmd = [
        "samtools", "fastq",
        "-f", "4",
        "-0", str(output_path),
        str(bam_path),
    ]

    logger.info("Extracting non-host reads: %s", " ".join(samtools_fastq_cmd))

    result = subprocess.run(samtools_fastq_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"samtools fastq failed (exit {result.returncode}): {result.stderr}"
        )

    # Clean up intermediate BAM
    if bam_path.exists():
        bam_path.unlink()

    logger.info("Host-free reads written to %s", output_path)
