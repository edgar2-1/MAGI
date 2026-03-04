# =============================================================================
# Unifier — Merge and normalize abundance tables across all kingdoms
# =============================================================================
# Combines bacteriome, mycobiome, and virome abundance tables into a single
# unified feature table, applies normalization, and filters by prevalence.
# =============================================================================


rule unifier:
    """
    Merge classification outputs from all three kingdoms into a single
    normalized abundance table with unified taxonomy.
    """
    input:
        bacteriome=expand(
            config["project"]["output_dir"] + "/classify/bacteriome/{sample}.abundance.tsv",
            sample=SAMPLES,
        ),
        mycobiome=expand(
            config["project"]["output_dir"] + "/classify/mycobiome/{sample}.abundance.tsv",
            sample=SAMPLES,
        ),
        virome=expand(
            config["project"]["output_dir"] + "/classify/virome/{sample}.abundance.tsv",
            sample=SAMPLES,
        ),
    output:
        normalized=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
    params:
        normalization=config["unifier"]["normalization"],
        min_prevalence=config["unifier"]["min_prevalence"],
        input_dir=config["project"]["output_dir"] + "/classify",
    log:
        config["project"]["output_dir"] + "/logs/unifier/unifier.log",
    conda:
        "../envs/base.yaml"
    shell:
        """
        magi unifier \
            --input {params.input_dir} \
            --normalize {params.normalization} \
            --min-prevalence {params.min_prevalence} \
            --output {output.normalized} \
            2>&1 | tee {log}
        """
