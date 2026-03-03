# MAGI -- Multi-kingdom Analysis of Genomic Interactions

MAGI integrates bacterial, fungal, and viral communities from long-read metagenomic data into a unified multi-kingdom analysis framework. It automates the journey from raw reads to publication-ready cross-kingdom interaction networks.

## Features

- **Quality control** -- Adapter trimming, host depletion, and read QC for long-read data
- **Taxonomic profiling** -- Multi-kingdom classification across bacteria, fungi, and viruses
- **Assembly** -- Long-read metagenomic assembly with hybrid polishing support
- **Binning** -- Metagenome-assembled genome recovery and quality assessment
- **Functional annotation** -- Gene prediction and pathway annotation across kingdoms
- **Cross-kingdom interaction networks** -- Co-occurrence and correlation-based interaction inference
- **Integrated reporting** -- Interactive HTML reports with multi-kingdom visualizations

## Quick start

```bash
pip install magi-metagenomics
magi --config config.yaml
```

## Requirements

- Python 3.10+
- Snakemake
- conda

## License

Apache 2.0. See [LICENSE](LICENSE) for details.
