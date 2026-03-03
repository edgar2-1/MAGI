# =============================================================================
# Reporting — Interactive dashboard and static figures
# =============================================================================


rule reporting_dashboard:
    """
    Generate an interactive HTML dashboard summarizing all pipeline outputs.
    """
    input:
        abundance=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        taxonomy=config["project"]["output_dir"] + "/unifier/unified_taxonomy.tsv",
        alpha=config["project"]["output_dir"] + "/analysis/diversity/alpha_diversity.tsv",
        pcoa=config["project"]["output_dir"] + "/analysis/diversity/pcoa_results.tsv",
        network=config["project"]["output_dir"] + "/analysis/cooccurrence/network.graphml",
        differential=config["project"]["output_dir"] + "/analysis/differential/results.tsv",
        correlation=config["project"]["output_dir"] + "/metadata/correlation_summary.tsv",
        metadata=config["input"]["metadata"],
    output:
        dashboard=config["project"]["output_dir"] + "/report/dashboard.html",
    params:
        project_name=config["project"]["name"],
        formats=",".join(config["reporting"]["formats"]),
    log:
        config["project"]["output_dir"] + "/logs/reporting/dashboard.log",
    conda:
        "../envs/base.yaml"
    shell:
        """
        magi report dashboard \
            --abundance {input.abundance} \
            --taxonomy {input.taxonomy} \
            --alpha-diversity {input.alpha} \
            --pcoa {input.pcoa} \
            --network {input.network} \
            --differential {input.differential} \
            --correlation {input.correlation} \
            --metadata {input.metadata} \
            --output {output.dashboard} \
            --project-name {params.project_name} \
            --formats {params.formats} \
            2>&1 | tee {log}
        """


rule reporting_figures:
    """
    Render static publication-quality figures in PNG and SVG formats.
    """
    input:
        abundance=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        taxonomy=config["project"]["output_dir"] + "/unifier/unified_taxonomy.tsv",
        alpha=config["project"]["output_dir"] + "/analysis/diversity/alpha_diversity.tsv",
        pcoa=config["project"]["output_dir"] + "/analysis/diversity/pcoa_results.tsv",
        network=config["project"]["output_dir"] + "/analysis/cooccurrence/network.graphml",
        differential=config["project"]["output_dir"] + "/analysis/differential/results.tsv",
        metadata=config["input"]["metadata"],
    output:
        flag=config["project"]["output_dir"] + "/report/figures_done.flag",
    params:
        outdir=config["project"]["output_dir"] + "/report/figures",
        formats=",".join(config["reporting"]["formats"]),
    log:
        config["project"]["output_dir"] + "/logs/reporting/figures.log",
    conda:
        "../envs/base.yaml"
    shell:
        """
        magi report figures \
            --abundance {input.abundance} \
            --taxonomy {input.taxonomy} \
            --alpha-diversity {input.alpha} \
            --pcoa {input.pcoa} \
            --network {input.network} \
            --differential {input.differential} \
            --metadata {input.metadata} \
            --output-dir {params.outdir} \
            --formats {params.formats} \
            2>&1 | tee {log}

        touch {output.flag}
        """
