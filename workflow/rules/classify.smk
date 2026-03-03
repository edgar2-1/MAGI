# =============================================================================
# Classify — Taxonomic classification for bacteriome, mycobiome, and virome
# =============================================================================
# These three rules are independent and can run in parallel.
# Each produces a per-sample abundance table and a classification report.
# =============================================================================


rule classify_bacteriome:
    """
    Classify bacterial taxa using Kraken2 against the GTDB database.
    """
    input:
        reads=get_classify_input,
    output:
        abundance=config["project"]["output_dir"] + "/classify/bacteriome/{sample}.abundance.tsv",
        report=config["project"]["output_dir"] + "/classify/bacteriome/{sample}.kreport",
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
        magi classify bacteriome \
            --input {input.reads} \
            --output {output.abundance} \
            --report {output.report} \
            --db {params.db} \
            --confidence {params.confidence} \
            --threads {threads} \
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
        report=config["project"]["output_dir"] + "/classify/mycobiome/{sample}.kreport",
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
        magi classify mycobiome \
            --input {input.reads} \
            --output {output.abundance} \
            --report {output.report} \
            --db {params.db} \
            --confidence {params.confidence} \
            --threads {threads} \
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
        report=config["project"]["output_dir"] + "/classify/virome/{sample}.virome_report.json",
    params:
        tool=config["classify"]["virome"]["tool"],
        db=config["classify"]["virome"]["db"],
    log:
        config["project"]["output_dir"] + "/logs/classify/{sample}.virome.log",
    conda:
        "../envs/genomad.yaml"
    threads: 8
    shell:
        """
        magi classify virome \
            --input {input.reads} \
            --output {output.abundance} \
            --report {output.report} \
            --tool {params.tool} \
            --db {params.db} \
            --threads {threads} \
            2>&1 | tee {log}
        """
