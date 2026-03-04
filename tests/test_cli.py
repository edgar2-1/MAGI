from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from magi.cli import main


def test_main_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "MAGI" in result.output


def test_qc_help():
    runner = CliRunner()
    result = runner.invoke(main, ["qc", "--help"])
    assert result.exit_code == 0


def test_classify_help():
    runner = CliRunner()
    result = runner.invoke(main, ["classify", "--help"])
    assert result.exit_code == 0


def test_unifier_help():
    runner = CliRunner()
    result = runner.invoke(main, ["unifier", "--help"])
    assert result.exit_code == 0


def test_db_help():
    runner = CliRunner()
    result = runner.invoke(main, ["db", "--help"])
    assert result.exit_code == 0


def test_run_invokes_snakemake(tmp_path):
    """magi run should invoke snakemake subprocess with config."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("project:\n  name: test\n  output_dir: results/\n")

    runner = CliRunner()
    with patch("magi.cli._subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = runner.invoke(main, ["--config", str(config_file), "run"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "snakemake" in cmd[0]


def test_run_fails_without_config():
    """magi run without --config should fail."""
    runner = CliRunner()
    result = runner.invoke(main, ["run"])
    assert result.exit_code == 1


def test_run_reports_snakemake_failure(tmp_path):
    """magi run reports failure when snakemake exits non-zero."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("project:\n  name: test\n  output_dir: results/\n")

    runner = CliRunner()
    with patch("magi.cli._subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="snakemake error")
        result = runner.invoke(main, ["--config", str(config_file), "run"])
        assert result.exit_code == 1


def test_run_with_profile(tmp_path):
    """magi run with --profile passes it to snakemake."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("project:\n  name: test\n  output_dir: results/\n")
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    (profile_dir / "config.yaml").write_text("executor: slurm\n")

    runner = CliRunner()
    with patch("magi.cli._subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = runner.invoke(main, [
            "--config", str(config_file), "run",
            "--profile", str(profile_dir)
        ])
        assert result.exit_code == 0
        cmd = mock_run.call_args[0][0]
        assert "--profile" in cmd


# ---------------------------------------------------------------------------
# assemble command
# ---------------------------------------------------------------------------


def test_assemble_help():
    runner = CliRunner()
    result = runner.invoke(main, ["assemble", "--help"])
    assert result.exit_code == 0


def test_assemble_command_calls_run_assembly(tmp_path):
    """Test that the assemble command invokes run_assembly correctly."""
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "contigs.fasta"

    runner = CliRunner()
    with patch("magi.assembly.assemblers.run_assembly"):
        result = runner.invoke(main, [
            "assemble",
            "--input", str(input_f),
            "--output", str(output_f),
            "--tool", "metaflye",
            "--threads", "16",
        ])

    assert result.exit_code == 0, result.output
    assert "Assembling" in result.output


def test_assemble_command_default_tool(tmp_path):
    """Test that metaflye is the default assembly tool."""
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "contigs.fasta"

    runner = CliRunner()
    with patch("magi.assembly.assemblers.run_assembly") as mock_asm:
        result = runner.invoke(main, [
            "assemble",
            "--input", str(input_f),
            "--output", str(output_f),
        ])

    assert result.exit_code == 0, result.output
    mock_asm.assert_called_once()
    call_kwargs = mock_asm.call_args
    assert call_kwargs.kwargs["tool"] == "metaflye"


# ---------------------------------------------------------------------------
# metadata command
# ---------------------------------------------------------------------------


def test_metadata_help():
    runner = CliRunner()
    result = runner.invoke(main, ["metadata", "--help"])
    assert result.exit_code == 0


def test_metadata_command_runs_correlation(tmp_path):
    """Test that the metadata command invokes run_correlation."""
    import pandas as pd

    # Create minimal test files
    matrix_f = tmp_path / "abundance.tsv"
    meta_f = tmp_path / "metadata.tsv"
    output_f = tmp_path / "results.json"

    matrix = pd.DataFrame(
        {"taxonA": [1, 2, 3], "taxonB": [4, 5, 6]},
        index=["s1", "s2", "s3"],
    )
    matrix.to_csv(matrix_f, sep="\t")

    meta = pd.DataFrame({"group": ["A", "B", "A"]}, index=["s1", "s2", "s3"])
    meta.to_csv(meta_f, sep="\t")

    runner = CliRunner()
    with patch("magi.metadata.correlation.run_correlation") as mock_corr:
        mock_corr.return_value = {"correlations": "test"}
        result = runner.invoke(main, [
            "metadata",
            "--input", str(matrix_f),
            "--metadata", str(meta_f),
            "--output", str(output_f),
        ])

    assert result.exit_code == 0, result.output
    assert "Correlation results written" in result.output
    mock_corr.assert_called_once()


def test_metadata_command_no_random_forest(tmp_path):
    """Test that --no-random-forest flag is passed through."""
    import pandas as pd

    matrix_f = tmp_path / "abundance.tsv"
    meta_f = tmp_path / "metadata.tsv"
    output_f = tmp_path / "results.json"

    matrix = pd.DataFrame({"taxonA": [1, 2]}, index=["s1", "s2"])
    matrix.to_csv(matrix_f, sep="\t")
    meta = pd.DataFrame({"group": ["A", "B"]}, index=["s1", "s2"])
    meta.to_csv(meta_f, sep="\t")

    runner = CliRunner()
    with patch("magi.metadata.correlation.run_correlation") as mock_corr:
        mock_corr.return_value = {}
        result = runner.invoke(main, [
            "metadata",
            "--input", str(matrix_f),
            "--metadata", str(meta_f),
            "--output", str(output_f),
            "--no-random-forest",
        ])

    assert result.exit_code == 0, result.output
    call_kwargs = mock_corr.call_args
    assert call_kwargs.kwargs.get("random_forest") is False
