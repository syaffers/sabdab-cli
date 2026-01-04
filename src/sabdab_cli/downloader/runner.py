"""Main download workflow orchestration."""

from __future__ import annotations

import asyncio

import httpx
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TransferSpeedColumn,
)
from rich.text import Text

from sabdab_cli.downloader.core import (
    DownloadOptions,
    DownloadStats,
    execute_download_task,
)
from sabdab_cli.downloader.tasks import (
    count_total_files,
    generate_abangle_task,
    generate_annotation_tasks,
    generate_imgt_tasks,
    generate_pdb_tasks,
    generate_sequence_tasks,
)
from sabdab_cli.summary import SummaryParseError, group_entries_by_pdb, parse_summary_file
from sabdab_cli.urls import SAbDabUrlBuilder
from sabdab_cli.utils import ensure_directory, get_concurrency_limit

console = Console()


class SmartDownloadColumn(DownloadColumn):
    """Download column that shows file count for overall task."""

    def render(self, task):
        if task.fields.get("is_overall"):
            return Text(
                f"({int(task.completed)}/{int(task.total)} files)", style="progress.download"
            )
        return Text(" ") + super().render(task)


class SmartTransferSpeedColumn(TransferSpeedColumn):
    """Transfer speed column that is hidden for overall task."""

    def render(self, task):
        if task.fields.get("is_overall"):
            return Text("")
        return Text(" • ") + super().render(task)


async def run_download(options: DownloadOptions) -> int:
    """Run the download workflow with async concurrency.

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

        # Group entries by PDB for efficient downloading.
        grouped_by_pdb = group_entries_by_pdb(entries)

        # Create output directory.
        ensure_directory(options.output_path)

        # Determine concurrency limit
        concurrency_limit = get_concurrency_limit(options.threads)
        semaphore = asyncio.Semaphore(concurrency_limit)

        console.print(f"[dim]Using {concurrency_limit} concurrent downloads[/dim]\n")

        # Setup httpx async client with timeout and HTTP/2.
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(options.timeout),
            http2=options.http2,
            follow_redirects=True,
        ) as client:
            # Create URL builder.
            builder = SAbDabUrlBuilder()

            # Count total files to download
            total_files = count_total_files(entries, grouped_by_pdb, options)

            # Track download statistics
            stats = DownloadStats()

            # Track which PDBs we've already downloaded to avoid duplicates.
            downloaded_pdbs: set[str] = set()
            downloaded_abangles: set[str] = set()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}", justify="left"),
                BarColumn(bar_width=None),
                TaskProgressColumn(),
                SmartDownloadColumn(),
                SmartTransferSpeedColumn(),
                console=console,
            ) as progress:
                overall_task = progress.add_task(
                    "[bold cyan]Total Progress", total=total_files, is_overall=True
                )

                # Collect all download tasks
                all_tasks = []

                for entry in entries:
                    # Generate PDB download tasks
                    pdb_tasks = generate_pdb_tasks(
                        entry, builder, options.output_path, options, downloaded_pdbs
                    )
                    for task in pdb_tasks:
                        all_tasks.append(
                            execute_download_task(
                                task,
                                client,
                                options.retries,
                                stats,
                                progress,
                                overall_task,
                                semaphore,
                            )
                        )
                    if pdb_tasks:
                        downloaded_pdbs.add(entry.pdb)

                    # Generate sequence download tasks
                    if options.sequences:
                        for task in generate_sequence_tasks(entry, builder, options.output_path):
                            all_tasks.append(
                                execute_download_task(
                                    task,
                                    client,
                                    options.retries,
                                    stats,
                                    progress,
                                    overall_task,
                                    semaphore,
                                )
                            )

                    # Generate annotation download tasks
                    if options.annotation:
                        for task in generate_annotation_tasks(entry, builder, options.output_path):
                            all_tasks.append(
                                execute_download_task(
                                    task,
                                    client,
                                    options.retries,
                                    stats,
                                    progress,
                                    overall_task,
                                    semaphore,
                                )
                            )

                    # Generate IMGT download tasks
                    if options.imgt:
                        for task in generate_imgt_tasks(entry, builder, options.output_path):
                            all_tasks.append(
                                execute_download_task(
                                    task,
                                    client,
                                    options.retries,
                                    stats,
                                    progress,
                                    overall_task,
                                    semaphore,
                                )
                            )

                    # Generate abangle download task
                    if options.abangle:
                        task = generate_abangle_task(
                            entry, builder, options.output_path, downloaded_abangles
                        )
                        if task:
                            all_tasks.append(
                                execute_download_task(
                                    task,
                                    client,
                                    options.retries,
                                    stats,
                                    progress,
                                    overall_task,
                                    semaphore,
                                )
                            )
                            downloaded_abangles.add(entry.pdb)

                # Execute all tasks concurrently
                if all_tasks:
                    await asyncio.gather(*all_tasks)

        # Print summary
        console.print(f"\nDownloaded: {stats.downloaded}")
        if stats.skipped > 0:
            console.print(f"Skipped (already exists): {stats.skipped}")
        if stats.failed > 0:
            console.print(f"Failed: {stats.failed}")
            for error in stats.errors[:10]:  # Show first 10 errors
                console.print(f"  [red]-[/red] {error}")
            if len(stats.errors) > 10:
                console.print(f"  [dim]... and {len(stats.errors) - 10} more[/dim]")

        console.print()

    except SummaryParseError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1
    except Exception as e:
        if "h2" in str(e) and "not installed" in str(e):
            console.print("[bold red]Error:[/bold red] HTTP/2 support is not installed.")
            console.print("Please install it with: [bold]pip install 'sabdab-cli[http2]'[/bold]")
            return 1
        if options.verbose:
            console.print_exception(show_locals=True)
        else:
            console.print(f"[bold red]Unexpected error:[/bold red] {e} Use -v for more details.")
        return 1

    return 0
