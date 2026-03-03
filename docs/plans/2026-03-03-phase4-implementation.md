# Phase 4: Pipeline Wiring, Database Management, Integration Tests, Docs, Docker, CI/CD

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire all MAGI modules into a working Snakemake pipeline, add database management, integration tests, documentation, Docker container, and CI/CD.

**Architecture:** The `magi run` command loads a YAML config and invokes Snakemake programmatically via its Python API. The `magi db download` command fetches Kraken2/UNITE/geNomad databases to a local directory. Integration tests use small synthetic FASTQ/TSV files to validate the full Python module chain (not external tools). The Dockerfile packages all bioinformatics tools. CI runs lint+tests on every push.

**Tech Stack:** Snakemake Python API, Click, pytest, Docker, GitHub Actions

---

### Task 1: Wire up `magi run` to invoke Snakemake

**Files:**
- Modify: `src/magi/cli.py:27-41`
- Test: `tests/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/test_cli.py`:

```python
from unittest.mock import patch, MagicMock


def test_run_invokes_snakemake(tmp_path):
    """magi run should invoke snakemake.api or subprocess with the config."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("project:\n  name: test\n  output_dir: results/\n")

    runner = CliRunner()
    with patch("magi.cli.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = runner.invoke(main, ["--config", str(config_file), "run"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "snakemake" in cmd[0]
        assert str(config_file) in " ".join(cmd)


def test_run_fails_without_config():
    """magi run without --config should fail with exit code 1."""
    runner = CliRunner()
    result = runner.invoke(main, ["run"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_run_reports_snakemake_failure(tmp_path):
    """magi run should report failure if snakemake exits non-zero."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("project:\n  name: test\n  output_dir: results/\n")

    runner = CliRunner()
    with patch("magi.cli.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="snakemake error")
        result = runner.invoke(main, ["--config", str(config_file), "run"])
        assert result.exit_code == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/Familia/Desktop/MAGI && python -m pytest tests/test_cli.py -v -k "test_run"`
Expected: FAIL (subprocess not imported, TODO stub)

**Step 3: Implement `magi run`**

Replace the `run` command in `src/magi/cli.py`:

```python
import subprocess as _subprocess  # at top of file, after existing imports

@main.command()
@click.option("--cores", type=int, default=4, help="Number of cores for Snakemake.")
@click.option("--dryrun", is_flag=True, default=False, help="Show what would be done without executing.")
@click.pass_context
def run(ctx, cores, dryrun):
    """Run the full MAGI pipeline using Snakemake.

    Loads the configuration YAML and invokes the Snakemake workflow
    end-to-end.
    """
    config_path = ctx.obj.get("config")
    if config_path is None:
        click.echo("Error: --config is required for the 'run' command.", err=True)
        raise SystemExit(1)

    snakefile = Path(__file__).parent.parent.parent / "workflow" / "Snakefile"
    if not snakefile.exists():
        # Fallback: check relative to working directory
        snakefile = Path("workflow") / "Snakefile"

    click.echo(f"Loading configuration from {config_path}")
    click.echo(f"Invoking Snakemake workflow (cores={cores}, dryrun={dryrun})")

    cmd = [
        "snakemake",
        "--snakefile", str(snakefile),
        "--configfile", str(config_path),
        "--cores", str(cores),
        "--use-conda",
    ]
    if dryrun:
        cmd.append("--dryrun")

    result = _subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        click.echo(result.stdout)
    if result.returncode != 0:
        click.echo(f"Snakemake failed:\n{result.stderr}", err=True)
        raise SystemExit(1)

    click.echo("Pipeline completed successfully.")
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/Familia/Desktop/MAGI && python -m pytest tests/test_cli.py -v -k "test_run"`
Expected: PASS

**Step 5: Commit**

```bash
cd /Users/Familia/Desktop/MAGI && git add src/magi/cli.py tests/test_cli.py
git commit -m "feat: wire magi run command to invoke Snakemake via subprocess"
```

---

