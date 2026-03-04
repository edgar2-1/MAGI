# =============================================================================
# Reporting — Interactive dashboard and static figures
# =============================================================================
# The CLI's `magi report` command generates both the interactive dashboard
# and publication-quality figures in a single call.
# =============================================================================


rule reporting:
    """
    Generate an interactive HTML dashboard and static publication-quality
    figures summarizing all pipeline outputs.
    """
    input:
        analysis_dir=config["project"]["output_dir"] + "/analysis",
        correlation=config["project"]["output_dir"] + "/metadata/correlation_summary.json",
    output:
        dashboard=config["project"]["output_dir"] + "/report/dashboard.html",
        flag=config["project"]["output_dir"] + "/report/figures_done.flag",
    params:
        report_dir=config["project"]["output_dir"] + "/report",
        formats=" ".join(
            f"--formats {fmt}" for fmt in config["reporting"]["formats"]
        ),
    log:
        config["project"]["output_dir"] + "/logs/reporting/report.log",
    conda:
        "../envs/base.yaml"
    shell:
        """
        magi report \
            --input {input.analysis_dir} \
            --output {params.report_dir} \
            {params.formats} \
            2>&1 | tee {log}

        touch {output.flag}
        """
