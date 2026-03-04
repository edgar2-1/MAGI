# =============================================================================
# Classify — Taxonomic classification for bacteriome, mycobiome, and virome
# =============================================================================
# These three rules are independent and can run in parallel.
# Each produces a per-sample abundance table.
# =============================================================================


rule classify_bacteriome:
    """
    Classify bacterial taxa using Kraken2 against the GTDB database.
    """
    input:
        reads=get_classify_input,
    output:
        abundance=config["project"]["output_dir"] + "/classify/bacteriome/{sample}.abundance.tsv",
    params:
        db=config["classify"]["bacteriome"]["db"],
        confidence=config["classify"]["bacteriome"]["confidence"],
    log:
        config["project"]["output_dir"] + "/logs/classify/{sample}.bacteriome.log",
    conda:
        "../envs/kraken2.yaml"
    threads: 8
    shell:
        """
        magi classify \
            --input {input.reads} \
            --kingdom bacteria \
            --db {params.db} \
            --confidence {params.confidence} \
            --output {output.abundance} \
            2>&1 | tee {log}
        """


rule classify_mycobiome:
    """
    Classify fungal taxa using Kraken2 against the UNITE database.
    """
    input:
        reads=get_classify_input,
    output:
        abundance=config["project"]["output_dir"] + "/classify/mycobiome/{sample}.abundance.tsv",
    params:
        db=config["classify"]["mycobiome"]["db"],
        confidence=config["classify"]["mycobiome"]["confidence"],
    log:
        config["project"]["output_dir"] + "/logs/classify/{sample}.mycobiome.log",
    conda:
        "../envs/kraken2.yaml"
    threads: 8
    shell:
        """
        magi classify \
            --input {input.reads} \
            --kingdom fungi \
            --db {params.db} \
            --confidence {params.confidence} \
            --output {output.abundance} \
            2>&1 | tee {log}
        """


rule classify_virome:
    """
    Identify and classify viral sequences using geNomad or VirSorter2.
    """
    input:
        reads=get_classify_input,
    output:
        abundance=config["project"]["output_dir"] + "/classify/virome/{sample}.abundance.tsv",
    params:
        db=config["classify"]["virome"]["db"],
    log:
        config["project"]["output_dir"] + "/logs/classify/{sample}.virome.log",
    conda:
        "../envs/genomad.yaml"
    threads: 8
    shell:
        """
        magi classify \
            --input {input.reads} \
            --kingdom virus \
            --db {params.db} \
            --output {output.abundance} \
            2>&1 | tee {log}
        """
