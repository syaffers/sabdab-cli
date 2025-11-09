from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from sabdab_cli.summary import SummaryParseError, parse_summary_file
from sabdab_cli.urls import build_chothia_pdb_url, build_original_pdb_url

console = Console()


@dataclass(frozen=True)
class DownloadOptions:
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


def _ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def _download_file(
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
        _ensure_directory(dest.parent)
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


def run_download(options: DownloadOptions) -> int:
    """Run the download workflow.

    Args:
        options: Download configuration options.

    Returns:
        Shell exit code (0 = success, non-zero = failure).

    Raises:
        SummaryParseError: If the summary file is invalid.
        FileNotFoundError: If the summary file is not found.
        Exception: If an unexpected error occurs.
    """
    try:
        # Parse summary file.
        console.print(f"[bold]Reading summary file:[/bold] {options.summary_file}")
        entries = parse_summary_file(options.summary_file)
        console.print(f"Found {len(entries)} entries\n")

        # Create output directory.
        _ensure_directory(options.output_path)

        # Setup httpx client with timeout and HTTP/2.
        client = httpx.Client(
            timeout=httpx.Timeout(options.timeout),
            http2=options.http2,
            follow_redirects=True,
        )

        # Count total files to download
        total_files = len(entries) * sum(
            [
                options.original_pdb,
                options.chothia_pdb,
                options.sequences,
                options.annotation,
                options.abangle,
                options.imgt,
            ]
        )

        downloaded = 0
        skipped = 0
        failed = 0
        errors = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Downloading...", total=total_files)

            with client:
                for entry in entries:
                    if options.original_pdb:
                        url = build_original_pdb_url(entry)
                        dest = options.output_path / "original" / f"{entry.pdb}.pdb"
                        progress.update(task, description=f"[cyan]Downloading {dest.name}...")

                        existed = dest.exists()
                        success, error = _download_file(url, dest, client, options.retries)

                        if existed:
                            skipped += 1
                        elif success:
                            downloaded += 1
                        else:
                            failed += 1
                            errors.append(f"{dest.name}: {error}")

                        progress.advance(task)

                    if options.chothia_pdb:
                        url = build_chothia_pdb_url(entry)
                        dest = options.output_path / "chothia" / f"{entry.pdb}.pdb"
                        progress.update(task, description=f"[cyan]Downloading {dest.name}...")

                        existed = dest.exists()
                        success, error = _download_file(url, dest, client, options.retries)

                        if existed:
                            skipped += 1
                        elif success:
                            downloaded += 1
                        else:
                            failed += 1
                            errors.append(f"{dest.name}: {error}")

                        progress.advance(task)

        # Print summary
        console.print(f"\nDownloaded: {downloaded}")
        if skipped > 0:
            console.print(f"Skipped (already exists): {skipped}")
        if failed > 0:
            console.print(f"Failed: {failed}")
            for error in errors[:10]:  # Show first 10 errors
                console.print(f"  [red]-[/red] {error}")
            if len(errors) > 10:
                console.print(f"  [dim]... and {len(errors) - 10} more[/dim]")

        console.print()

    except SummaryParseError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1
    except Exception as e:
        if options.verbose:
            console.print_exception(show_locals=True)
        else:
            console.print(f"[bold red]Unexpected error:[/bold red] {e} Use -v for more details.")
        return 1

    return 0
