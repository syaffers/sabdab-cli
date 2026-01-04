"""Tests for async download functionality."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from sabdab_cli.downloader.core import (
    DownloadOptions,
    DownloadStats,
    DownloadTask,
    download_file,
    execute_download_task,
)
from sabdab_cli.downloader.runner import _get_concurrency_limit, run_download


class TestGetConcurrencyLimit:
    """Test concurrency limit calculation."""

    def test_returns_user_specified_threads(self):
        """Should return user-specified thread count."""
        assert _get_concurrency_limit(5) == 5
        assert _get_concurrency_limit(1) == 1
        assert _get_concurrency_limit(50) == 50

    def test_auto_detect_returns_reasonable_limit(self):
        """Should auto-detect and return reasonable concurrency limit."""
        limit = _get_concurrency_limit(None)
        assert isinstance(limit, int)
        # Assuming os.cpu_count() returns something, or defaults to 4
        # limit should be min(cpu*2, 20)
        assert 1 <= limit <= 20


class TestDownloadFile:
    """Test async file download functionality."""

    @pytest.mark.asyncio
    async def test_downloads_file_successfully(self, tmp_path: Path):
        """Should download a file successfully."""
        url = "https://example.com/test.txt"
        dest = tmp_path / "test.txt"
        content = b"test content"

        # Mock async client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = content
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        semaphore = asyncio.Semaphore(5)

        success, error = await download_file(
            url, dest, mock_client, max_retries=3, semaphore=semaphore
        )

        assert success is True
        assert error is None
        assert dest.exists()
        assert dest.read_bytes() == content

    @pytest.mark.asyncio
    async def test_skips_existing_file(self, tmp_path: Path):
        """Should skip downloading if file already exists."""
        url = "https://example.com/test.txt"
        dest = tmp_path / "test.txt"
        dest.write_text("existing content")

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        semaphore = asyncio.Semaphore(5)

        success, error = await download_file(
            url, dest, mock_client, max_retries=3, semaphore=semaphore
        )

        assert success is True
        assert error is None
        # Should not have called the client
        mock_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_404_gracefully(self, tmp_path: Path):
        """Should handle 404 errors gracefully."""
        url = "https://example.com/nonexistent.txt"
        dest = tmp_path / "test.txt"

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)
        )

        semaphore = asyncio.Semaphore(5)

        success, error = await download_file(
            url, dest, mock_client, max_retries=3, semaphore=semaphore
        )

        assert success is False
        assert error == "not found (404)"
        assert not dest.exists()

    @pytest.mark.asyncio
    async def test_cleans_up_temp_file_on_failure(self, tmp_path: Path):
        """Should clean up temporary file if download fails."""
        url = "https://example.com/test.txt"
        dest = tmp_path / "test.txt"
        temp_dest = dest.with_suffix(dest.suffix + ".tmp")

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.NetworkError("Connection failed"))

        semaphore = asyncio.Semaphore(5)

        success, error = await download_file(
            url, dest, mock_client, max_retries=0, semaphore=semaphore
        )

        assert success is False
        assert error == "network error"
        assert not dest.exists()
        assert not temp_dest.exists()


class TestExecuteDownloadTask:
    """Test async download task execution."""

    @pytest.mark.asyncio
    async def test_successful_download_updates_stats(self, tmp_path: Path):
        """Should update stats correctly for successful download."""
        url = "https://example.com/test.txt"
        dest = tmp_path / "test.txt"
        content = b"test content"

        # Mock async client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = content
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_response)

        # Mock progress
        mock_progress = Mock()
        mock_progress.update = Mock()
        mock_progress.advance = Mock()

        task = DownloadTask(url=url, dest=dest)
        stats = DownloadStats()
        semaphore = asyncio.Semaphore(5)

        await execute_download_task(
            task,
            mock_client,
            max_retries=3,
            stats=stats,
            progress=mock_progress,
            progress_task=1,
            semaphore=semaphore,
        )

        assert stats.downloaded == 1
        assert stats.skipped == 0
        assert stats.failed == 0
        assert len(stats.errors) == 0

    @pytest.mark.asyncio
    async def test_existing_file_updates_stats(self, tmp_path: Path):
        """Should update stats correctly when file already exists."""
        url = "https://example.com/test.txt"
        dest = tmp_path / "test.txt"
        dest.write_text("existing content")

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_progress = Mock()
        mock_progress.update = Mock()
        mock_progress.advance = Mock()

        task = DownloadTask(url=url, dest=dest)
        stats = DownloadStats()
        semaphore = asyncio.Semaphore(5)

        await execute_download_task(
            task,
            mock_client,
            max_retries=3,
            stats=stats,
            progress=mock_progress,
            progress_task=1,
            semaphore=semaphore,
        )

        assert stats.downloaded == 0
        assert stats.skipped == 1
        assert stats.failed == 0
        assert len(stats.errors) == 0

    @pytest.mark.asyncio
    async def test_failed_download_updates_stats(self, tmp_path: Path):
        """Should update stats correctly when download fails."""
        url = "https://example.com/test.txt"
        dest = tmp_path / "test.txt"

        mock_response = Mock()
        mock_response.status_code = 404

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)
        )

        mock_progress = Mock()
        mock_progress.update = Mock()
        mock_progress.advance = Mock()

        task = DownloadTask(url=url, dest=dest)
        stats = DownloadStats()
        semaphore = asyncio.Semaphore(5)

        await execute_download_task(
            task,
            mock_client,
            max_retries=0,
            stats=stats,
            progress=mock_progress,
            progress_task=1,
            semaphore=semaphore,
        )

        assert stats.downloaded == 0
        assert stats.skipped == 0
        assert stats.failed == 1
        assert len(stats.errors) == 1
        assert "not found (404)" in stats.errors[0]


class TestRunDownload:
    """Test async download runner."""

    @pytest.mark.asyncio
    async def test_creates_output_directory(self, tmp_path: Path):
        """Should create output directory if it doesn't exist."""
        summary_file = tmp_path / "summary.tsv"
        summary_file.write_text("pdb\tHchain\tLchain\tmodel\n1a2b\tH\tL\t0\n")
        output_path = tmp_path / "nonexistent_output"

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=True,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=2,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        # This will fail on actual downloads but should create directory
        await run_download(options)

        assert output_path.exists()
        assert output_path.is_dir()

    @pytest.mark.asyncio
    async def test_empty_summary_file(self, tmp_path: Path):
        """Should handle empty summary file gracefully."""
        summary_file = tmp_path / "empty.tsv"
        summary_file.write_text("pdb\tHchain\tLchain\tmodel\n")

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=tmp_path / "output",
            original_pdb=True,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=2,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        exit_code = await run_download(options)
        # Empty summary file is treated as an error
        assert exit_code == 1


class TestConcurrency:
    """Test that concurrency is properly limited."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self, tmp_path: Path):
        """Should respect semaphore limit for concurrent downloads."""
        concurrency_limit = 3
        semaphore = asyncio.Semaphore(concurrency_limit)

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0

        async def mock_download_with_tracking():
            nonlocal concurrent_count, max_concurrent
            async with semaphore:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)
                await asyncio.sleep(0.01)  # Simulate some work
                concurrent_count -= 1

        # Create more tasks than the semaphore limit
        tasks = [mock_download_with_tracking() for _ in range(10)]
        await asyncio.gather(*tasks)

        # Should not exceed the concurrency limit
        assert max_concurrent <= concurrency_limit
