"""Metagenomic assembly using metaFlye or hifiasm-meta."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def run_assembly(
    input_path: Path,
    output_path: Path,
    tool: str = "metaflye",
    threads: int = 8,
    platform: str = "hifi",
) -> None:
    """Assemble metagenomic reads into contigs.

    Args:
        input_path: Path to input FASTQ file (filtered reads).
        output_path: Path to write assembled contigs (FASTA).
        tool: Assembly tool ("metaflye" or "hifiasm-meta").
        threads: Number of threads.
        platform: Sequencing platform ("hifi" or "nanopore").

    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If tool is not recognized.
        RuntimeError: If the assembler returns a non-zero exit code.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if tool not in ("metaflye", "hifiasm-meta"):
        raise ValueError(f"Unknown assembly tool: {tool}. Use 'metaflye' or 'hifiasm-meta'.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent / "assembly_work"

    if tool == "metaflye":
        # Select input type flag based on platform
        if platform == "hifi":
            input_flag = "--pacbio-hifi"
        else:
            input_flag = "--nano-hq"
        cmd = [
            "flye",
            "--meta",
            input_flag, str(input_path),
            "--out-dir", str(work_dir),
            "--threads", str(threads),
        ]
    else:
        cmd = [
            "hifiasm_meta",
            "-t", str(threads),
            "-o", str(work_dir / "asm"),
            str(input_path),
        ]

    logger.info("Running %s: %s", tool, " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{tool} failed (exit {result.returncode}): {result.stderr}")

    # Copy main output to expected path
    if tool == "metaflye":
        contigs_src = work_dir / "assembly.fasta"
    else:
        contigs_src = work_dir / "asm.p_ctg.fa"

    if contigs_src.exists():
        import shutil
        shutil.copy2(contigs_src, output_path)

    logger.info("Assembly complete: %s -> %s", tool, output_path)
