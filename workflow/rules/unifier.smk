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
            sample=glob_wildcards("data/raw/{sample}.fastq.gz").sample,
        ),
        mycobiome=expand(
            config["project"]["output_dir"] + "/classify/mycobiome/{sample}.abundance.tsv",
            sample=glob_wildcards("data/raw/{sample}.fastq.gz").sample,
        ),
        virome=expand(
            config["project"]["output_dir"] + "/classify/virome/{sample}.abundance.tsv",
            sample=glob_wildcards("data/raw/{sample}.fastq.gz").sample,
        ),
    output:
        merged=config["project"]["output_dir"] + "/unifier/merged_abundance.tsv",
        normalized=config["project"]["output_dir"] + "/unifier/normalized_abundance.tsv",
        taxonomy=config["project"]["output_dir"] + "/unifier/unified_taxonomy.tsv",
    params:
        normalization=config["unifier"]["normalization"],
        min_prevalence=config["unifier"]["min_prevalence"],
        taxonomy_backend=config["unifier"]["taxonomy_backend"],
    log:
        config["project"]["output_dir"] + "/logs/unifier/unifier.log",
    conda:
        "../envs/base.yaml"
    shell:
        """
        magi unify \
            --bacteriome-dir {config[project][output_dir]}/classify/bacteriome \
            --mycobiome-dir {config[project][output_dir]}/classify/mycobiome \
            --virome-dir {config[project][output_dir]}/classify/virome \
            --output-merged {output.merged} \
            --output-normalized {output.normalized} \
            --output-taxonomy {output.taxonomy} \
            --normalization {params.normalization} \
            --min-prevalence {params.min_prevalence} \
            --taxonomy-backend {params.taxonomy_backend} \
            2>&1 | tee {log}
        """
