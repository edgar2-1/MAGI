from unittest.mock import patch, MagicMock

import pytest

from magi.qc import trim_adapters, remove_host
from magi.qc.filtering import filter_reads as filter_reads_direct


def test_filter_reads_builds_correct_fastp_command_hifi(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "filtered.fastq"

    with patch("magi.qc.filtering.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        filter_reads_direct(input_f, output_f, min_quality=20, min_length=1000, platform="hifi")

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "fastp" in cmd
    assert "--qualified_quality_phred" in cmd
    assert "20" in cmd
    assert "--length_required" in cmd
    assert "1000" in cmd


def test_filter_reads_includes_max_length_when_set(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "filtered.fastq"

    with patch("magi.qc.filtering.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        filter_reads_direct(input_f, output_f, max_length=50000, platform="hifi")

    cmd = mock_run.call_args[0][0]
    assert "--length_limit" in cmd
    assert "50000" in cmd


def test_filter_reads_raises_on_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        filter_reads_direct(tmp_path / "nonexistent.fastq", tmp_path / "out.fastq")


def test_filter_reads_raises_on_fastp_failure(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "filtered.fastq"

    with patch("magi.qc.filtering.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        with pytest.raises(RuntimeError, match="fastp failed"):
            filter_reads_direct(input_f, output_f, platform="hifi")


def test_trim_adapters_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        trim_adapters("input.fastq", "output.fastq")


def test_remove_host_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        remove_host("input.fastq", "output.fastq", "host.fna")