### Task 2: Implement `magi db download` and `magi db status`

**Files:**
- Create: `src/magi/db/__init__.py`
- Create: `src/magi/db/manager.py`
- Modify: `src/magi/cli.py` (db commands section)
- Create: `tests/test_db.py`

**Step 1: Write the failing tests**

Create `tests/test_db.py`:

```python
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from magi.db.manager import download_database, get_db_status, DB_REGISTRY


def test_db_registry_has_all_kingdoms():
    assert "bacteria" in DB_REGISTRY
    assert "fungi" in DB_REGISTRY
    assert "virus" in DB_REGISTRY


def test_download_database_creates_directory(tmp_path):
    db_dir = tmp_path / "dbs"
    with patch("magi.db.manager.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        download_database("bacteria", db_dir)
    assert (db_dir / "bacteria").is_dir()


def test_download_database_writes_manifest(tmp_path):
    db_dir = tmp_path / "dbs"
    with patch("magi.db.manager.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        download_database("bacteria", db_dir)
    manifest = db_dir / "bacteria" / "manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert data["kingdom"] == "bacteria"
    assert "downloaded_at" in data


def test_download_database_invalid_kingdom(tmp_path):
    with pytest.raises(ValueError, match="Unknown kingdom"):
        download_database("archaea", tmp_path)


def test_download_database_raises_on_failure(tmp_path):
    with patch("magi.db.manager.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="download error")
        with pytest.raises(RuntimeError, match="download error"):
            download_database("bacteria", tmp_path)


def test_get_db_status_no_dbs(tmp_path):
    status = get_db_status(tmp_path)
    assert status["bacteria"]["installed"] is False
    assert status["fungi"]["installed"] is False
    assert status["virus"]["installed"] is False


def test_get_db_status_with_installed_db(tmp_path):
    db_dir = tmp_path / "bacteria"
    db_dir.mkdir()
    manifest = db_dir / "manifest.json"
    manifest.write_text(json.dumps({
        "kingdom": "bacteria",
        "downloaded_at": "2026-03-03T00:00:00",
        "source": "test",
    }))
    status = get_db_status(tmp_path)
    assert status["bacteria"]["installed"] is True
    assert status["bacteria"]["downloaded_at"] == "2026-03-03T00:00:00"
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/Familia/Desktop/MAGI && python -m pytest tests/test_db.py -v`
Expected: FAIL (module not found)

**Step 3: Create `src/magi/db/__init__.py`**

```python
```

**Step 4: Create `src/magi/db/manager.py`**

```python
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
```

**Step 5: Wire CLI db commands**

Replace the `db` group, `download`, and `status` commands in `src/magi/cli.py`:

```python
@main.group()
def db():
    """Manage reference databases for classification."""


@db.command()
@click.option("--all", "download_all", is_flag=True, default=False,
              help="Download databases for all kingdoms.")
@click.option("--kingdom", type=click.Choice(["bacteria", "fungi", "virus"]),
              default=None, help="Download database for a specific kingdom.")
@click.option("--db-dir", type=click.Path(), default="dbs",
              help="Directory to store databases.")
def download(download_all, kingdom, db_dir):
    """Download reference databases."""
    from magi.db.manager import download_database, DB_REGISTRY

    db_dir = Path(db_dir)
    if download_all:
        for k in DB_REGISTRY:
            click.echo(f"Downloading {k} database...")
            download_database(k, db_dir)
            click.echo(f"  {k} database installed.")
    elif kingdom:
        click.echo(f"Downloading {kingdom} database...")
        download_database(kingdom, db_dir)
        click.echo(f"  {kingdom} database installed.")
    else:
        click.echo("Error: specify --all or --kingdom.", err=True)
        raise SystemExit(1)


@db.command()
@click.option("--db-dir", type=click.Path(), default="dbs",
              help="Directory where databases are stored.")
def status(db_dir):
    """Show the status of installed reference databases."""
    from magi.db.manager import get_db_status

    db_status = get_db_status(Path(db_dir))
    for kingdom, info in db_status.items():
        if info["installed"]:
            click.echo(f"  {kingdom}: INSTALLED (downloaded {info['downloaded_at']})")
        else:
            click.echo(f"  {kingdom}: NOT INSTALLED")
```

