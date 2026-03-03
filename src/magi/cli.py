"""Main CLI for the MAGI pipeline.

Provides subcommands for quality control, classification, unification,
analysis, reporting, and database management.
"""

import logging
from pathlib import Path

import click

import subprocess as _subprocess

logger = logging.getLogger(__name__)


@click.group()
@click.option("--config", type=click.Path(exists=True), default=None,
              help="Path to a YAML configuration file.")
@click.pass_context
def main(ctx, config):
    """MAGI - Multi-kingdom Analysis of Genomic Interactions."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@main.command()
@click.option("--cores", type=int, default=4, help="Number of cores for Snakemake.")
@click.option("--dryrun", is_flag=True, default=False, help="Show what would be done.")
@click.pass_context
def run(ctx, cores, dryrun):
    """Run the full MAGI pipeline using Snakemake."""
    config_path = ctx.obj.get("config")
    if config_path is None:
        click.echo("Error: --config is required for the 'run' command.", err=True)
        raise SystemExit(1)

    snakefile = Path(__file__).parent.parent.parent / "workflow" / "Snakefile"
    if not snakefile.exists():
        snakefile = Path("workflow") / "Snakefile"

    click.echo(f"Loading configuration from {config_path}")
    click.echo(f"Invoking Snakemake workflow (cores={cores}, dryrun={dryrun})")

    cmd = [
        "snakemake",
        "--snakefile", str(snakefile),
        "--configfile", str(config_path),
        "--cores", str(cores),
        "--use-conda",
    ]
    if dryrun:
        cmd.append("--dryrun")

    result = _subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        click.echo(result.stdout)
    if result.returncode != 0:
        click.echo(f"Snakemake failed:\n{result.stderr}", err=True)
        raise SystemExit(1)

    click.echo("Pipeline completed successfully.")


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
    from magi.qc.filtering import filter_reads
    from magi.qc.host_removal import remove_host

    click.echo(f"Running QC on {input_path} (platform={platform})")

    filter_reads(
        input_path=Path(input_path),
        output_path=Path(output_path),
        min_quality=min_quality,
        min_length=min_length,
        platform=platform,
    )
    click.echo(f"Filtered reads written to {output_path}")

    if host_reference:
        dehosted_path = Path(output_path).with_suffix(".dehosted.fastq")
        remove_host(
            input_path=Path(output_path),
            output_path=dehosted_path,
            host_reference=Path(host_reference),
        )
        click.echo(f"Host-free reads written to {dehosted_path}")


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to input reads or contigs.")
@click.option("--kingdom", type=click.Choice(["bacteria", "fungi", "virus"]), required=True,
              help="Target kingdom for classification.")
@click.option("--db", "db_path", type=click.Path(exists=True), required=True,
              help="Path to classification database.")
@click.option("--confidence", type=float, default=0.2,
              help="Minimum confidence threshold for classification.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write classification results.")
def classify(input_path, kingdom, db_path, confidence, output_path):
    """Classify reads or contigs by kingdom.

    Routes to the appropriate classifier (bacteriome, mycobiome, or
    virome) based on the selected kingdom.
    """
    click.echo(f"Classifying {input_path} for kingdom={kingdom}")

    if kingdom == "bacteria":
        from magi.classify.bacteriome import classify_bacteriome
        classify_bacteriome(
            input_path=Path(input_path),
            output_path=Path(output_path),
            db_path=Path(db_path),
            confidence=confidence,
        )
    elif kingdom == "fungi":
        from magi.classify.mycobiome import classify_mycobiome
        classify_mycobiome(
            input_path=Path(input_path),
            output_path=Path(output_path),
            db_path=Path(db_path),
            confidence=confidence,
        )
    elif kingdom == "virus":
        from magi.classify.virome import classify_virome
        classify_virome(
            input_path=Path(input_path),
            output_path=Path(output_path),
            db_path=Path(db_path),
        )

    click.echo(f"Classification results written to {output_path}")


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
    from magi.unifier.matrix import build_feature_matrix
    from magi.unifier.normalize import normalize
    from magi.unifier.standardize import standardize_outputs

    input_dir = Path(input_path)
    output_file = Path(output_path)

    click.echo(f"Unifying outputs from {input_dir}")

    # Standardize each kingdom
    for kingdom, method in [("bacteria", "kraken2"), ("fungi", "kraken2"), ("virus", "genomad")]:
        df = standardize_outputs(input_dir, kingdom=kingdom, method=method)
        if not df.empty:
            std_path = input_dir / f"standardized_{kingdom}.tsv"
            df.to_csv(std_path, sep="\t", index=False)
            click.echo(f"  Standardized {kingdom}: {len(df)} records")

    # Build feature matrix
    matrix = build_feature_matrix(input_dir)
    click.echo(f"  Feature matrix: {matrix.shape[0]} samples x {matrix.shape[1]} features")

    # Normalize
    normalized = normalize(matrix, method=normalize_method)

    # Filter by prevalence
    prevalence = (normalized > 0).sum() / len(normalized)
    kept = prevalence[prevalence >= min_prevalence].index
    normalized = normalized[kept]
    click.echo(f"  After prevalence filter ({min_prevalence}): {normalized.shape[1]} features")

    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(output_file, sep="\t")
    click.echo(f"Unified matrix written to {output_file}")


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to the unified feature matrix (TSV).")
@click.option("--method", type=click.Choice(["spieceasi", "sparcc"]),
              default="spieceasi", help="Co-occurrence network method.")
@click.option("--metadata", type=click.Path(exists=True), default=None,
              help="Path to metadata TSV for differential abundance.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write analysis results directory.")
def analysis(input_path, method, metadata, output_path):
    """Run downstream analyses on the unified matrix.

    Includes co-occurrence network inference, diversity calculations,
    and differential abundance testing.
    """
    import json

    import networkx as nx
    import pandas as pd

    from magi.analysis.cooccurrence import run_cooccurrence
    from magi.analysis.differential import run_differential
    from magi.analysis.diversity import compute_alpha_diversity, compute_beta_diversity

    matrix = pd.read_csv(input_path, sep="\t", index_col=0)
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Running analysis on {input_path} ({matrix.shape[0]} samples x {matrix.shape[1]} taxa)")

    # Co-occurrence network
    G = run_cooccurrence(matrix, method=method)
    network_path = output_dir / "cooccurrence_network.json"
    network_data = nx.node_link_data(G)
    with open(network_path, "w") as f:
        json.dump(network_data, f, indent=2)
    click.echo(f"  Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges -> {network_path}")

    # Alpha diversity
    alpha = compute_alpha_diversity(matrix)
    alpha_path = output_dir / "alpha_diversity.tsv"
    alpha.to_csv(alpha_path, sep="\t")
    click.echo(f"  Alpha diversity -> {alpha_path}")

    # Beta diversity
    beta = compute_beta_diversity(matrix)
    beta_path = output_dir / "beta_diversity.tsv"
    beta.to_csv(beta_path, sep="\t")
    click.echo(f"  Beta diversity -> {beta_path}")

    # Differential abundance (if metadata provided)
    if metadata:
        meta_df = pd.read_csv(metadata, sep="\t", index_col=0)
        diff = run_differential(matrix, meta_df)
        diff_path = output_dir / "differential_abundance.tsv"
        diff.to_csv(diff_path, sep="\t")
        click.echo(f"  Differential abundance -> {diff_path}")

    click.echo(f"Analysis complete. Results in {output_dir}")


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to analysis results directory.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write the report output directory.")
@click.option("--formats", multiple=True, default=("png",),
              help="Output formats for static figures (e.g., png, svg).")
def report(input_path, output_path, formats):
    """Generate reports and visualizations.

    Produces an interactive dashboard and publication-quality figures
    from the analysis results.
    """
    from magi.reporting.dashboard import generate_dashboard
    from magi.reporting.figures import generate_figures

    results_dir = Path(input_path)
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Generating report from {results_dir}")

    # Interactive HTML dashboard
    dashboard_path = output_dir / "dashboard.html"
    generate_dashboard(results_dir, dashboard_path)
    click.echo(f"  Dashboard -> {dashboard_path}")

    # Static publication figures
    figures_dir = output_dir / "figures"
    generate_figures(results_dir, figures_dir, formats=list(formats))
    click.echo(f"  Figures -> {figures_dir}")

    click.echo(f"Report complete. Output in {output_dir}")


@main.group()
def db():
    """Manage reference databases for classification."""


@db.command()
@click.option("--all", "download_all", is_flag=True, default=False,
              help="Download databases for all kingdoms.")
@click.option("--kingdom", type=click.Choice(["bacteria", "fungi", "virus"]),
              default=None, help="Download database for a specific kingdom.")
@click.option("--db-dir", type=click.Path(), default="databases",
              help="Directory to store databases.")
def download(download_all, kingdom, db_dir):
    """Download reference databases.

    Fetches the required classification databases for one or all
    kingdoms.
    """
    from magi.db.manager import download_database, DB_REGISTRY

    db_path = Path(db_dir)

    if download_all:
        click.echo("Downloading databases for all kingdoms...")
        for k in DB_REGISTRY:
            click.echo(f"  Downloading {k}...")
            download_database(k, db_path)
            click.echo(f"  {k} complete.")
    elif kingdom:
        click.echo(f"Downloading database for kingdom={kingdom}...")
        download_database(kingdom, db_path)
        click.echo(f"Download complete for {kingdom}.")
    else:
        click.echo("Error: specify --all or --kingdom.", err=True)
        raise SystemExit(1)


@db.command()
@click.option("--db-dir", type=click.Path(), default="databases",
              help="Directory where databases are stored.")
def status(db_dir):
    """Show the status of installed reference databases."""
    from magi.db.manager import get_db_status

    db_path = Path(db_dir)
    click.echo("Checking database status...")
    statuses = get_db_status(db_path)
    for kingdom, info in statuses.items():
        state = "INSTALLED" if info["installed"] else "NOT INSTALLED"
        click.echo(f"  {kingdom}: {info['name']} - {state}")


if __name__ == "__main__":
    main()
