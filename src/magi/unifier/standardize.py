"""Standardize classification outputs into a unified format."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

STANDARD_COLUMNS = [
    "SampleID", "Kingdom", "Taxon", "NCBI_TaxID",
    "Rank", "Abundance", "Method",
]


def standardize_outputs(
    input_dir: Path,
    kingdom: str,
    method: str,
) -> pd.DataFrame:
    """Parse classification output files into a standardized DataFrame.

    Reads Bracken/Kraken2 TSV files from input_dir and converts them
    into the unified MAGI format.

    Args:
        input_dir: Directory containing classification output files.
        kingdom: Kingdom label ("bacteria", "fungi", or "virus").
        method: Classification method used ("kraken2" or "genomad").

    Returns:
        DataFrame with columns: SampleID, Kingdom, Taxon, NCBI_TaxID,
        Rank, Abundance, Method.
    """
    input_dir = Path(input_dir)
    rows = []

    tsv_files = list(input_dir.glob(f"*{kingdom}*.tsv")) or list(input_dir.glob("*.tsv"))

    for tsv_file in tsv_files:
        sample_id = tsv_file.stem.split("_")[0]

        try:
            df = pd.read_csv(tsv_file, sep="\t")
        except Exception as e:
            logger.warning("Could not parse %s: %s", tsv_file, e)
            continue

        if "name" in df.columns and "taxonomy_id" in df.columns:
            for _, row in df.iterrows():
                rows.append({
                    "SampleID": sample_id,
                    "Kingdom": kingdom,
                    "Taxon": row["name"],
                    "NCBI_TaxID": int(row["taxonomy_id"]),
                    "Rank": _map_rank(row.get("taxonomy_lvl", "S")),
                    "Abundance": float(row.get("fraction_total_reads", 0)),
                    "Method": method,
                })

    if not rows:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    result = pd.DataFrame(rows, columns=STANDARD_COLUMNS)
    logger.info(
        "Standardized %d records from %s (%s)",
        len(result), kingdom, method,
    )
    return result


def _map_rank(code: str) -> str:
    """Map single-letter rank codes to full names."""
    rank_map = {
        "D": "domain", "K": "kingdom", "P": "phylum",
        "C": "class", "O": "order", "F": "family",
        "G": "genus", "S": "species",
    }
    return rank_map.get(str(code).upper(), "species")