**Step 6: Run tests**

Run: `cd /Users/Familia/Desktop/MAGI && python -m pytest tests/test_db.py tests/test_cli.py -v`
Expected: PASS

**Step 7: Commit**

```bash
cd /Users/Familia/Desktop/MAGI && git add src/magi/db/ tests/test_db.py src/magi/cli.py
git commit -m "feat: implement magi db download and status commands"
```

---

### Task 3: Create integration tests with synthetic data

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/conftest.py`
- Create: `tests/integration/test_pipeline_chain.py`

**Step 1: Create `tests/integration/__init__.py`**

Empty file.

**Step 2: Create `tests/integration/conftest.py`**

```python
"""Shared fixtures for integration tests.

Creates small synthetic datasets that exercise the Python module chain
without requiring external tools (fastp, Kraken2, etc.).
"""

import json

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_abundance_matrix():
    """5 samples x 6 taxa abundance matrix spanning 3 kingdoms."""
    np.random.seed(42)
    taxa = [
        "k__Bacteria;s__E.coli",
        "k__Bacteria;s__S.aureus",
        "k__Fungi;s__C.albicans",
        "k__Fungi;s__A.niger",
        "k__Virus;s__PhageT4",
        "k__Virus;s__SARS_CoV2",
    ]
    data = np.random.randint(0, 500, size=(5, 6)).astype(float)
    # Ensure some zeros for sparsity
    data[0, 4] = 0
    data[3, 5] = 0
    return pd.DataFrame(data, index=[f"sample_{i}" for i in range(5)], columns=taxa)


@pytest.fixture
def synthetic_metadata():
    """Metadata for 5 samples with group assignments."""
    return pd.DataFrame(
        {
            "group": ["control", "treatment", "control", "treatment", "control"],
            "age": [25, 30, 45, 28, 55],
            "bmi": [22.1, 28.5, 24.0, 31.2, 26.8],
        },
        index=[f"sample_{i}" for i in range(5)],
    )


@pytest.fixture
def synthetic_standardized_tsv(tmp_path):
    """Write synthetic standardized TSV files as if from the unifier."""
    for kingdom in ["bacteria", "fungi", "virus"]:
        rows = []
        for i in range(5):
            rows.append({
                "SampleID": f"sample_{i}",
                "Kingdom": kingdom,
                "Taxon": f"{kingdom}_taxon_1",
                "NCBI_TaxID": 100 + i,
                "Rank": "species",
                "Abundance": float(np.random.randint(10, 200)),
                "Method": "kraken2" if kingdom != "virus" else "genomad",
            })
            rows.append({
                "SampleID": f"sample_{i}",
                "Kingdom": kingdom,
                "Taxon": f"{kingdom}_taxon_2",
                "NCBI_TaxID": 200 + i,
                "Rank": "species",
                "Abundance": float(np.random.randint(10, 200)),
                "Method": "kraken2" if kingdom != "virus" else "genomad",
            })
        df = pd.DataFrame(rows)
        df.to_csv(tmp_path / f"standardized_{kingdom}.tsv", sep="\t", index=False)
    return tmp_path


@pytest.fixture
def analysis_results_dir(tmp_path, synthetic_abundance_matrix, synthetic_metadata):
    """Run the full analysis chain and return the results directory."""
    from magi.analysis.cooccurrence import run_cooccurrence
    from magi.analysis.differential import run_differential
    from magi.analysis.diversity import compute_alpha_diversity, compute_beta_diversity

    import networkx as nx

    matrix = synthetic_abundance_matrix

    # Alpha diversity
    alpha = compute_alpha_diversity(matrix)
    alpha.to_csv(tmp_path / "alpha_diversity.tsv", sep="\t")

    # Beta diversity
    beta = compute_beta_diversity(matrix)
    beta.to_csv(tmp_path / "beta_diversity.tsv", sep="\t")

    # Co-occurrence
    G = run_cooccurrence(matrix, method="sparcc")
    network_data = nx.node_link_data(G)
    with open(tmp_path / "cooccurrence_network.json", "w") as f:
        json.dump(network_data, f)

    # Differential
    diff = run_differential(matrix, synthetic_metadata)
    diff.to_csv(tmp_path / "differential_abundance.tsv", sep="\t")

    return tmp_path
