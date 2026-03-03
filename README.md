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
conda install -c bioconda -c conda-forge fastp minimap2 samtools kraken2 bracken flye
pip install genomad snakemake
```

## Quick Start

### 1. Download reference databases

```bash
magi db download --all --db-dir dbs/
magi db status --db-dir dbs/
```

### 2. Prepare your configuration

```bash
cp config/default_config.yaml my_config.yaml
```

Edit `my_config.yaml` to set your input paths and parameters.

### 3. Run the full pipeline

```bash
magi --config my_config.yaml run --cores 8
```

Or do a dry run first:
```bash
magi --config my_config.yaml run --cores 8 --dryrun
```

### 4. Use individual modules

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
|   +-- unifier/               # Standardize + merge + normalize
|   +-- analysis/              # Co-occurrence, diversity, differential
|   +-- metadata/              # Metadata correlation + random forest
|   +-- reporting/             # Plotly dashboard + matplotlib figures
|   +-- assembly/              # metaFlye / hifiasm-meta
|   +-- db/                    # Database download and management
+-- workflow/                  # Snakemake orchestration layer
+-- config/                    # Default configuration
+-- tests/                     # Unit and integration tests
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
pytest --cov=magi --cov-report=term-missing
```

## License

Apache 2.0. See [LICENSE](LICENSE) for details.
