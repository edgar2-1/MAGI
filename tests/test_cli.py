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
