"""Configuration and dependency validation for the MAGI pipeline."""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

logger = logging.getLogger(__name__)

REQUIRED_TOOLS = {
    "fastp": "Read quality control",
    "minimap2": "Host read removal",
    "samtools": "BAM/FASTQ handling",
    "kraken2": "Bacterial/fungal classification",
    "bracken": "Abundance re-estimation",
    "genomad": "Viral identification",
    "snakemake": "Workflow orchestration",
}

OPTIONAL_TOOLS = {
    "flye": "Metagenomic assembly (metaFlye)",
    "hifiasm_meta": "HiFi metagenomic assembly",
}

REQUIRED_CONFIG_KEYS = ["samples", "output_dir"]


def check_tools(include_optional: bool = False) -> List[Dict[str, str]]:
    """Check availability of external tools.

    Returns:
        List of dicts with keys: tool, description, status ("found"/"missing"), path.
    """
    results = []
    tools = dict(REQUIRED_TOOLS)
    if include_optional:
        tools.update(OPTIONAL_TOOLS)

    for tool, desc in tools.items():
        path = shutil.which(tool)
        results.append({
            "tool": tool,
            "description": desc,
            "status": "found" if path else "missing",
            "path": path or "",
            "required": tool in REQUIRED_TOOLS,
        })

    return results


def validate_config(config_path: Path) -> Tuple[List[str], List[str]]:
    """Validate a MAGI configuration file.

    Args:
        config_path: Path to YAML config file.

    Returns:
        Tuple of (errors, warnings).
    """
    errors = []
    warnings = []

    config_path = Path(config_path)
    if not config_path.exists():
        errors.append(f"Config file not found: {config_path}")
        return errors, warnings

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors, warnings

    if config is None:
        errors.append("Config file is empty")
        return errors, warnings

    if not isinstance(config, dict):
        errors.append("Config must be a YAML mapping (dict)")
        return errors, warnings

    # Check required keys
    for key in REQUIRED_CONFIG_KEYS:
        if key not in config:
            errors.append(f"Missing required key: '{key}'")

    # Validate samples
    if "samples" in config:
        samples = config["samples"]
        if not isinstance(samples, (list, dict)):
            errors.append("'samples' must be a list or mapping")
        elif isinstance(samples, list):
            for i, s in enumerate(samples):
                if isinstance(s, str) and not Path(s).exists():
                    warnings.append(f"Sample file not found: {s}")
                elif isinstance(s, dict):
                    if "path" in s and not Path(s["path"]).exists():
                        warnings.append(f"Sample file not found: {s['path']}")

    # Validate platform
    if "platform" in config:
        if config["platform"] not in ("hifi", "nanopore"):
            errors.append(f"Invalid platform: '{config['platform']}' (must be 'hifi' or 'nanopore')")

    # Validate normalization
    if "normalize" in config:
        if config["normalize"] not in ("clr", "relative", "tss"):
            errors.append(f"Invalid normalize method: '{config['normalize']}'")

    # Validate database paths
    if "databases" in config and isinstance(config["databases"], dict):
        for kingdom, db_path in config["databases"].items():
            if db_path and not Path(db_path).exists():
                warnings.append(f"Database path not found for {kingdom}: {db_path}")

    return errors, warnings
