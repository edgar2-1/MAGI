"""Configuration and dependency validation for the MAGI pipeline."""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml
from pydantic import BaseModel, field_validator

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


class SampleEntry(BaseModel):
    """A sample entry that can be a path string or a dict with a path key."""
    path: str


class DatabaseConfig(BaseModel):
    """Database paths per kingdom."""
    bacteria: Optional[str] = None
    fungi: Optional[str] = None
    virus: Optional[str] = None


class MAGIConfig(BaseModel):
    """MAGI pipeline configuration schema."""
    samples: Union[List[str], List[dict], dict]
    output_dir: str
    platform: Optional[str] = None
    normalize: Optional[str] = None
    databases: Optional[Dict[str, Optional[str]]] = None
    min_quality: Optional[int] = None
    min_length: Optional[int] = None
    confidence: Optional[float] = None
    host_reference: Optional[str] = None
    cooccurrence_method: Optional[str] = None
    metadata: Optional[str] = None

    model_config = {"extra": "allow"}

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v is not None and v not in ("hifi", "nanopore"):
            raise ValueError(f"Invalid platform: '{v}' (must be 'hifi' or 'nanopore')")
        return v

    @field_validator("normalize")
    @classmethod
    def validate_normalize(cls, v):
        if v is not None and v not in ("clr", "relative", "tss"):
            raise ValueError(f"Invalid normalize method: '{v}'")
        return v

    @field_validator("cooccurrence_method")
    @classmethod
    def validate_cooccurrence_method(cls, v):
        if v is not None and v not in ("spieceasi", "sparcc"):
            raise ValueError(f"Invalid cooccurrence method: '{v}'")
        return v


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
    """Validate a MAGI configuration file using pydantic schema.

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

    # Validate with pydantic schema
    try:
        parsed = MAGIConfig(**config)
    except Exception as e:
        # Extract individual validation errors
        for err_line in str(e).split("\n"):
            err_line = err_line.strip()
            if err_line and not err_line.startswith("For further"):
                errors.append(err_line)
        # Check for missing required keys specifically
        for key in REQUIRED_CONFIG_KEYS:
            if key not in config:
                if not any(key in e for e in errors):
                    errors.append(f"Missing required key: '{key}'")
        return errors, warnings

    # Warnings for file existence (not errors since files may not exist yet)
    if isinstance(parsed.samples, list):
        for s in parsed.samples:
            if isinstance(s, str) and s and not Path(s).exists():
                warnings.append(f"Sample file not found: {s}")
            elif isinstance(s, dict) and "path" in s and not Path(s["path"]).exists():
                warnings.append(f"Sample file not found: {s['path']}")

    if parsed.databases:
        for kingdom, db_path in parsed.databases.items():
            if db_path and not Path(db_path).exists():
                warnings.append(f"Database path not found for {kingdom}: {db_path}")

    return errors, warnings
