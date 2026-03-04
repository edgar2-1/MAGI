# =============================================================================
# Metadata Correlation — Random forest feature importance
# =============================================================================
# There is no CLI command for metadata correlation; it is only available as
# a Python API.  We use a Snakemake `run:` directive to call the function
# directly.
# =============================================================================


rule metadata_correlation:
    """
    Run metadata-microbiome correlation analysis.
    Optionally trains a random forest model for feature importance ranking.
    """
    input:
        abundance=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        metadata=config["input"]["metadata"],
    output:
        summary=config["project"]["output_dir"] + "/metadata/correlation_summary.json",
    params:
        random_forest=config["metadata_correlation"]["random_forest"],
    log:
        config["project"]["output_dir"] + "/logs/metadata/correlation.log",
    conda:
        "../envs/base.yaml"
    run:
        import json
        import pandas as pd
        from pathlib import Path
        from magi.metadata.correlation import run_correlation

        matrix = pd.read_csv(input.abundance, sep="\t", index_col=0)
        meta = pd.read_csv(input.metadata, sep="\t", index_col=0)
        results = run_correlation(matrix, meta, random_forest=params.random_forest)

        # Save summary
        Path(output.summary).parent.mkdir(parents=True, exist_ok=True)
        with open(output.summary, "w") as f:
            json.dump(results, f, indent=2, default=str)
