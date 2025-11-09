"""Tests for downloader.core module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock

import httpx
import pytest

from sabdab_cli.downloader.core import (
    DownloadOptions,
    DownloadStats,
    DownloadTask,
    download_file,
    ensure_directory,
    execute_download_task,
)
from conftest import DUMMY_BASE_URL


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Create a mock httpx.Client."""
    return MagicMock(spec=httpx.Client)


@pytest.fixture
def mock_progress() -> tuple[Mock, Mock]:
    """Create mock progress objects."""
    progress = Mock()
    progress_task = Mock()
    return progress, progress_task


@pytest.fixture
def download_stats() -> DownloadStats:
    """Create a fresh DownloadStats instance."""
    return DownloadStats()


@pytest.fixture
def mock_success_response() -> MagicMock:
    """Create a mock successful HTTP response."""
    mock_response = MagicMock()
    mock_response.content = b"mock pdb content"
    mock_response.raise_for_status = MagicMock()
    return mock_response


def create_mock_error_response(status_code: int, message: str) -> MagicMock:
    """Helper to create mock error responses."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message, request=MagicMock(), response=mock_response
    )
    return mock_response


@pytest.mark.unit
class TestDownloadOptions:
    """Test DownloadOptions dataclass."""

    def test_create_options(self, tmp_path: Path) -> None:
        """Test creating download options."""
        summary_file = tmp_path / "summary.tsv"
        output_path = tmp_path / "output"

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=True,
            chothia_pdb=False,
            sequences=True,
            annotation=False,
            abangle=False,
            imgt=True,
            threads=4,
            retries=3,
            timeout=30.0,
            http2=True,
            verbose=False,
        )

        assert options.summary_file == summary_file
        assert options.output_path == output_path
        assert options.original_pdb is True
        assert options.chothia_pdb is False
        assert options.sequences is True
        assert options.threads == 4

    def test_options_frozen(self, tmp_path: Path) -> None:
        """Test that DownloadOptions is frozen."""
        options = DownloadOptions(
            summary_file=tmp_path / "summary.tsv",
            output_path=tmp_path / "output",
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
            verbose=False,
        )

        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.11+
            options.original_pdb = False


@pytest.mark.unit
class TestDownloadStats:
    """Test DownloadStats dataclass."""

    def test_create_stats(self) -> None:
        """Test creating download stats."""
        stats = DownloadStats()

        assert stats.downloaded == 0
        assert stats.skipped == 0
        assert stats.failed == 0
        assert stats.errors == []

    def test_stats_with_values(self) -> None:
        """Test creating stats with initial values."""
        stats = DownloadStats(downloaded=5, skipped=2, failed=1, errors=["error1"])

        assert stats.downloaded == 5
        assert stats.skipped == 2
        assert stats.failed == 1
        assert stats.errors == ["error1"]

    def test_update_stats(self) -> None:
        """Test updating stats."""
        stats = DownloadStats()

        stats.downloaded += 1
        stats.skipped += 2
        stats.failed += 1
        stats.errors.append("test error")

        assert stats.downloaded == 1
        assert stats.skipped == 2
        assert stats.failed == 1
        assert len(stats.errors) == 1


@pytest.mark.unit
class TestEnsureDirectory:
    """Test ensure_directory function."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        """Test that directory is created."""
        target = tmp_path / "new_dir" / "nested"
        assert not target.exists()

        ensure_directory(target)

        assert target.exists()
        assert target.is_dir()

    def test_idempotent(self, tmp_path: Path) -> None:
        """Test that calling twice is safe."""
        target = tmp_path / "dir"
        target.mkdir()

        ensure_directory(target)
        ensure_directory(target)

        assert target.exists()

    def test_creates_nested_structure(self, tmp_path: Path) -> None:
        """Test creating deeply nested directories."""
        target = tmp_path / "a" / "b" / "c" / "d"
        ensure_directory(target)

        assert target.exists()
        assert target.is_dir()


@pytest.mark.unit
class TestDownloadFile:
    """Test download_file function."""

    def test_downloads_file_successfully(
        self, tmp_path: Path, mock_http_client: MagicMock, mock_success_response: MagicMock
    ) -> None:
        """Test successful file download."""
        dest = tmp_path / "test.pdb"
        url = f"{DUMMY_BASE_URL}/test.pdb"

        mock_http_client.get.return_value = mock_success_response

        success, error = download_file(url, dest, mock_http_client, max_retries=3)

        assert success is True
        assert error is None
        assert dest.exists()
        assert dest.read_bytes() == mock_success_response.content
        mock_http_client.get.assert_called_once_with(url)

    def test_skips_existing_file(self, tmp_path: Path, mock_http_client: MagicMock) -> None:
        """Test that existing files are skipped."""
        dest = tmp_path / "existing.pdb"
        dest.write_text("existing content")
        url = f"{DUMMY_BASE_URL}/test.pdb"

        success, error = download_file(url, dest, mock_http_client, max_retries=3)

        # Client should not be called for existing files
        assert success is True
        assert error is None
        mock_http_client.get.assert_not_called()
        assert dest.read_text() == "existing content"

    def test_handles_404_gracefully(self, tmp_path: Path, mock_http_client: MagicMock) -> None:
        """Test that 404 errors are handled without raising."""
        dest = tmp_path / "missing.pdb"
        url = f"{DUMMY_BASE_URL}/missing.pdb"

        mock_http_client.get.return_value = create_mock_error_response(404, "Not Found")

        success, error = download_file(url, dest, mock_http_client, max_retries=0)

        assert success is False
        assert error == "not found (404)"
        assert not dest.exists()

    def test_handles_500_error(self, tmp_path: Path, mock_http_client: MagicMock) -> None:
        """Test that 500 errors are handled."""
        dest = tmp_path / "error.pdb"
        url = f"{DUMMY_BASE_URL}/error.pdb"

        mock_http_client.get.return_value = create_mock_error_response(500, "Server Error")

        success, error = download_file(url, dest, mock_http_client, max_retries=0)

        assert success is False
        assert error == "HTTP 500"
        assert not dest.exists()

    def test_handles_network_error(self, tmp_path: Path, mock_http_client: MagicMock) -> None:
        """Test that network errors are handled."""
        dest = tmp_path / "network.pdb"
        url = f"{DUMMY_BASE_URL}/network.pdb"

        mock_http_client.get.side_effect = httpx.NetworkError("Connection failed")

        success, error = download_file(url, dest, mock_http_client, max_retries=0)

        assert success is False
        assert error == "network error"
        assert not dest.exists()

    def test_cleans_up_temp_file_on_failure(
        self, tmp_path: Path, mock_http_client: MagicMock
    ) -> None:
        """Test that temporary files are cleaned up on failure."""
        dest = tmp_path / "cleanup.pdb"
        url = f"{DUMMY_BASE_URL}/cleanup.pdb"

        mock_http_client.get.side_effect = httpx.NetworkError("Connection failed")

        download_file(url, dest, mock_http_client, max_retries=0)

        # Temp file should not exist
        temp_file = dest.with_suffix(dest.suffix + ".tmp")
        assert not temp_file.exists()


@pytest.mark.unit
class TestExecuteDownloadTask:
    """Test execute_download_task function."""

    def test_successful_download_updates_stats(
        self,
        tmp_path: Path,
        mock_http_client: MagicMock,
        mock_success_response: MagicMock,
        download_stats: DownloadStats,
        mock_progress: tuple[Mock, Mock],
    ) -> None:
        """Test that successful download updates stats correctly."""
        task = DownloadTask(
            url=f"{DUMMY_BASE_URL}/test.pdb",
            dest=tmp_path / "test.pdb",
        )

        mock_http_client.get.return_value = mock_success_response
        progress, progress_task = mock_progress

        execute_download_task(task, mock_http_client, 3, download_stats, progress, progress_task)

        assert download_stats.downloaded == 1
        assert download_stats.skipped == 0
        assert download_stats.failed == 0
        assert len(download_stats.errors) == 0

    def test_existing_file_updates_stats(
        self,
        tmp_path: Path,
        mock_http_client: MagicMock,
        download_stats: DownloadStats,
        mock_progress: tuple[Mock, Mock],
    ) -> None:
        """Test that existing file updates stats correctly."""
        dest = tmp_path / "existing.pdb"
        dest.write_text("existing")

        task = DownloadTask(url=f"{DUMMY_BASE_URL}/test.pdb", dest=dest)
        progress, progress_task = mock_progress

        execute_download_task(task, mock_http_client, 3, download_stats, progress, progress_task)

        assert download_stats.downloaded == 0
        assert download_stats.skipped == 1
        assert download_stats.failed == 0

    def test_failed_download_updates_stats(
        self,
        tmp_path: Path,
        mock_http_client: MagicMock,
        download_stats: DownloadStats,
        mock_progress: tuple[Mock, Mock],
    ) -> None:
        """Test that failed download updates stats correctly."""
        task = DownloadTask(
            url=f"{DUMMY_BASE_URL}/missing.pdb",
            dest=tmp_path / "missing.pdb",
        )

        mock_http_client.get.return_value = create_mock_error_response(404, "Not Found")
        progress, progress_task = mock_progress

        execute_download_task(task, mock_http_client, 0, download_stats, progress, progress_task)

        assert download_stats.downloaded == 0
        assert download_stats.skipped == 0
        assert download_stats.failed == 1
        assert len(download_stats.errors) == 1
        assert "missing.pdb" in download_stats.errors[0]
