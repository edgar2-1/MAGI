from unittest.mock import patch, MagicMock

import pytest

from magi.qc import trim_adapters, remove_host  # noqa: F401
from magi.qc.filtering import filter_reads as filter_reads_direct
from magi.qc.host_removal import remove_host as remove_host_direct
from magi.qc.trimming import trim_adapters as trim_adapters_direct


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


def test_trim_adapters_builds_correct_command(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "trimmed.fastq"

    with patch("magi.qc.trimming.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        trim_adapters_direct(input_f, output_f)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "fastp" in cmd
    assert str(input_f) in cmd
    assert str(output_f) in cmd


def test_trim_adapters_raises_on_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        trim_adapters_direct(tmp_path / "nonexistent.fastq", tmp_path / "out.fastq")


def test_remove_host_calls_minimap2_and_samtools(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    host_ref = tmp_path / "host.fna"
    host_ref.touch()
    output_f = tmp_path / "dehosted.fastq"

    mock_pipe_proc = MagicMock()
    mock_pipe_proc.stdout = MagicMock()
    mock_pipe_proc.returncode = 0
    mock_pipe_proc.communicate.return_value = (b"", b"")

    with (
        patch("magi.qc.host_removal.subprocess.Popen") as mock_popen,
        patch("magi.qc.host_removal.subprocess.run") as mock_run,
    ):
        mock_popen.return_value = mock_pipe_proc
        mock_run.return_value = MagicMock(returncode=0)
        remove_host_direct(input_f, output_f, host_ref)

    # Popen called twice: minimap2 and samtools view (the pipe)
    assert mock_popen.call_count == 2
    minimap2_cmd = mock_popen.call_args_list[0][0][0]
    samtools_view_cmd = mock_popen.call_args_list[1][0][0]
    assert "minimap2" in minimap2_cmd
    assert "samtools" in samtools_view_cmd
    assert "view" in samtools_view_cmd

    # subprocess.run called once for samtools fastq
    mock_run.assert_called_once()
    fastq_cmd = mock_run.call_args[0][0]
    assert "samtools" in fastq_cmd
    assert "fastq" in fastq_cmd


def test_remove_host_raises_on_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        remove_host_direct(tmp_path / "missing.fastq", tmp_path / "out.fastq", tmp_path / "host.fna")


def test_remove_host_raises_on_missing_reference(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    with pytest.raises(FileNotFoundError):
        remove_host_direct(input_f, tmp_path / "out.fastq", tmp_path / "missing_host.fna")


def test_filter_reads_uses_custom_threads(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "filtered.fastq"

    with patch("magi.qc.filtering.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        filter_reads_direct(input_f, output_f, platform="hifi", threads=16)

    cmd = mock_run.call_args[0][0]
    thread_idx = cmd.index("--thread")
    assert cmd[thread_idx + 1] == "16"


def test_trim_adapters_uses_custom_threads(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    output_f = tmp_path / "trimmed.fastq"

    with patch("magi.qc.trimming.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        trim_adapters_direct(input_f, output_f, threads=8)

    cmd = mock_run.call_args[0][0]
    thread_idx = cmd.index("--thread")
    assert cmd[thread_idx + 1] == "8"


def test_remove_host_uses_custom_threads(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    host_ref = tmp_path / "host.fna"
    host_ref.touch()
    output_f = tmp_path / "dehosted.fastq"

    mock_pipe_proc = MagicMock()
    mock_pipe_proc.stdout = MagicMock()
    mock_pipe_proc.returncode = 0
    mock_pipe_proc.communicate.return_value = (b"", b"")

    with (
        patch("magi.qc.host_removal.subprocess.Popen") as mock_popen,
        patch("magi.qc.host_removal.subprocess.run") as mock_run,
    ):
        mock_popen.return_value = mock_pipe_proc
        mock_run.return_value = MagicMock(returncode=0)
        remove_host_direct(input_f, output_f, host_ref, threads=12)

    minimap2_cmd = mock_popen.call_args_list[0][0][0]
    thread_idx = minimap2_cmd.index("-t")
    assert minimap2_cmd[thread_idx + 1] == "12"


def test_remove_host_uses_nanopore_preset(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    host_ref = tmp_path / "host.fna"
    host_ref.touch()
    output_f = tmp_path / "dehosted.fastq"

    mock_pipe_proc = MagicMock()
    mock_pipe_proc.stdout = MagicMock()
    mock_pipe_proc.returncode = 0
    mock_pipe_proc.communicate.return_value = (b"", b"")

    with (
        patch("magi.qc.host_removal.subprocess.Popen") as mock_popen,
        patch("magi.qc.host_removal.subprocess.run") as mock_run,
    ):
        mock_popen.return_value = mock_pipe_proc
        mock_run.return_value = MagicMock(returncode=0)
        remove_host_direct(input_f, output_f, host_ref, platform="nanopore")

    minimap2_cmd = mock_popen.call_args_list[0][0][0]
    assert "map-ont" in minimap2_cmd


def test_remove_host_uses_hifi_preset_by_default(tmp_path):
    input_f = tmp_path / "reads.fastq"
    input_f.touch()
    host_ref = tmp_path / "host.fna"
    host_ref.touch()
    output_f = tmp_path / "dehosted.fastq"

    mock_pipe_proc = MagicMock()
    mock_pipe_proc.stdout = MagicMock()
    mock_pipe_proc.returncode = 0
    mock_pipe_proc.communicate.return_value = (b"", b"")

    with (
        patch("magi.qc.host_removal.subprocess.Popen") as mock_popen,
        patch("magi.qc.host_removal.subprocess.run") as mock_run,
    ):
        mock_popen.return_value = mock_pipe_proc
        mock_run.return_value = MagicMock(returncode=0)
        remove_host_direct(input_f, output_f, host_ref)

    minimap2_cmd = mock_popen.call_args_list[0][0][0]
    assert "map-hifi" in minimap2_cmd
