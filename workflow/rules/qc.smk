# =============================================================================
# QC — Quality control, adapter trimming, and host decontamination
# =============================================================================


rule qc_filter:
    """
    Run quality filtering on raw reads.
    Applies minimum quality, length filters, and optional host removal.
    """
    input:
        reads="data/raw/{sample}.fastq.gz",
    output:
        filtered=config["project"]["output_dir"] + "/qc/{sample}.filtered.fastq.gz",
        report=config["project"]["output_dir"] + "/qc/{sample}.qc_report.json",
    params:
        min_quality=config["qc"]["min_quality"],
        min_length=config["qc"]["min_length"],
        max_length=config["qc"].get("max_length", ""),
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
            --report {output.report} \
            --min-quality {params.min_quality} \
            --min-length {params.min_length} \
            --max-length {params.max_length} \
            --host-reference {params.host_ref} \
            --platform {params.platform} \
            --threads {threads} \
            2>&1 | tee {log}
        """


rule qc_multiqc:
    """
    Aggregate individual QC reports into a single MultiQC summary.
    """
    input:
        reports=expand(
            config["project"]["output_dir"] + "/qc/{sample}.qc_report.json",
            sample=glob_wildcards("data/raw/{sample}.fastq.gz").sample,
        ),
    output:
        summary=config["project"]["output_dir"] + "/qc/multiqc_report.html",
    log:
        config["project"]["output_dir"] + "/logs/qc/multiqc.log",
    conda:
        "../envs/qc.yaml"
    shell:
        """
        magi qc-summary \
            --input-dir {config[project][output_dir]}/qc \
            --output {output.summary} \
            2>&1 | tee {log}
        """
