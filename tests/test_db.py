import json
from unittest.mock import patch, MagicMock

import pytest

from magi.db.manager import download_database, get_db_status, DB_REGISTRY


def test_db_registry_has_all_kingdoms():
    assert "bacteria" in DB_REGISTRY
    assert "fungi" in DB_REGISTRY
    assert "virus" in DB_REGISTRY


def test_download_database_creates_directory(tmp_path):
    db_dir = tmp_path / "dbs"
    with patch("magi.db.manager.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        download_database("bacteria", db_dir)
    assert (db_dir / "bacteria").is_dir()


def test_download_database_writes_manifest(tmp_path):
    db_dir = tmp_path / "dbs"
    with patch("magi.db.manager.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        download_database("bacteria", db_dir)
    manifest = db_dir / "bacteria" / "manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert data["kingdom"] == "bacteria"
    assert "downloaded_at" in data


def test_download_database_invalid_kingdom(tmp_path):
    with pytest.raises(ValueError, match="Unknown kingdom"):
        download_database("archaea", tmp_path)


def test_download_database_raises_on_failure(tmp_path):
    with patch("magi.db.manager.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="download error")
        with pytest.raises(RuntimeError, match="download error"):
            download_database("bacteria", tmp_path)


def test_get_db_status_no_dbs(tmp_path):
    status = get_db_status(tmp_path)
    assert status["bacteria"]["installed"] is False
    assert status["fungi"]["installed"] is False
    assert status["virus"]["installed"] is False


def test_get_db_status_with_installed_db(tmp_path):
    db_dir = tmp_path / "bacteria"
    db_dir.mkdir()
    manifest = db_dir / "manifest.json"
    manifest.write_text(json.dumps({
        "kingdom": "bacteria",
        "downloaded_at": "2026-03-03T00:00:00",
        "source": "test",
    }))
    status = get_db_status(tmp_path)
    assert status["bacteria"]["installed"] is True
    assert status["bacteria"]["downloaded_at"] == "2026-03-03T00:00:00"
