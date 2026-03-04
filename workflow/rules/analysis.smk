# =============================================================================
# Analysis — Co-occurrence, diversity, and differential abundance
# =============================================================================
# The CLI's `magi analysis` command runs co-occurrence network inference,
# diversity calculations, and differential abundance testing in a single call.
# =============================================================================


rule analysis:
    """
    Run all downstream analyses on the unified abundance matrix:
    co-occurrence networks, alpha/beta diversity, and differential abundance.
    """
    input:
        abundance=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        metadata=config["input"]["metadata"],
    output:
        results_dir=directory(config["project"]["output_dir"] + "/analysis"),
    params:
        method=config["analysis"]["cooccurrence"]["method"],
    log:
        config["project"]["output_dir"] + "/logs/analysis/analysis.log",
    conda:
        "../envs/spieceasi.yaml"
    threads: 4
    shell:
        """
        magi analysis \
            --input {input.abundance} \
            --method {params.method} \
            --metadata {input.metadata} \
            --output {output.results_dir} \
            2>&1 | tee {log}
        """
