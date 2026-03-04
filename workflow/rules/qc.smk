# =============================================================================
# QC — Quality control, adapter trimming, and host decontamination
# =============================================================================


rule qc_filter:
    """
    Run quality filtering on raw reads.
    Applies minimum quality, length filters, and optional host removal.
    """
    input:
        reads=READS_DIR + "/{sample}.fastq.gz",
    output:
        filtered=config["project"]["output_dir"] + "/qc/{sample}.filtered.fastq.gz",
    params:
        min_quality=config["qc"]["min_quality"],
        min_length=config["qc"]["min_length"],
        host_ref=config["qc"].get("host_reference", ""),
        platform=config["input"]["platform"],
    log:
        config["project"]["output_dir"] + "/logs/qc/{sample}.log",
    conda:
        "../envs/qc.yaml"
    threads: 4
    shell:
        """
        magi qc \
            --input {input.reads} \
            --output {output.filtered} \
            --platform {params.platform} \
            --min-quality {params.min_quality} \
            --min-length {params.min_length} \
            --threads {threads} \
            $(if [ -n "{params.host_ref}" ]; then echo "--host-reference {params.host_ref}"; fi) \
            2>&1 | tee {log}
        """


rule qc_multiqc:
    """
    Aggregate individual QC reports into a single MultiQC summary.
    """
    input:
        reports=expand(
            config["project"]["output_dir"] + "/qc/{sample}.filtered.fastq.gz",
            sample=SAMPLES,
        ),
    output:
        summary=config["project"]["output_dir"] + "/qc/multiqc_report.html",
    log:
        config["project"]["output_dir"] + "/logs/qc/multiqc.log",
    conda:
        "../envs/qc.yaml"
    shell:
        """
        multiqc \
            {config[project][output_dir]}/qc \
            --outdir $(dirname {output.summary}) \
            --filename $(basename {output.summary}) \
            --force \
            2>&1 | tee {log}
        """
