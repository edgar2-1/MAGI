# =============================================================================
# Metadata Correlation — MaAsLin2, LEfSe, and Random Forest
# =============================================================================


rule metadata_correlation:
    """
    Run metadata-microbiome correlation analysis using MaAsLin2 and LEfSe.
    Optionally trains a random forest model for feature importance ranking.
    """
    input:
        abundance=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        taxonomy=config["project"]["output_dir"] + "/unifier/unified_taxonomy.tsv",
        metadata=config["input"]["metadata"],
    output:
        maaslin2=config["project"]["output_dir"] + "/metadata/maaslin2_results/",
        lefse=config["project"]["output_dir"] + "/metadata/lefse_results.tsv",
        rf_importance=config["project"]["output_dir"] + "/metadata/rf_feature_importance.tsv",
        summary=config["project"]["output_dir"] + "/metadata/correlation_summary.tsv",
    params:
        tools=",".join(config["metadata_correlation"]["tools"]),
        random_forest=config["metadata_correlation"]["random_forest"],
    log:
        config["project"]["output_dir"] + "/logs/metadata/correlation.log",
    conda:
        "../envs/base.yaml"
    threads: 4
    shell:
        """
        magi metadata-correlation \
            --input {input.abundance} \
            --taxonomy {input.taxonomy} \
            --metadata {input.metadata} \
            --output-maaslin2 {output.maaslin2} \
            --output-lefse {output.lefse} \
            --output-rf {output.rf_importance} \
            --output-summary {output.summary} \
            --tools {params.tools} \
            --random-forest {params.random_forest} \
            --threads {threads} \
            2>&1 | tee {log}
        """
