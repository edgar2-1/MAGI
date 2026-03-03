import pytest

from magi.qc import filter_reads, trim_adapters, remove_host


def test_filter_reads_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        filter_reads("input.fastq", "output.fastq")


def test_trim_adapters_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        trim_adapters("input.fastq", "output.fastq")


def test_remove_host_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        remove_host("input.fastq", "output.fastq", "host.fna")
