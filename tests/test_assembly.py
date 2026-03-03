from unittest.mock import patch, MagicMock

import pytest

from magi.assembly.assemblers import run_assembly


def test_run_assembly_metaflye(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "contigs.fasta"

    with patch("magi.assembly.assemblers.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        run_assembly(input_f, output_f, tool="metaflye")

    cmd = mock_run.call_args[0][0]
    assert "flye" in cmd
    assert "--meta" in cmd
    assert "--pacbio-hifi" in cmd


def test_run_assembly_hifiasm(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "contigs.fasta"

    with patch("magi.assembly.assemblers.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        run_assembly(input_f, output_f, tool="hifiasm-meta")

    cmd = mock_run.call_args[0][0]
    assert "hifiasm_meta" in cmd


def test_run_assembly_raises_on_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_assembly(tmp_path / "missing.fastq", tmp_path / "out.fasta")


def test_run_assembly_raises_on_invalid_tool(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    with pytest.raises(ValueError, match="Unknown assembly tool"):
        run_assembly(input_f, tmp_path / "out.fasta", tool="invalid")


def test_run_assembly_raises_on_failure(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()

    with patch("magi.assembly.assemblers.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="mem error")
        with pytest.raises(RuntimeError, match="metaflye failed"):
            run_assembly(input_f, tmp_path / "out.fasta")
