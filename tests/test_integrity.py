from unittest.mock import patch, MagicMock

import pytest

from magi.db.integrity import compute_checksum, download_with_retry, verify_checksum


def test_compute_checksum(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    result = compute_checksum(f, algorithm="sha256")
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex digest length


def test_compute_checksum_md5(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    result = compute_checksum(f, algorithm="md5")
    assert isinstance(result, str)
    assert len(result) == 32  # MD5 hex digest length


def test_verify_checksum_valid(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    checksum = compute_checksum(f)
    assert verify_checksum(f, checksum) is True


def test_verify_checksum_invalid(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        verify_checksum(f, "0000000000000000000000000000000000000000000000000000000000000000")


def test_download_with_retry_succeeds_first_try():
    mock_fn = MagicMock()
    download_with_retry(mock_fn, max_retries=3, retry_delay=0)
    assert mock_fn.call_count == 1


def test_download_with_retry_succeeds_after_failures():
    mock_fn = MagicMock(side_effect=[OSError("fail"), OSError("fail"), None])
    download_with_retry(mock_fn, max_retries=3, retry_delay=0)
    assert mock_fn.call_count == 3


def test_download_with_retry_exhausts_retries():
    mock_fn = MagicMock(side_effect=OSError("persistent failure"))
    with pytest.raises(RuntimeError, match="failed after 3 attempts"):
        download_with_retry(mock_fn, max_retries=3, retry_delay=0)
    assert mock_fn.call_count == 3


def test_download_with_retry_uses_delay():
    mock_fn = MagicMock(side_effect=[OSError("fail"), None])
    with patch("magi.db.integrity.time.sleep") as mock_sleep:
        download_with_retry(mock_fn, max_retries=3, retry_delay=5)
        mock_sleep.assert_called_once_with(5)
