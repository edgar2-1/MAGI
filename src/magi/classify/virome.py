"""Viral identification and classification using geNomad or VirSorter2."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def classify_virome(
    input_path: Path,
    output_path: Path,
    db_path: Path,
    tool: str = "genomad",
    threads: int = 8,
) -> None:
    """Identify and classify viral sequences using geNomad or VirSorter2.

    Args:
        input_path: Path to input FASTQ/FASTA file.
        output_path: Path to write viral abundance table (TSV).
        db_path: Path to geNomad or VirSorter2 database directory.
        tool: Viral identification tool ("genomad" or "virsorter2").
        threads: Number of threads for the viral identification tool.

    Raises:
        FileNotFoundError: If input file or database does not exist.
        ValueError: If tool is not "genomad" or "virsorter2".
        RuntimeError: If the tool returns a non-zero exit code.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    db_path = Path(db_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if tool not in ("genomad", "virsorter2"):
        raise ValueError(f"Unknown virome tool: {tool}. Use 'genomad' or 'virsorter2'.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent / "virome_work"

    if tool == "genomad":
        cmd = [
            "genomad", "end-to-end",
            "--cleanup",
            "--threads", str(threads),
            str(input_path),
            str(work_dir),
            str(db_path),
        ]
    else:
        cmd = [
            "virsorter", "run",
            "--seqfile", str(input_path),
            "--db-dir", str(db_path),
            "--working-dir", str(work_dir),
            "--jobs", str(threads),
            "--include-groups", "dsDNAphage,NCLDV,RNA,ssDNA,lavidaviridae",
        ]

    logger.info("Running %s: %s", tool, " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{tool} failed (exit {result.returncode}): {result.stderr}")

    # Parse and copy results to expected output path
    if tool == "genomad":
        # geNomad writes results to work_dir/<input_stem>_summary/
        input_stem = input_path.stem
        summary_dir = work_dir / f"{input_stem}_summary"
        virus_summary = summary_dir / f"{input_stem}_virus_summary.tsv"
        if not virus_summary.exists():
            # Try alternate location
            virus_summary = work_dir / f"{input_stem}_virus_summary.tsv"
        if virus_summary.exists():
            import shutil
            shutil.copy2(virus_summary, output_path)
        else:
            # Create empty output if no viruses found
            output_path.write_text("name\ttaxonomy_id\ttaxonomy_lvl\tabundance\n")
            logger.warning("No viral sequences found by geNomad")
    else:
        # VirSorter2 writes to work_dir/final-viral-score.tsv
        virsorter_out = work_dir / "final-viral-score.tsv"
        if virsorter_out.exists():
            import shutil
            shutil.copy2(virsorter_out, output_path)
        else:
            output_path.write_text("name\ttaxonomy_id\ttaxonomy_lvl\tabundance\n")
            logger.warning("No viral sequences found by VirSorter2")

    logger.info("Virome classification written to %s", output_path)
