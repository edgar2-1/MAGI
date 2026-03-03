from unittest.mock import patch, MagicMock

import pytest

from magi.classify.bacteriome import classify_bacteriome
from magi.classify.mycobiome import classify_mycobiome
from magi.classify.virome import classify_virome


def test_classify_bacteriome_calls_kraken2(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    db = tmp_path / "gtdb_db"
    db.mkdir()
    output_f = tmp_path / "bacteria.tsv"

    with patch("magi.classify.bacteriome.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        classify_bacteriome(input_f, output_f, db, confidence=0.2)

    assert mock_run.call_count >= 1
    first_cmd = mock_run.call_args_list[0][0][0]
    assert "kraken2" in first_cmd
    assert "--confidence" in first_cmd
    assert "0.2" in first_cmd


def test_classify_bacteriome_raises_on_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        classify_bacteriome(
            tmp_path / "missing.fastq",
            tmp_path / "out.tsv",
            tmp_path / "db",
        )


def test_classify_bacteriome_raises_on_missing_db(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    with pytest.raises(FileNotFoundError):
        classify_bacteriome(input_f, tmp_path / "out.tsv", tmp_path / "missing_db")


def test_classify_bacteriome_raises_on_kraken2_failure(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    db = tmp_path / "db"
    db.mkdir()

    with patch("magi.classify.bacteriome.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="db error")
        with pytest.raises(RuntimeError, match="kraken2 failed"):
            classify_bacteriome(input_f, tmp_path / "out.tsv", db)


def test_classify_mycobiome_calls_kraken2(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    db = tmp_path / "unite_db"
    db.mkdir()
    output_f = tmp_path / "fungi.tsv"

    with patch("magi.classify.mycobiome.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        classify_mycobiome(input_f, output_f, db, confidence=0.2)

    first_cmd = mock_run.call_args_list[0][0][0]
    assert "kraken2" in first_cmd


def test_classify_mycobiome_raises_on_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        classify_mycobiome(
            tmp_path / "missing.fastq",
            tmp_path / "out.tsv",
            tmp_path / "db",
        )


def test_classify_virome_calls_genomad(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    db = tmp_path / "genomad_db"
    db.mkdir()
    output_f = tmp_path / "virome.tsv"

    with patch("magi.classify.virome.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        classify_virome(input_f, output_f, db, tool="genomad")

    first_cmd = mock_run.call_args_list[0][0][0]
    assert "genomad" in first_cmd


def test_classify_virome_raises_on_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        classify_virome(
            tmp_path / "missing.fastq",
            tmp_path / "out.tsv",
            tmp_path / "db",
        )


def test_classify_virome_raises_on_invalid_tool(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    db = tmp_path / "db"
    db.mkdir()
    with pytest.raises(ValueError, match="Unknown virome tool"):
        classify_virome(input_f, tmp_path / "out.tsv", db, tool="invalid")
