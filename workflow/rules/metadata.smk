# =============================================================================
# Metadata Correlation — Random forest feature importance
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
        random_forest_flag=lambda wildcards: "" if config["metadata_correlation"]["random_forest"] else "--no-random-forest",
    log:
        config["project"]["output_dir"] + "/logs/metadata/correlation.log",
    conda:
        "../envs/base.yaml"
    shell:
        """
        magi metadata \
            --input {input.abundance} \
            --metadata {input.metadata} \
            --output {output.summary} \
            {params.random_forest_flag} \
            2>&1 | tee {log}
        """
