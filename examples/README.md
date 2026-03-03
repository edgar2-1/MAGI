# MAGI Example Dataset

This directory contains a small synthetic dataset for testing the MAGI pipeline's
analysis modules (stages 4-7: unification, analysis, metadata correlation, reporting).

## Files

- `config.yaml` -- Example configuration for running the analysis stages
- `data/metadata.tsv` -- Sample metadata (10 samples, 2 groups)
- `data/standardized_bacteria.tsv` -- Simulated bacterial abundance data
- `data/standardized_fungi.tsv` -- Simulated fungal abundance data
- `data/standardized_virus.tsv` -- Simulated viral abundance data

## Quick Start

From the MAGI project root:

```bash
# Run the analysis stages on the example data
cd examples

# 1. Build unified feature matrix
magi unifier --input data/ --output results/unified_matrix.tsv --normalize clr

# 2. Run analysis
magi analysis --input results/unified_matrix.tsv --output results/analysis/ --method sparcc --metadata data/metadata.tsv

# 3. Generate reports
magi report --input results/analysis/ --output results/report/ --formats png svg
```

## What to Expect

- **Unified matrix:** 10 samples x 12 taxa (4 bacteria + 4 fungi + 4 viruses)
- **Co-occurrence network:** Cross-kingdom interaction network
- **Alpha diversity:** Shannon, Simpson, observed species per sample
- **Beta diversity:** Bray-Curtis distance matrix (10x10)
- **Differential abundance:** Kruskal-Wallis test comparing healthy vs disease groups
- **Dashboard:** Interactive HTML report at `results/report/dashboard.html`
- **Figures:** Publication-quality PNGs at `results/report/figures/`
