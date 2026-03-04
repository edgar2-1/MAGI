"""Configuration and dependency validation for the MAGI pipeline."""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, ValidationError, field_validator

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

REQUIRED_CONFIG_KEYS = ["project", "input"]


class ProjectConfig(BaseModel):
    """Project-level configuration."""
    name: str = "my_study"
    output_dir: str = "results/"


class InputConfig(BaseModel):
    """Input data configuration."""
    reads: str = "data/raw/*.fastq.gz"
    platform: str = "hifi"
    metadata: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in ("hifi", "nanopore"):
            raise ValueError(f"Invalid platform: '{v}' (must be 'hifi' or 'nanopore')")
        return v


class QCConfig(BaseModel):
    """QC configuration."""
    min_quality: int = 20
    min_length: int = 1000
    max_length: Optional[int] = None
    host_reference: Optional[str] = None


class AssemblyConfig(BaseModel):
    """Assembly configuration."""
    enabled: bool = False
    tool: str = "metaflye"


class KingdomClassifyConfig(BaseModel):
    """Per-kingdom classification config."""
    db: str
    confidence: float = 0.2
    read_length: int = 150


class ViromeClassifyConfig(BaseModel):
    """Virome-specific classification config."""
    tool: str = "genomad"
    db: str


class ClassifyConfig(BaseModel):
    """Classification configuration."""
    bacteriome: Optional[KingdomClassifyConfig] = None
    mycobiome: Optional[KingdomClassifyConfig] = None
    virome: Optional[ViromeClassifyConfig] = None


class UnifierConfig(BaseModel):
    """Unifier configuration."""
    normalization: str = "clr"
    min_prevalence: float = 0.1
    taxonomy_backend: str = "ncbi"

    @field_validator("normalization")
    @classmethod
    def validate_normalization(cls, v):
        if v not in ("clr", "relative", "tss"):
            raise ValueError(f"Invalid normalize method: '{v}'")
        return v


class CooccurrenceConfig(BaseModel):
    """Co-occurrence analysis configuration."""
    method: str = "spieceasi"
    min_abundance: float = 0.01

    @field_validator("method")
    @classmethod
    def validate_method(cls, v):
        if v not in ("spieceasi", "sparcc"):
            raise ValueError(f"Invalid cooccurrence method: '{v}'")
        return v


class AnalysisConfig(BaseModel):
    """Analysis configuration."""
    cooccurrence: Optional[CooccurrenceConfig] = None
    model_config = {"extra": "allow"}


class MetadataCorrelationConfig(BaseModel):
    """Metadata correlation configuration."""
    tools: list = ["spearman"]
    random_forest: bool = True


class MAGIConfig(BaseModel):
    """MAGI pipeline configuration schema (matches nested YAML)."""
    project: ProjectConfig = ProjectConfig()
    input: InputConfig = InputConfig()
    qc: Optional[QCConfig] = None
    assembly: Optional[AssemblyConfig] = None
    classify: Optional[ClassifyConfig] = None
    unifier: Optional[UnifierConfig] = None
    analysis: Optional[AnalysisConfig] = None
    metadata_correlation: Optional[MetadataCorrelationConfig] = None

    model_config = {"extra": "allow"}


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

    # Check for required top-level keys
    for key in REQUIRED_CONFIG_KEYS:
        if key not in config:
            errors.append(f"Missing required key: '{key}'")
    if errors:
        return errors, warnings

    # Validate with pydantic schema
    try:
        MAGIConfig(**config)
    except ValidationError as e:
        for err_line in str(e).split("\n"):
            err_line = err_line.strip()
            if err_line and not err_line.startswith("For further"):
                errors.append(err_line)
        return errors, warnings

    # Warnings for missing database files
    if isinstance(config.get("classify"), dict):
        for kingdom in ("bacteriome", "mycobiome", "virome"):
            kingdom_cfg = config["classify"].get(kingdom, {})
            if isinstance(kingdom_cfg, dict):
                db_path = kingdom_cfg.get("db")
                if db_path and not Path(db_path).exists():
                    warnings.append(f"Database path not found for {kingdom}: {db_path}")

    return errors, warnings
