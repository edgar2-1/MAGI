# =============================================================================
# Assembly — Optional metagenomic assembly
# =============================================================================
# This step is conditional on config["assembly"]["enabled"].
# When disabled, downstream rules consume QC-filtered reads directly.
# =============================================================================


if config["assembly"]["enabled"]:

    rule assembly:
        """
        Perform metagenomic assembly using the configured tool
        (metaflye or hifiasm-meta).
        """
        input:
            reads=config["project"]["output_dir"] + "/qc/{sample}.filtered.fastq.gz",
        output:
            contigs=config["project"]["output_dir"] + "/assembly/{sample}/contigs.fasta",
        params:
            tool=config["assembly"]["tool"],
        log:
            config["project"]["output_dir"] + "/logs/assembly/{sample}.log",
        conda:
            "../envs/base.yaml"
        threads: 8
        shell:
            """
            magi assemble \
                --input {input.reads} \
                --output {output.contigs} \
                --tool {params.tool} \
                --threads {threads} \
                2>&1 | tee {log}
            """


    def get_classify_input(wildcards):
        """When assembly is enabled, classification uses contigs."""
        return config["project"]["output_dir"] + f"/assembly/{wildcards.sample}/contigs.fasta"

else:

    def get_classify_input(wildcards):
        """When assembly is disabled, classification uses QC-filtered reads."""
        return config["project"]["output_dir"] + f"/qc/{wildcards.sample}.filtered.fastq.gz"
