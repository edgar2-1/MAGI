"""Main CLI for the MAGI pipeline.

Provides subcommands for quality control, classification, unification,
analysis, reporting, and database management.
"""

import click
import logging

logger = logging.getLogger(__name__)


@click.group()
@click.option("--config", type=click.Path(exists=True), default=None,
              help="Path to a YAML configuration file.")
@click.pass_context
def main(ctx, config):
    """MAGI - Metagenomics Aggregation and Global Integration pipeline."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@main.command()
@click.pass_context
def run(ctx):
    """Run the full MAGI pipeline using Snakemake.

    Loads the configuration YAML and invokes the Snakemake workflow
    end-to-end.
    """
    config_path = ctx.obj.get("config")
    if config_path is None:
        click.echo("Error: --config is required for the 'run' command.", err=True)
        raise SystemExit(1)
    click.echo(f"Loading configuration from {config_path}")
    # TODO: load YAML and invoke Snakemake
    click.echo("Invoking Snakemake workflow...")
    pass


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to input reads.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write filtered reads.")
@click.option("--platform", type=click.Choice(["hifi", "nanopore"]), required=True,
              help="Sequencing platform (hifi or nanopore).")
@click.option("--min-quality", type=int, default=20,
              help="Minimum read quality score.")
@click.option("--min-length", type=int, default=1000,
              help="Minimum read length.")
@click.option("--host-reference", type=click.Path(), default=None,
              help="Path to host reference genome for decontamination.")
def qc(input_path, output_path, platform, min_quality, min_length, host_reference):
    """Run quality control on sequencing reads.

    Filters, trims, and optionally removes host reads from the input
    FASTQ files.
    """
    click.echo(f"Running QC on {input_path} (platform={platform})")
    click.echo(f"  min_quality={min_quality}, min_length={min_length}")
    if host_reference:
        click.echo(f"  Host removal using {host_reference}")
    # TODO: call qc module functions
    pass


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to input reads or contigs.")
@click.option("--kingdom", type=click.Choice(["bacteria", "fungi", "virus"]), required=True,
              help="Target kingdom for classification.")
@click.option("--db", "db_path", type=click.Path(), default=None,
              help="Path to classification database.")
@click.option("--confidence", type=float, default=0.7,
              help="Minimum confidence threshold for classification.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write classification results.")
def classify(input_path, kingdom, db_path, confidence, output_path):
    """Classify reads or contigs by kingdom.

    Routes to the appropriate classifier (bacteriome, mycobiome, or
    virome) based on the selected kingdom.
    """
    click.echo(f"Classifying {input_path} for kingdom={kingdom}")
    click.echo(f"  confidence={confidence}, output={output_path}")
    # TODO: call classify module functions
    pass


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to classification output directory.")
@click.option("--normalize", "normalize_method", type=click.Choice(["clr", "relative", "tss"]),
              default="clr", help="Normalization method to apply.")
@click.option("--min-prevalence", type=float, default=0.1,
              help="Minimum prevalence threshold for feature retention.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write the unified feature matrix.")
def unifier(input_path, normalize_method, min_prevalence, output_path):
    """Unify and normalize classification outputs.

    Standardizes outputs from all classifiers into a single feature
    matrix, then applies the selected normalization method.
    """
    click.echo(f"Unifying outputs from {input_path}")
    click.echo(f"  normalize={normalize_method}, min_prevalence={min_prevalence}")
    # TODO: call unifier module functions
    pass


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to the unified feature matrix.")
@click.option("--method", type=click.Choice(["spieceasi", "sparcc"]),
              default="spieceasi", help="Co-occurrence network method.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write analysis results.")
def analysis(input_path, method, output_path):
    """Run downstream analyses on the unified matrix.

    Includes co-occurrence network inference, diversity calculations,
    and differential abundance testing.
    """
    click.echo(f"Running analysis on {input_path} with method={method}")
    # TODO: call analysis module functions
    pass


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to analysis results directory.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write the report.")
@click.option("--formats", multiple=True, default=("html",),
              help="Output formats for the report (e.g., html, pdf, png).")
def report(input_path, output_path, formats):
    """Generate reports and visualizations.

    Produces an interactive dashboard and publication-quality figures
    from the analysis results.
    """
    click.echo(f"Generating report from {input_path}")
    click.echo(f"  output={output_path}, formats={formats}")
    # TODO: call reporting module functions
    pass


@main.group()
def db():
    """Manage reference databases for classification."""
    pass


@db.command()
@click.option("--all", "download_all", is_flag=True, default=False,
              help="Download databases for all kingdoms.")
@click.option("--kingdom", type=click.Choice(["bacteria", "fungi", "virus"]),
              default=None, help="Download database for a specific kingdom.")
def download(download_all, kingdom):
    """Download reference databases.

    Fetches the required classification databases for one or all
    kingdoms.
    """
    if download_all:
        click.echo("Downloading databases for all kingdoms...")
    elif kingdom:
        click.echo(f"Downloading database for kingdom={kingdom}...")
    else:
        click.echo("Error: specify --all or --kingdom.", err=True)
        raise SystemExit(1)
    # TODO: implement database download logic
    pass


@db.command()
def status():
    """Show the status of installed reference databases.

    Lists each database, its version, size, and whether it is up to
    date.
    """
    click.echo("Checking database status...")
    # TODO: implement database status check
    pass


if __name__ == "__main__":
    main()
