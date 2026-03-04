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
@click.option("--profile", type=click.Path(), default=None,
              help="Path to Snakemake cluster profile directory.")
@click.pass_context
def run(ctx, cores, dryrun, profile):
    """Run the full MAGI pipeline using Snakemake."""
    config_path = ctx.obj.get("config")
    if config_path is None:
        click.echo("Error: --config is required for the 'run' command.", err=True)
        raise SystemExit(1)

    # Try multiple locations for the Snakefile
    candidates = [
        Path(__file__).parent.parent.parent / "workflow" / "Snakefile",  # dev/editable install
        Path(__file__).parent / "workflow" / "Snakefile",  # bundled in package
        Path("workflow") / "Snakefile",  # CWD
    ]
    snakefile = None
    for candidate in candidates:
        if candidate.exists():
            snakefile = candidate
            break

    if snakefile is None:
        click.echo(
            "Error: Cannot find the Snakemake workflow files.\n"
            "  The 'magi run' command requires the workflow/ directory.\n"
            "  Either:\n"
            "    1. Run from the MAGI repository root, or\n"
            "    2. Install in development mode: pip install -e .\n"
            "  Individual steps (qc, classify, etc.) work without the workflow.",
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"Loading configuration from {config_path}")
    click.echo(f"Invoking Snakemake workflow (cores={cores}, dryrun={dryrun})")

    cmd = [
        "snakemake",
        "--snakefile", str(snakefile),
        "--configfile", str(config_path),
        "--cores", str(cores),
        "--use-conda",
    ]
    if profile:
        cmd.extend(["--profile", str(profile)])
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
@click.option("--threads", type=int, default=4, help="Number of threads for QC tools.")
def qc(input_path, output_path, platform, min_quality, min_length, host_reference, threads):
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
        threads=threads,
    )
    click.echo(f"Filtered reads written to {output_path}")

    if host_reference:
        dehosted_path = Path(output_path).with_suffix(".dehosted.fastq")
        remove_host(
            input_path=Path(output_path),
            output_path=dehosted_path,
            host_reference=Path(host_reference),
            threads=threads,
            platform=platform,
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
@click.option("--threads", type=int, default=8, help="Number of threads for classification tools.")
@click.option("--read-length", type=int, default=150,
              help="Read length for Bracken abundance estimation (default 150 for short reads, use higher for long reads).")
def classify(input_path, kingdom, db_path, confidence, output_path, threads, read_length):
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
            threads=threads,
            read_length=read_length,
        )
    elif kingdom == "fungi":
        from magi.classify.mycobiome import classify_mycobiome
        classify_mycobiome(
            input_path=Path(input_path),
            output_path=Path(output_path),
            db_path=Path(db_path),
            confidence=confidence,
            threads=threads,
            read_length=read_length,
        )
    elif kingdom == "virus":
        from magi.classify.virome import classify_virome
        classify_virome(
            input_path=Path(input_path),
            output_path=Path(output_path),
            db_path=Path(db_path),
            threads=threads,
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

    # Filter by prevalence BEFORE normalization (on raw counts)
    prevalence = (matrix > 0).sum() / len(matrix)
    kept = prevalence[prevalence >= min_prevalence].index
    matrix = matrix[kept]
    click.echo(f"  After prevalence filter ({min_prevalence}): {matrix.shape[1]} features")

    # Normalize AFTER filtering
    normalized = normalize(matrix, method=normalize_method)

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
@click.option("--alpha-metrics", type=str, default="shannon,simpson,observed_species",
              help="Comma-separated alpha diversity metrics (shannon, simpson, observed_species, chao1).")
@click.option("--beta-metrics", type=str, default="bray_curtis",
              help="Comma-separated beta diversity metrics (bray_curtis, jaccard).")
def analysis(input_path, method, metadata, output_path, alpha_metrics, beta_metrics):
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

    alpha_list = [m.strip() for m in alpha_metrics.split(",")]
    beta_list = [m.strip() for m in beta_metrics.split(",")]

    click.echo(f"Running analysis on {input_path} ({matrix.shape[0]} samples x {matrix.shape[1]} taxa)")

    # Co-occurrence network
    G = run_cooccurrence(matrix, method=method)
    network_path = output_dir / "cooccurrence_network.json"
    network_data = nx.node_link_data(G)
    with open(network_path, "w") as f:
        json.dump(network_data, f, indent=2)
    click.echo(f"  Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges -> {network_path}")

    # Alpha diversity
    alpha = compute_alpha_diversity(matrix, metrics=alpha_list)
    alpha_path = output_dir / "alpha_diversity.tsv"
    alpha.to_csv(alpha_path, sep="\t")
    click.echo(f"  Alpha diversity -> {alpha_path}")

    # Beta diversity
    beta = compute_beta_diversity(matrix, metrics=beta_list)
    beta_path = output_dir / "beta_diversity.tsv"
    beta.to_csv(beta_path, sep="\t")
    click.echo(f"  Beta diversity -> {beta_path}")

    # PCoA ordination
    from magi.analysis.diversity import compute_pcoa, compute_nmds
    pcoa = compute_pcoa(matrix)
    pcoa_path = output_dir / "pcoa_ordination.tsv"
    pcoa.to_csv(pcoa_path, sep="\t")
    click.echo(f"  PCoA ordination -> {pcoa_path}")

    # NMDS ordination
    nmds = compute_nmds(matrix)
    nmds_path = output_dir / "nmds_ordination.tsv"
    nmds.to_csv(nmds_path, sep="\t")
    click.echo(f"  NMDS ordination -> {nmds_path}")

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
              help="Path to input filtered reads (FASTQ).")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write assembled contigs (FASTA).")
