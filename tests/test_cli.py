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
