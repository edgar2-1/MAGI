# MAGI Design Document

**MAGI — Multi-kingdom Analysis of Genomic Interactions**
**Author:** Edgardo
**Version:** 0.1
**Date:** 2026-03-03

## Vision

Integrate bacterial (16S), fungal (ITS), and viral communities from long-read
metagenomic data into a single analysis framework, enabling discovery of
cross-kingdom interaction patterns invisible to single-kingdom tools.

## Key Decisions

| Decision              | Choice                                      |
|-----------------------|---------------------------------------------|
| Orchestrator          | Snakemake                                   |
| Architecture          | Python package + Snakemake orchestration     |
| Primary platform      | PacBio HiFi (Nanopore compatible)           |
| Taxonomy standard     | NCBI taxids                                 |
| Co-occurrence default | SpiecEasi (SparCC available)                |
| Visualization         | Plotly interactive + matplotlib/seaborn static |
| License               | Apache 2.0                                  |

## Architecture

Two-layer design:

**Layer 1 — Python Package (`src/magi/`):**
Each module is an independently importable and CLI-callable subpackage.
Researchers can use individual modules without running the full pipeline.

**Layer 2 — Snakemake Workflow (`workflow/`):**
Orchestrates the Python modules as pipeline steps. Handles parallelism,
file dependency resolution, and conda environment management.

## Pipeline Modules

### Module 1 — QC & Preprocessing
Raw HiFi/Nanopore reads -> quality filtering (fastp), adapter trimming,
host read removal (minimap2 + samtools). Configurable host reference,
quality thresholds, read length bounds.

### Module 2 — Assembly (Optional)
metaFlye or hifiasm-meta. Disabled by default. Users opt in via config.

### Module 3 — Kingdom-Specific Classification (Parallel)
- 3A Bacteriome: Kraken2 + Bracken against GTDB
- 3B Mycobiome: Kraken2 against UNITE, or ITSx
- 3C Virome: geNomad + Kraken2 against viral RefSeq

### Module 4 — Unifier (Core Innovation)
Standardizes all classification outputs into:
`[SampleID, Kingdom, Taxon, NCBI_TaxID, Rank, Abundance, Method]`

Builds unified Sample x Feature matrix. Handles normalization (CLR,
relative, TSS) and compositionality-aware zero handling. Maps all
taxonomy to NCBI taxids for cross-database interoperability.

### Module 5 — Cross-Kingdom Analysis
- Co-occurrence networks: SpiecEasi (default) or SparCC
- Alpha/beta diversity per kingdom and merged
- Differential abundance: ANCOM-BC or ALDEx2

### Module 6 — Metadata Correlation Engine
MaAsLin2, LEfSe, random forests. Tests whether multi-kingdom biomarker
panels outperform single-kingdom.

### Module 7 — Reporting
- Interactive HTML dashboards (Plotly + Jinja2)
- Static publication-ready figures (matplotlib + seaborn)
- Network graphs, heatmaps, PCoA plots
- Exportable tables (TSV/CSV)

## Data Flow

```
Raw reads (FASTQ)
    |
    v
Module 1: QC --> filtered_reads.fastq
    |
    +---> Module 2: Assembly (optional) --> contigs.fasta
    |
    v
Module 3: Classification (parallel)
    +-- 3A Bacteriome --> kraken2_bacteria.tsv
    +-- 3B Mycobiome  --> kraken2_fungi.tsv
    +-- 3C Virome     --> genomad_viruses.tsv
    |
    v
Module 4: Unifier --> unified_matrix.tsv
    |
    +---> Module 5: Cross-Kingdom Analysis
    +---> Module 6: Metadata Correlation
    |
    v
Module 7: Reporting --> HTML dashboard + figures + tables
```

## Configuration

Single YAML config file. One command: `magi --config config.yaml`

See `config/default_config.yaml` for the full schema.

## CLI Design

Full pipeline:
```
magi --config config.yaml
magi run --config config.yaml --until classify
```

Individual modules:
```
magi qc --input reads.fastq --output filtered.fastq --platform hifi
magi classify --input filtered.fastq --kingdom bacteria --db dbs/gtdb
magi unifier --input results/classify/ --normalize clr --output matrix.tsv
magi analysis --input matrix.tsv --method spieceasi --output networks/
magi report --input results/ --output report/
```

Database management:
```
magi db download --all
magi db download --kingdom bacteria
magi db status
```

## Dependencies

Python (pip): click, pyyaml, pandas, numpy, scipy, scikit-bio, taxopy,
plotly, matplotlib, seaborn, jinja2, networkx, statsmodels, snakemake

External (conda): fastp, minimap2, samtools, kraken2, bracken, genomad,
virsorter2, itsx, metaflye, hifiasm-meta

R (isolated conda envs): SpiecEasi, ANCOM-BC, ALDEx2, MaAsLin2, LEfSe

## Testing

- Unit tests: core functions per module
- Integration tests: module chains with small synthetic data
- CLI tests: Click test runner
- CI: GitHub Actions (Python 3.10-3.12, pytest, ruff)

## Implementation Phases

- Phase 1: Modules 1, 3, 4 (QC, Classification, Unifier)
- Phase 2: Module 5 (Cross-Kingdom Analysis)
- Phase 3: Modules 2, 6, 7 (Assembly, Metadata, Reporting)
