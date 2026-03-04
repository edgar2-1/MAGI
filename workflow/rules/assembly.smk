# =============================================================================
# Assembly — Optional metagenomic assembly
# =============================================================================
# This step is conditional on config["assembly"]["enabled"].
# When disabled, downstream rules consume QC-filtered reads directly.
# There is no CLI command for assembly; it is only available as a Python API.
# We use a Snakemake `run:` directive to call the function directly.
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
            stats=config["project"]["output_dir"] + "/assembly/{sample}/assembly_stats.json",
        params:
            tool=config["assembly"]["tool"],
            platform=config["input"]["platform"],
        log:
            config["project"]["output_dir"] + "/logs/assembly/{sample}.log",
        conda:
            "../envs/base.yaml"
        threads: 8
        run:
            from magi.assembly.assemblers import run_assembly
            from pathlib import Path

            run_assembly(
                input_path=Path(input.reads),
                output_dir=Path(output.contigs).parent,
                tool=params.tool,
                platform=params.platform,
                threads=threads,
            )


    def get_classify_input(wildcards):
        """When assembly is enabled, classification uses contigs."""
        return config["project"]["output_dir"] + f"/assembly/{wildcards.sample}/contigs.fasta"

else:

    def get_classify_input(wildcards):
        """When assembly is disabled, classification uses QC-filtered reads."""
        return config["project"]["output_dir"] + f"/qc/{wildcards.sample}.filtered.fastq.gz"
