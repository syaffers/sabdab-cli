from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from sabdab_cli import __version__
from sabdab_cli.downloader import DownloadOptions, run_download

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="SAbDab CLI: download structures, sequences, annotations, and related data.",
)


@app.command(no_args_is_help=True)
def download(
    summary_file: Path = typer.Option(
        ...,
        "--summary-file",
        "-s",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Summary file from SAbDab (must include columns: pdb, Hchain, Lchain, model).",
    ),
    output_path: Path = typer.Option(
        ...,
        "--output-path",
        "-o",
        file_okay=False,
        dir_okay=True,
        writable=True,
        help="Path to the download directory",
    ),
    original_pdb: bool = typer.Option(
        False, "--original-pdb", help="Download original PDB structures."
    ),
    chothia_pdb: bool = typer.Option(
        False, "--chothia-pdb", help="Download Chothia-renumbered PDB structures."
    ),
    sequences: bool = typer.Option(False, "--sequences", help="Download sequence FASTA files."),
    annotation: bool = typer.Option(
        False, "--annotation", help="Download Chothia-numbered sequence annotations."
    ),
    abangle: bool = typer.Option(False, "--abangle", help="Download AbAngle orientation angles."),
    imgt: bool = typer.Option(False, "--imgt", help="Download IMGT annotations."),
    threads: int | None = typer.Option(
        None,
        "--threads",
        "-t",
        min=1,
        help="Number of threads to use for downloads.",
    ),
    retries: int = typer.Option(
        3, "--retries", min=0, help="Number of retry attempts for transient failures."
    ),
    timeout: float = typer.Option(
        30.0, "--timeout", min=1.0, help="HTTP timeout (seconds) per request."
    ),
    http2: bool = typer.Option(
        False, "--http2/--no-http2", help="Enable HTTP/2 for downloads when supported."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose error details."),
) -> None:
    """
    Download selected SAbDab assets specified by the summary file.
    """
    if not any([original_pdb, chothia_pdb, sequences, annotation, abangle, imgt]):
        typer.echo(
            "No data types selected. Choose at least one of the following: "
            "--original-pdb, --chothia-pdb, --sequences, --annotation, --abangle, --imgt."
        )
        raise typer.Exit(code=2)

    options = DownloadOptions(
        summary_file=summary_file,
        output_path=output_path,
        original_pdb=original_pdb,
        chothia_pdb=chothia_pdb,
        sequences=sequences,
        annotation=annotation,
        abangle=abangle,
        imgt=imgt,
        threads=threads,
        retries=retries,
        timeout=timeout,
        http2=http2,
        verbose=verbose,
    )

    exit_code = asyncio.run(run_download(options))

    raise typer.Exit(code=exit_code)


@app.command()
def version():
    """
    Display the current version of sabdab-cli.
    """
    typer.echo(f"SAbDab CLI version {__version__}")


if __name__ == "__main__":
    app()
