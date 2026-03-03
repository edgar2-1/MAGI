"""Database download and management for MAGI classification databases."""

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DB_REGISTRY = {
    "bacteria": {
        "name": "Kraken2 GTDB",
        "url": "https://genome-idx.s3.amazonaws.com/kraken/k2_standard_20240605.tar.gz",
        "tool": "kraken2",
        "description": "Standard Kraken2 database for bacterial classification",
    },
    "fungi": {
        "name": "Kraken2 UNITE",
        "url": "https://genome-idx.s3.amazonaws.com/kraken/k2_pluspfp_20240605.tar.gz",
        "tool": "kraken2",
        "description": "Kraken2 PlusPFP database including fungal sequences",
    },
    "virus": {
        "name": "geNomad",
        "url": "https://zenodo.org/records/8339387/files/genomad_db_v1.5.tar.gz",
        "tool": "genomad",
        "description": "geNomad database for viral identification",
    },
}


def download_database(kingdom: str, db_dir: Path) -> Path:
    """Download a reference database for a given kingdom.

    Args:
        kingdom: One of "bacteria", "fungi", "virus".
        db_dir: Base directory for storing databases.

    Returns:
        Path to the downloaded database directory.

    Raises:
        ValueError: If kingdom is not recognized.
        RuntimeError: If download fails.
    """
    if kingdom not in DB_REGISTRY:
        raise ValueError(f"Unknown kingdom: {kingdom}. Choose from: {list(DB_REGISTRY.keys())}")

    entry = DB_REGISTRY[kingdom]
    target_dir = Path(db_dir) / kingdom
    target_dir.mkdir(parents=True, exist_ok=True)

    url = entry["url"]
    archive = target_dir / url.split("/")[-1]

    logger.info("Downloading %s database from %s", entry["name"], url)

    # Download
    cmd_download = ["curl", "-L", "-o", str(archive), url]
    result = subprocess.run(cmd_download, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Download failed for {kingdom}: {result.stderr}")

    # Extract
    cmd_extract = ["tar", "-xzf", str(archive), "-C", str(target_dir)]
    result = subprocess.run(cmd_extract, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning("Extraction warning: %s", result.stderr)

    # Clean up archive
    if archive.exists():
        archive.unlink()

    # Write manifest
    manifest = {
        "kingdom": kingdom,
        "name": entry["name"],
        "source": url,
        "tool": entry["tool"],
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    (target_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    logger.info("Database installed: %s -> %s", entry["name"], target_dir)
    return target_dir


def get_db_status(db_dir: Path) -> dict:
    """Check installation status of all databases.

    Args:
        db_dir: Base directory for databases.

    Returns:
        Dict keyed by kingdom with installation status.
    """
    db_dir = Path(db_dir)
    status = {}

    for kingdom, entry in DB_REGISTRY.items():
        kingdom_dir = db_dir / kingdom
        manifest_path = kingdom_dir / "manifest.json"

        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            status[kingdom] = {
                "installed": True,
                "name": entry["name"],
                "path": str(kingdom_dir),
                "downloaded_at": manifest.get("downloaded_at", "unknown"),
            }
        else:
            status[kingdom] = {
                "installed": False,
                "name": entry["name"],
                "path": str(kingdom_dir),
            }

    return status