@click.option("--tool", type=click.Choice(["metaflye", "hifiasm-meta"]),
              default="metaflye", help="Assembly tool to use.")
@click.option("--platform", type=click.Choice(["hifi", "nanopore"]),
              default="hifi", help="Sequencing platform.")
@click.option("--threads", type=int, default=8,
              help="Number of threads for assembly.")
def assemble(input_path, output_path, tool, platform, threads):
    """Assemble metagenomic reads into contigs."""
    from magi.assembly.assemblers import run_assembly

    click.echo(f"Assembling {input_path} with {tool} (threads={threads})")
    run_assembly(
        input_path=Path(input_path),
        output_path=Path(output_path),
        tool=tool,
        threads=threads,
        platform=platform,
    )
    click.echo(f"Assembly complete. Contigs written to {output_path}")


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to unified abundance matrix (TSV).")
@click.option("--metadata", "metadata_path", required=True, type=click.Path(exists=True),
              help="Path to sample metadata (TSV).")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write correlation results (JSON).")
@click.option("--group-col", type=str, default=None,
              help="Metadata column for group-based analysis.")
@click.option("--no-random-forest", is_flag=True, default=False,
              help="Skip random forest feature importance analysis.")
def metadata(input_path, metadata_path, output_path, group_col, no_random_forest):
    """Run metadata-microbiome correlation analysis."""
    import json

    import pandas as pd

    from magi.metadata.correlation import run_correlation

    matrix = pd.read_csv(input_path, sep="\t", index_col=0)
    meta_df = pd.read_csv(metadata_path, sep="\t", index_col=0)

    click.echo(f"Running metadata correlation ({matrix.shape[0]} samples x {matrix.shape[1]} features)")

    results = run_correlation(
        matrix, meta_df,
        random_forest=not no_random_forest,
        group_col=group_col,
    )

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    click.echo(f"Correlation results written to {output_path}")


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




@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="Path to observed abundance TSV (taxa as rows, abundance column).")
@click.option("--mock", type=click.Choice(["zymo_d6300", "zymo_d6331"]),
              required=True, help="Mock community standard to compare against.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Path to write benchmark results TSV.")
def benchmark(input_path, mock, output_path):
    """Benchmark classification results against a known mock community."""
    import pandas as pd

    from magi.benchmarking.metrics import compute_benchmark_metrics
    from magi.benchmarking.mock_communities import MOCK_COMMUNITIES

    observed = pd.read_csv(input_path, sep="\t", index_col=0)
    if "Abundance" in observed.columns:
        obs_series = observed["Abundance"]
    else:
        obs_series = observed.iloc[:, 0]

    community = MOCK_COMMUNITIES[mock]
    metrics = compute_benchmark_metrics(obs_series, community["expected"], name=mock)

    result = pd.DataFrame([metrics]).set_index("name")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, sep="\t")

    click.echo(f"Benchmark against {community['name']}:")
    click.echo(f"  Bray-Curtis:  {metrics['bray_curtis']:.4f}")
    click.echo(f"  J-S divergence: {metrics['jensen_shannon']:.4f}")
    click.echo(f"  F1 score:     {metrics['f1_score']:.4f}")
    click.echo(f"  Precision:    {metrics['precision']:.4f}")
    click.echo(f"  Recall:       {metrics['recall']:.4f}")
    click.echo(f"Results written to {output_path}")

@main.command()
@click.option("--config", "config_path", type=click.Path(), default=None,
              help="Path to config file to validate.")
@click.option("--tools-only", is_flag=True, default=False,
              help="Only check tool availability, skip config validation.")
@click.option("--include-optional", is_flag=True, default=False,
              help="Include optional tools in the check.")
def validate(config_path, tools_only, include_optional):
    """Validate configuration and check external tool availability."""
    from magi.validate import check_tools, validate_config

    all_ok = True

    # Check tools
    click.echo("Checking external tools...")
    tool_results = check_tools(include_optional=include_optional)
    for t in tool_results:
        marker = "OK" if t["status"] == "found" else ("MISSING" if t["required"] else "OPTIONAL")
        symbol = "+" if t["status"] == "found" else "-"
        click.echo(f"  [{symbol}] {t['tool']}: {marker}" + (f" ({t['path']})" if t["path"] else ""))
        if t["status"] == "missing" and t["required"]:
            all_ok = False

    # Check config
    if not tools_only and config_path:
        click.echo(f"\nValidating config: {config_path}")
        errors, warnings = validate_config(config_path)
        for w in warnings:
            click.echo(f"  [!] WARNING: {w}")
        for e in errors:
            click.echo(f"  [x] ERROR: {e}", err=True)
            all_ok = False
        if not errors:
            click.echo("  Config validation passed.")
    elif not tools_only and not config_path:
        click.echo("\nNo config file specified. Use --config to validate a config file.")

    if all_ok:
        click.echo("\nValidation passed.")
    else:
        click.echo("\nValidation failed.", err=True)
        raise SystemExit(1)

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
        kingdoms = list(DB_REGISTRY.keys())
        click.echo(f"Downloading databases for {len(kingdoms)} kingdoms...")
        for i, k in enumerate(kingdoms, 1):
            click.echo(f"  [{i}/{len(kingdoms)}] Downloading {k}...")
            download_database(k, db_path)
            click.echo(f"  [{i}/{len(kingdoms)}] {k} complete.")
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