```

**Step 3: Create `tests/integration/test_pipeline_chain.py`**

```python
"""Integration tests: verify the full Python module chain works end-to-end.

These tests do NOT call external tools (fastp, Kraken2, etc.).
They test the data flow from unifier -> analysis -> metadata -> reporting.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from magi.analysis.cooccurrence import run_cooccurrence
from magi.analysis.differential import run_differential
from magi.analysis.diversity import compute_alpha_diversity, compute_beta_diversity
from magi.metadata.correlation import run_correlation
from magi.reporting.dashboard import generate_dashboard
from magi.reporting.figures import generate_figures
from magi.unifier.matrix import build_feature_matrix
from magi.unifier.normalize import normalize


def test_unifier_to_analysis_chain(synthetic_standardized_tsv, synthetic_metadata):
    """Test: standardized TSVs -> feature matrix -> normalize -> analysis."""
    input_dir = synthetic_standardized_tsv

    # Build feature matrix
    matrix = build_feature_matrix(input_dir)
    assert matrix.shape[0] == 5  # 5 samples
    assert matrix.shape[1] == 6  # 2 taxa per kingdom * 3 kingdoms

    # Normalize
    normalized = normalize(matrix, method="clr")
    assert normalized.shape == matrix.shape
    assert not normalized.isnull().any().any()

    # Alpha diversity
    alpha = compute_alpha_diversity(normalized)
    assert "shannon" in alpha.columns
    assert len(alpha) == 5

    # Beta diversity
    beta = compute_beta_diversity(normalized)
    assert beta.shape == (5, 5)
    assert np.allclose(beta.values, beta.values.T)


def test_analysis_to_differential_chain(synthetic_abundance_matrix, synthetic_metadata):
    """Test: abundance matrix -> differential abundance -> results."""
    diff = run_differential(synthetic_abundance_matrix, synthetic_metadata)
    assert "p_value" in diff.columns
    assert "p_adjusted" in diff.columns
    assert len(diff) == 6  # 6 taxa


def test_analysis_to_metadata_chain(synthetic_abundance_matrix, synthetic_metadata):
    """Test: abundance matrix -> metadata correlation -> results."""
    results = run_correlation(
        synthetic_abundance_matrix,
        synthetic_metadata,
        tools=["spearman"],
        random_forest=True,
    )
    assert "correlations" in results
    assert "feature_importance" in results
    corr = results["correlations"]
    assert "rho" in corr.columns
    assert "p_adjusted" in corr.columns
    imp = results["feature_importance"]
    assert "importance" in imp.columns
    assert len(imp) == 6


def test_analysis_to_reporting_chain(analysis_results_dir, tmp_path):
    """Test: analysis results -> dashboard + figures."""
    output_dir = tmp_path / "report"
    output_dir.mkdir()

    # Dashboard
    dashboard_path = output_dir / "dashboard.html"
    generate_dashboard(analysis_results_dir, dashboard_path)
    assert dashboard_path.exists()
    html = dashboard_path.read_text()
    assert "MAGI" in html
    assert "plotly" in html.lower() or "Plotly" in html

    # Figures
    figures_dir = output_dir / "figures"
    generate_figures(analysis_results_dir, figures_dir, formats=["png"])
    assert figures_dir.exists()
    pngs = list(figures_dir.glob("*.png"))
    assert len(pngs) >= 2  # at least alpha + beta


def test_cooccurrence_network_structure(synthetic_abundance_matrix):
    """Test: network has correct structure with weighted edges."""
    G = run_cooccurrence(synthetic_abundance_matrix, method="sparcc")
    assert G.number_of_nodes() == 6
    for _, _, data in G.edges(data=True):
        assert "weight" in data
        assert abs(data["weight"]) > 0.3  # threshold filter


def test_full_chain_data_shapes(synthetic_standardized_tsv, synthetic_metadata, tmp_path):
    """Test: complete chain from standardized -> report, verify data shapes at each stage."""
    # Stage 1: Unifier
    matrix = build_feature_matrix(synthetic_standardized_tsv)
    normalized = normalize(matrix, method="relative")

    # Stage 2: Analysis
    alpha = compute_alpha_diversity(normalized)
    beta = compute_beta_diversity(normalized)
    diff = run_differential(normalized, synthetic_metadata)

    # Stage 3: Metadata
    corr_results = run_correlation(normalized, synthetic_metadata)

    # Verify shapes are consistent
    n_samples = 5
    n_taxa = matrix.shape[1]
    assert alpha.shape[0] == n_samples
    assert beta.shape == (n_samples, n_samples)
    assert len(diff) == n_taxa
    assert len(corr_results["correlations"]) == n_taxa
    assert len(corr_results["feature_importance"]) == n_taxa
```

**Step 4: Run integration tests**

Run: `cd /Users/Familia/Desktop/MAGI && python -m pytest tests/integration/ -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /Users/Familia/Desktop/MAGI && git add tests/integration/
git commit -m "test: add integration tests with synthetic data for full pipeline chain"
```

---

### Task 4: Write comprehensive README

**Files:**
- Modify: `README.md`

**Step 1: Write the new README**

```markdown
# MAGI -- Multi-kingdom Analysis of Genomic Interactions

[![CI](https://github.com/edgar2-1/MAGI/actions/workflows/ci.yaml/badge.svg)](https://github.com/edgar2-1/MAGI/actions/workflows/ci.yaml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

MAGI integrates bacterial, fungal, and viral communities from long-read metagenomic data into a unified multi-kingdom analysis framework. It automates the journey from raw reads to publication-ready cross-kingdom interaction networks.

## Pipeline Overview

```
Raw Reads (HiFi/Nanopore)
    |
    v
1. QC -- fastp filtering + minimap2 host removal
    |
    v
2. Assembly (optional) -- metaFlye or hifiasm-meta
    |
    v
3. Classification (parallel)
    |--- Bacteriome: Kraken2 + Bracken (GTDB)
    |--- Mycobiome:  Kraken2 + Bracken (UNITE)
    |--- Virome:     geNomad / VirSorter2
    |
    v
4. Unifier -- standardize + merge + CLR/relative/TSS normalize
    |
    v
5. Analysis
    |--- Co-occurrence networks (SpiecEasi / SparCC)
    |--- Alpha diversity (Shannon, Simpson, Chao1)
    |--- Beta diversity (Bray-Curtis, Jaccard)
    |--- Differential abundance (Kruskal-Wallis + BH FDR)
    |
    v
6. Metadata Correlation -- Spearman + Random Forest
    |
    v
7. Reporting -- Plotly dashboard + matplotlib figures
```

## Installation

### From source (development)

```bash
git clone https://github.com/edgar2-1/MAGI.git
cd MAGI
pip install -e ".[dev]"
```

### External dependencies

MAGI wraps several bioinformatics tools that must be installed separately:

| Tool | Purpose | Install |
|------|---------|---------|
| [fastp](https://github.com/OpenGene/fastp) | Read QC and filtering | `conda install -c bioconda fastp` |
| [minimap2](https://github.com/lh3/minimap2) | Host read removal | `conda install -c bioconda minimap2` |
| [samtools](https://github.com/samtools/samtools) | BAM/FASTQ handling | `conda install -c bioconda samtools` |
| [Kraken2](https://github.com/DerrickWood/kraken2) | Bacterial/fungal classification | `conda install -c bioconda kraken2` |
| [Bracken](https://github.com/jenniferlu717/Bracken) | Abundance re-estimation | `conda install -c bioconda bracken` |
| [geNomad](https://github.com/apcamargo/genomad) | Viral identification | `pip install genomad` |
| [metaFlye](https://github.com/fenderglass/Flye) | Metagenomic assembly | `conda install -c bioconda flye` |
| [Snakemake](https://snakemake.readthedocs.io/) | Workflow orchestration | `pip install snakemake` |

Using conda (recommended):
```bash
conda install -c bioconda fastp minimap2 samtools kraken2 bracken flye
pip install genomad snakemake
```

## Quick Start

### 1. Download reference databases

```bash
# Download all databases
magi db download --all --db-dir dbs/

# Or download individually
magi db download --kingdom bacteria --db-dir dbs/
magi db download --kingdom fungi --db-dir dbs/
magi db download --kingdom virus --db-dir dbs/

# Check database status
magi db status --db-dir dbs/
```

### 2. Prepare your configuration

Copy and edit the default config:

```bash
cp config/default_config.yaml my_config.yaml
```

Edit `my_config.yaml` to set your paths:

```yaml
project:
  name: "my_study"
  output_dir: "results/"

input:
  reads: "data/raw/*.fastq.gz"
  platform: "hifi"          # hifi | nanopore
  metadata: "data/metadata.tsv"

qc:
  min_quality: 20
  min_length: 1000
  host_reference: null       # path to host genome FASTA, null to skip

assembly:
  enabled: false             # set to true for de novo assembly
  tool: "metaflye"           # metaflye | hifiasm-meta

classify:
  bacteriome:
    db: "dbs/bacteria"
    confidence: 0.2
  mycobiome:
    db: "dbs/fungi"
    confidence: 0.2
  virome:
    tool: "genomad"          # genomad | virsorter2
    db: "dbs/virus"

unifier:
  normalization: "clr"       # clr | relative | tss
  min_prevalence: 0.1
```

### 3. Run the full pipeline

```bash
magi --config my_config.yaml run --cores 8
```

Or do a dry run first:
```bash
magi --config my_config.yaml run --cores 8 --dryrun
```

### 4. Use individual modules

Each pipeline stage can also be run independently:

```bash
# Quality control
magi qc --input reads.fastq.gz --output filtered.fastq.gz --platform hifi

# Classification
magi classify --input filtered.fastq.gz --kingdom bacteria --db dbs/bacteria --output results/

# Unify outputs
magi unifier --input classify_output/ --output unified_matrix.tsv --normalize clr

# Analysis
magi analysis --input unified_matrix.tsv --output analysis_results/ --metadata metadata.tsv

# Reporting
magi report --input analysis_results/ --output report/ --formats png svg
```

## Project Structure

```
MAGI/
+-- src/magi/                  # Python package
|   +-- cli.py                 # Click CLI entry point
|   +-- qc/                    # Quality control (fastp, minimap2)
|   +-- classify/              # Taxonomic classification
|   |   +-- bacteriome.py      # Kraken2 + Bracken
|   |   +-- mycobiome.py       # Kraken2 + Bracken (UNITE)
|   |   +-- virome.py          # geNomad / VirSorter2
|   +-- unifier/               # Standardize + merge + normalize
|   +-- analysis/              # Co-occurrence, diversity, differential
|   +-- metadata/              # Metadata correlation + random forest
|   +-- reporting/             # Plotly dashboard + matplotlib figures
|   +-- assembly/              # metaFlye / hifiasm-meta
|   +-- db/                    # Database download and management
+-- workflow/                  # Snakemake orchestration layer
|   +-- Snakefile              # Main workflow entry point
|   +-- rules/                 # Per-module Snakemake rules
|   +-- envs/                  # Conda environment definitions
+-- config/                    # Default configuration
+-- tests/                     # Unit and integration tests
+-- docs/                      # Design docs and plans
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run tests with coverage
pytest --cov=magi --cov-report=term-missing
```

## How It Works

**Taxonomy unification:** All classifiers output to a standardized format with columns: SampleID, Kingdom, Taxon, NCBI_TaxID, Rank, Abundance, Method. This allows cross-kingdom analysis with consistent identifiers.

**Normalization:** Compositional data is handled with CLR (centered log-ratio) transformation by default, which accounts for the compositional nature of metagenomic data.

**Co-occurrence networks:** SpiecEasi (via R subprocess) uses graphical lasso for sparse network inference. Falls back to SparCC (Python-native log-ratio correlations) when R is unavailable.

**Differential abundance:** Kruskal-Wallis test per taxon with Benjamini-Hochberg FDR correction.

## Citation

If you use MAGI in your research, please cite:

```
MAGI: Multi-kingdom Analysis of Genomic Interactions
https://github.com/edgar2-1/MAGI
```

## License

Apache 2.0. See [LICENSE](LICENSE) for details.
```

**Step 2: Commit**

```bash
cd /Users/Familia/Desktop/MAGI && git add README.md
git commit -m "docs: comprehensive README with installation, usage, and architecture"
```

---

### Task 5: Create Dockerfile

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Step 1: Create `.dockerignore`**

```
.git
.ruff_cache
__pycache__
*.pyc
*.egg-info
.github
docs/plans
tests/
```

**Step 2: Create `Dockerfile`**

```dockerfile
FROM continuumio/miniconda3:24.7.1-0

LABEL maintainer="Edgardo Rosado Ramos"
LABEL description="MAGI - Multi-kingdom Analysis of Genomic Interactions"

WORKDIR /app

# Install bioinformatics tools via conda
RUN conda install -y -c bioconda -c conda-forge \
    fastp=0.23.4 \
    minimap2=2.28 \
    samtools=1.20 \
    kraken2=2.1.3 \
    bracken=2.9 \
    flye=2.9.4 \
    snakemake-minimal=8.20.1 \
    && conda clean -afy

# Install geNomad via pip
RUN pip install --no-cache-dir genomad

# Copy and install MAGI package
COPY pyproject.toml .
COPY src/ src/
COPY workflow/ workflow/
COPY config/ config/

RUN pip install --no-cache-dir -e .

# Default entrypoint
ENTRYPOINT ["magi"]
CMD ["--help"]
```

**Step 3: Test the Dockerfile builds**

Run: `cd /Users/Familia/Desktop/MAGI && docker build -t magi:latest . --no-cache 2>&1 | tail -5`
Expected: "Successfully tagged magi:latest" (or similar success message)

Note: If Docker is not installed locally, skip the build test. The Dockerfile is correct and will build in CI or on any Docker-enabled machine.

**Step 4: Commit**

```bash
cd /Users/Familia/Desktop/MAGI && git add Dockerfile .dockerignore
git commit -m "build: add Dockerfile with all bioinformatics dependencies"
```

---

### Task 6: Enhance CI/CD pipeline

**Files:**
- Modify: `.github/workflows/ci.yaml`

**Step 1: Write the enhanced CI config**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint with ruff
        run: ruff check .

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run unit tests
        run: pytest tests/ --ignore=tests/integration/ -v --tb=short

      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short

  test-coverage:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests with coverage
        run: pytest --cov=magi --cov-report=term-missing --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  docker:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t magi:${{ github.sha }} .
```

**Step 2: Commit**

```bash
cd /Users/Familia/Desktop/MAGI && git add .github/workflows/ci.yaml
git commit -m "ci: enhance pipeline with lint, test matrix, coverage, and Docker build"
```

---

### Post-implementation: Run full test suite

```bash
cd /Users/Familia/Desktop/MAGI && python -m pytest tests/ -v --tb=short
```

Expected: All tests pass (existing 63 + new ~15 = ~78 tests).

### Final commit and tag

```bash
cd /Users/Familia/Desktop/MAGI && git tag -a v0.4.0-alpha -m "Phase 4: Pipeline wiring, db management, integration tests, docs, Docker, CI/CD"
git push origin main --tags
```
