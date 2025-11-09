"""Core downloading functionality and data structures."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


@dataclass(frozen=True)
class DownloadOptions:
    """Configuration options for the download workflow."""

    summary_file: Path
    output_path: Path
    original_pdb: bool
    chothia_pdb: bool
    sequences: bool
    annotation: bool
    abangle: bool
    imgt: bool
    threads: int | None
    retries: int
    timeout: float
    http2: bool
    verbose: bool


@dataclass
class DownloadStats:
    """Track download statistics."""

    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class DownloadTask:
    """Represents a single file download task."""

    url: str
    dest: Path


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory to create.
    """
    path.mkdir(parents=True, exist_ok=True)


def download_file(
    url: str,
    dest: Path,
    client: httpx.Client,
    max_retries: int,
) -> tuple[bool, str | None]:
    """Download a file from a URL to a destination path.

    Args:
        url: Source URL to download from.
        dest: Destination file path.
        client: httpx.Client instance to use.
        max_retries: Maximum number of retry attempts.

    Returns:
        Tuple of (success: bool, error_message: str | None).
    """
    if dest.exists():
        return True, None

    # Create a retry decorator for transient errors.
    @retry(
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)
        ),
        stop=stop_after_attempt(max_retries + 1),  # +1 because first attempt + retries
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _fetch() -> bytes:
        response = client.get(url)
        response.raise_for_status()
        return response.content

    try:
        # Download to temporary file for atomic write.
        temp_dest = dest.with_suffix(dest.suffix + ".tmp")

        content = _fetch()

        # Atomic write: download to temp, then rename.
        ensure_directory(dest.parent)
        temp_dest.write_bytes(content)
        temp_dest.rename(dest)

        return True, None

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return False, "not found (404)"
        else:
            return False, f"HTTP {e.response.status_code}"
    except (httpx.TimeoutException, httpx.NetworkError):
        return False, "network error"
    finally:
        # Clean up temp file if download failed.
        temp_dest = dest.with_suffix(dest.suffix + ".tmp")
        if temp_dest.exists():
            temp_dest.unlink()


def execute_download_task(
    task: DownloadTask,
    client: httpx.Client,
    max_retries: int,
    stats: DownloadStats,
    progress,
    progress_task,
) -> None:
    """Execute a single download task and update statistics.

    Args:
        task: The download task to execute.
        client: httpx.Client instance to use.
        max_retries: Maximum number of retry attempts.
        stats: Statistics object to update.
        progress: Rich progress instance.
        progress_task: Progress task ID.
    """
    progress.update(progress_task, description=f"[cyan]Downloading {task.dest.name}...")

    existed = task.dest.exists()
    success, error = download_file(task.url, task.dest, client, max_retries)

    if existed:
        stats.skipped += 1
    elif success:
        stats.downloaded += 1
    else:
        stats.failed += 1
        stats.errors.append(f"{task.dest.name}: {error}")

    progress.advance(progress_task)


# ========== Async versions ==========


async def download_file_async(
    url: str,
    dest: Path,
    client: httpx.AsyncClient,
    max_retries: int,
    semaphore: asyncio.Semaphore,
) -> tuple[bool, str | None]:
    """Download a file from a URL to a destination path (async version).

    Args:
        url: Source URL to download from.
        dest: Destination file path.
        client: httpx.AsyncClient instance to use.
        max_retries: Maximum number of retry attempts.
        semaphore: Semaphore to limit concurrent downloads.

    Returns:
        Tuple of (success: bool, error_message: str | None).
    """
    if dest.exists():
        return True, None

    # Create a retry decorator for transient errors.
    @retry(
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)
        ),
        stop=stop_after_attempt(max_retries + 1),  # +1 because first attempt + retries
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _fetch() -> bytes:
        response = await client.get(url)
        response.raise_for_status()
        return response.content

    temp_dest = dest.with_suffix(dest.suffix + ".tmp")

    try:
        async with semaphore:
            # Download to temporary file for atomic write.
            content = await _fetch()

            # Atomic write: download to temp, then rename.
            ensure_directory(dest.parent)
            temp_dest.write_bytes(content)
            temp_dest.rename(dest)

        return True, None

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return False, "not found (404)"
        else:
            return False, f"HTTP {e.response.status_code}"
    except (httpx.TimeoutException, httpx.NetworkError):
        return False, "network error"
    finally:
        # Clean up temp file if download failed.
        if temp_dest.exists():
            temp_dest.unlink()


async def execute_download_task_async(
    task: DownloadTask,
    client: httpx.AsyncClient,
    max_retries: int,
    stats: DownloadStats,
    progress,
    progress_task,
    semaphore: asyncio.Semaphore,
) -> None:
    """Execute a single download task and update statistics (async version).

    Args:
        task: The download task to execute.
        client: httpx.AsyncClient instance to use.
        max_retries: Maximum number of retry attempts.
        stats: Statistics object to update.
        progress: Rich progress instance.
        progress_task: Progress task ID.
        semaphore: Semaphore to limit concurrent downloads.
    """
    progress.update(progress_task, description=f"[cyan]Downloading {task.dest.name}...")

    existed = task.dest.exists()
    success, error = await download_file_async(task.url, task.dest, client, max_retries, semaphore)

    if existed:
        stats.skipped += 1
    elif success:
        stats.downloaded += 1
    else:
        stats.failed += 1
        stats.errors.append(f"{task.dest.name}: {error}")

    progress.advance(progress_task)
