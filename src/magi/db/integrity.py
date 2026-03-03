"""Download integrity verification for MAGI databases.

Provides retry logic for unreliable network downloads and checksum
verification to ensure downloaded database files are not corrupted.

Integration note
----------------
The ``DB_REGISTRY`` in ``magi.db.manager`` may optionally include a
``sha256`` key for each database entry.  When present, callers should
invoke :func:`verify_checksum` after downloading to confirm file
integrity.  When the value is ``None`` (the default for entries whose
checksums are not yet known), verification is skipped.
"""

import hashlib
import logging
import time
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def download_with_retry(
    download_fn: Callable,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY_SECONDS,
) -> None:
    """Execute a download function with retry logic.

    Args:
        download_fn: Callable that performs the download. Should raise on failure.
        max_retries: Maximum number of attempts.
        retry_delay: Seconds to wait between retries.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            download_fn()
            return
        except (OSError, RuntimeError) as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    "Download attempt %d/%d failed: %s. Retrying in %.0fs...",
                    attempt, max_retries, e, retry_delay,
                )
                time.sleep(retry_delay)
            else:
                logger.error("Download failed after %d attempts: %s", max_retries, e)

    raise RuntimeError(f"Download failed after {max_retries} attempts: {last_error}") from last_error


def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (sha256, md5).

    Returns:
        Hex digest string.
    """
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksum(
    file_path: Path,
    expected: str,
    algorithm: str = "sha256",
) -> bool:
    """Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected: Expected hex digest.
        algorithm: Hash algorithm.

    Returns:
        True if checksum matches.

    Raises:
        ValueError: If checksum doesn't match.
    """
    actual = compute_checksum(file_path, algorithm)
    if actual != expected:
        raise ValueError(
            f"Checksum mismatch for {file_path}: "
            f"expected {expected[:16]}..., got {actual[:16]}..."
        )
    logger.info("Checksum verified for %s (%s)", file_path.name, algorithm)
    return True
