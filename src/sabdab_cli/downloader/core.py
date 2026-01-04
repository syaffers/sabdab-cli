"""Core downloading functionality and data structures."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

import httpx
from rich.progress import Progress, TaskID
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from sabdab_cli.utils import ensure_directory


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


async def download_file(
    url: str,
    dest: Path,
    client: httpx.AsyncClient,
    max_retries: int,
    semaphore: asyncio.Semaphore,
    progress: Progress | None = None,
    task_id: TaskID | None = None,
) -> tuple[bool, str | None]:
    """Download a file from a URL to a destination path.

    Args:
        url: Source URL to download from.
        dest: Destination file path.
        client: httpx.AsyncClient instance to use.
        max_retries: Maximum number of retry attempts.
        semaphore: Semaphore to limit concurrent downloads.
        progress: Rich progress instance.
        task_id: Rich progress task ID.

    Returns:
        Tuple of (success: bool, error_message: str | None).
    """
    if dest.exists():
        return True, None

    @retry(
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)
        ),
        stop=stop_after_attempt(max_retries + 1),  # +1 because first attempt + retries
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _fetch():
        async with client.stream("GET", url) as response:
            response.raise_for_status()

            total = int(response.headers.get("Content-Length", 0))
            if progress and task_id:
                progress.update(task_id, total=total, visible=True)

            ensure_directory(dest.parent)
            with temp_dest.open("wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
                    if progress and task_id:
                        progress.advance(task_id, len(chunk))

    temp_dest = dest.with_suffix(dest.suffix + ".tmp")

    try:
        async with semaphore:
            # Download to temporary file for atomic write.
            await _fetch()

            # Atomic write: rename temp file to dest.
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


async def execute_download_task(
    task: DownloadTask,
    client: httpx.AsyncClient,
    max_retries: int,
    stats: DownloadStats,
    progress: Progress,
    overall_progress_task: TaskID,
    semaphore: asyncio.Semaphore,
) -> None:
    """Execute a single download task and update statistics.

    Args:
        task: The download task to execute.
        client: httpx.AsyncClient instance to use.
        max_retries: Maximum number of retry attempts.
        stats: Statistics object to update.
        progress: Rich progress instance.
        overall_progress_task: Overall progress task ID.
        semaphore: Semaphore to limit concurrent downloads.
    """
    existed = task.dest.exists()

    if existed:
        stats.skipped += 1
        progress.advance(overall_progress_task)
        return

    # Add a new progress task for this specific file.
    # It starts as invisible until we know the total size or start downloading.
    task_id = progress.add_task(
        f"[cyan]Downloading {task.dest.name}...",
        total=None,
        visible=False,
    )

    try:
        success, error = await download_file(
            task.url, task.dest, client, max_retries, semaphore, progress, task_id
        )

        if success:
            stats.downloaded += 1
        else:
            stats.failed += 1
            stats.errors.append(f"{task.dest.name}: {error}")
    finally:
        # Remove the individual task from the progress display and advance overall progress.
        progress.remove_task(task_id)
        progress.advance(overall_progress_task)
