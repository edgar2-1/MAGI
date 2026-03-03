# =============================================================================
# Analysis — Co-occurrence, diversity, and differential abundance
# =============================================================================


rule analysis_cooccurrence:
    """
    Build co-occurrence networks across kingdoms using SpiecEasi or SparCC.
    """
    input:
        abundance=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        taxonomy=config["project"]["output_dir"] + "/unifier/unified_taxonomy.tsv",
    output:
        network=config["project"]["output_dir"] + "/analysis/cooccurrence/network.graphml",
        edges=config["project"]["output_dir"] + "/analysis/cooccurrence/edge_table.tsv",
    params:
        method=config["analysis"]["cooccurrence"]["method"],
        min_abundance=config["analysis"]["cooccurrence"]["min_abundance"],
    log:
        config["project"]["output_dir"] + "/logs/analysis/cooccurrence.log",
    conda:
        "../envs/spieceasi.yaml"
    threads: 4
    shell:
        """
        magi analysis cooccurrence \
            --input {input.abundance} \
            --taxonomy {input.taxonomy} \
            --output-network {output.network} \
            --output-edges {output.edges} \
            --method {params.method} \
            --min-abundance {params.min_abundance} \
            --threads {threads} \
            2>&1 | tee {log}
        """


rule analysis_diversity:
    """
    Compute alpha and beta diversity metrics.
    """
    input:
        abundance=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        metadata=config["input"]["metadata"],
    output:
        alpha=config["project"]["output_dir"] + "/analysis/diversity/alpha_diversity.tsv",
        beta=config["project"]["output_dir"] + "/analysis/diversity/beta_distance_matrices/",
        pcoa=config["project"]["output_dir"] + "/analysis/diversity/pcoa_results.tsv",
    params:
        alpha_metrics=",".join(config["analysis"]["diversity"]["alpha_metrics"]),
        beta_metrics=",".join(config["analysis"]["diversity"]["beta_metrics"]),
    log:
        config["project"]["output_dir"] + "/logs/analysis/diversity.log",
    conda:
        "../envs/base.yaml"
    shell:
        """
        magi analysis diversity \
            --input {input.abundance} \
            --metadata {input.metadata} \
            --output-alpha {output.alpha} \
            --output-beta {output.beta} \
            --output-pcoa {output.pcoa} \
            --alpha-metrics {params.alpha_metrics} \
            --beta-metrics {params.beta_metrics} \
            2>&1 | tee {log}
        """


rule analysis_differential:
    """
    Perform differential abundance testing (ANCOM-BC or ALDEx2).
    """
    input:
        abundance=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        metadata=config["input"]["metadata"],
    output:
        results=config["project"]["output_dir"] + "/analysis/differential/results.tsv",
        volcano=config["project"]["output_dir"] + "/analysis/differential/volcano_plot.svg",
    params:
        method=config["analysis"]["differential"]["method"],
    log:
        config["project"]["output_dir"] + "/logs/analysis/differential.log",
    conda:
        "../envs/base.yaml"
    shell:
        """
        magi analysis differential \
            --input {input.abundance} \
            --metadata {input.metadata} \
            --output {output.results} \
            --output-plot {output.volcano} \
            --method {params.method} \
            2>&1 | tee {log}
        """
