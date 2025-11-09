"""Tests for downloader module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from sabdab_cli.downloader import DownloadOptions, _download_file, _ensure_directory, run_download


@pytest.mark.unit
class TestEnsureDirectory:
    """Test _ensure_directory helper."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        """Test that directory is created."""
        target = tmp_path / "new_dir" / "nested"
        assert not target.exists()

        _ensure_directory(target)

        assert target.exists()
        assert target.is_dir()

    def test_idempotent(self, tmp_path: Path) -> None:
        """Test that calling twice is safe."""
        target = tmp_path / "dir"
        target.mkdir()

        _ensure_directory(target)
        _ensure_directory(target)

        assert target.exists()


@pytest.mark.unit
class TestDownloadFile:
    """Test _download_file function."""

    def test_downloads_file_successfully(self, tmp_path: Path) -> None:
        """Test successful file download."""
        dest = tmp_path / "test.pdb"
        url = "https://example.com/test.pdb"
        content = b"mock pdb content"

        # Mock httpx client
        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.content = content
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        _download_file(url, dest, mock_client, max_retries=3)

        assert dest.exists()
        assert dest.read_bytes() == content
        mock_client.get.assert_called_once_with(url)

    def test_skips_existing_file(self, tmp_path: Path) -> None:
        """Test that existing files are skipped."""
        dest = tmp_path / "existing.pdb"
        dest.write_text("existing content")
        url = "https://example.com/test.pdb"

        mock_client = MagicMock(spec=httpx.Client)

        _download_file(url, dest, mock_client, max_retries=3)

        # Client should not be called for existing files
        mock_client.get.assert_not_called()
        assert dest.read_text() == "existing content"

    def test_handles_404_gracefully(self, tmp_path: Path) -> None:
        """Test that 404 errors are handled without raising."""
        dest = tmp_path / "missing.pdb"
        url = "https://example.com/missing.pdb"

        mock_client = MagicMock(spec=httpx.Client)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        mock_client.get.return_value = mock_response

        # Should not raise, but file should not exist
        _download_file(url, dest, mock_client, max_retries=0)

        assert not dest.exists()


@pytest.mark.unit
class TestRunDownload:
    """Test run_download function."""

    def test_run_download_missing_summary_file(self, tmp_path: Path) -> None:
        """Test error handling when summary file is missing."""
        summary_file = tmp_path / "nonexistent.tsv"
        output_path = tmp_path / "output"

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=True,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=None,
            retries=3,
            timeout=30.0,
            http2=True,
        )

        exit_code = run_download(options)

        assert exit_code == 1
