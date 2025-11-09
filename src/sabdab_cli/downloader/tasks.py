"""Task generation logic for different file types."""

from __future__ import annotations

from pathlib import Path

from sabdab_cli.summary import SAbDabEntry
from sabdab_cli.urls import SAbDabUrlBuilder
from sabdab_cli.downloader.core import DownloadOptions, DownloadTask


def generate_pdb_tasks(
    entry: SAbDabEntry,
    builder: SAbDabUrlBuilder,
    output_path: Path,
    options: DownloadOptions,
    downloaded_pdbs: set[str],
) -> list[DownloadTask]:
    """Generate download tasks for PDB files.

    Args:
        entry: Summary entry to generate tasks for.
        builder: URL builder instance.
        output_path: Base output directory.
        options: Download options.
        downloaded_pdbs: Set of already downloaded PDB IDs.

    Returns:
        List of download tasks.
    """
    tasks = []

    if entry.pdb in downloaded_pdbs:
        return tasks

    if options.original_pdb:
        url = builder.build_original_pdb_url(entry)
        dest = output_path / "original" / f"{entry.pdb}.pdb"
        tasks.append(DownloadTask(url=url, dest=dest))

    if options.chothia_pdb:
        url = builder.build_chothia_pdb_url(entry)
        dest = output_path / "chothia" / f"{entry.pdb}.pdb"
        tasks.append(DownloadTask(url=url, dest=dest))

    return tasks


def generate_sequence_tasks(
    entry: SAbDabEntry, builder: SAbDabUrlBuilder, output_path: Path
) -> list[DownloadTask]:
    """Generate download tasks for sequence files.

    Args:
        entry: Summary entry to generate tasks for.
        builder: URL builder instance.
        output_path: Base output directory.

    Returns:
        List of download tasks.
    """
    tasks = []

    # Raw sequence
    url = builder.build_sequence_raw_url(entry)
    dest = output_path / "sequences" / f"{entry.pdb}_raw.fa"
    tasks.append(DownloadTask(url=url, dest=dest))

    # VH sequence
    if entry.has_heavy_chain:
        url = builder.build_sequence_vh_url(entry)
        if url:
            dest = output_path / "sequences" / f"{entry.pdb}_{entry.hchain}_VH.fa"
            tasks.append(DownloadTask(url=url, dest=dest))

    # VL sequence
    if entry.has_light_chain:
        url = builder.build_sequence_vl_url(entry)
        if url:
            dest = output_path / "sequences" / f"{entry.pdb}_{entry.lchain}_VL.fa"
            tasks.append(DownloadTask(url=url, dest=dest))

    return tasks


def generate_annotation_tasks(
    entry: SAbDabEntry, builder: SAbDabUrlBuilder, output_path: Path
) -> list[DownloadTask]:
    """Generate download tasks for annotation files.

    Args:
        entry: Summary entry to generate tasks for.
        builder: URL builder instance.
        output_path: Base output directory.

    Returns:
        List of download tasks.
    """
    tasks = []

    # VH annotation
    if entry.has_heavy_chain:
        url = builder.build_annotation_vh_url(entry)
        if url:
            dest = output_path / "annotation" / f"{entry.pdb}_{entry.hchain}_VH.ann"
            tasks.append(DownloadTask(url=url, dest=dest))

    # VL annotation
    if entry.has_light_chain:
        url = builder.build_annotation_vl_url(entry)
        if url:
            dest = output_path / "annotation" / f"{entry.pdb}_{entry.lchain}_VL.ann"
            tasks.append(DownloadTask(url=url, dest=dest))

    return tasks


def generate_imgt_tasks(
    entry: SAbDabEntry, builder: SAbDabUrlBuilder, output_path: Path
) -> list[DownloadTask]:
    """Generate download tasks for IMGT files.

    Args:
        entry: Summary entry to generate tasks for.
        builder: URL builder instance.
        output_path: Base output directory.

    Returns:
        List of download tasks.
    """
    tasks = []

    # H IMGT
    if entry.has_heavy_chain:
        url = builder.build_imgt_h_url(entry)
        if url:
            dest = output_path / "imgt" / f"{entry.pdb}_{entry.hchain}_H.imgt"
            tasks.append(DownloadTask(url=url, dest=dest))

    # L IMGT
    if entry.has_light_chain:
        url = builder.build_imgt_l_url(entry)
        if url:
            dest = output_path / "imgt" / f"{entry.pdb}_{entry.lchain}_L.imgt"
            tasks.append(DownloadTask(url=url, dest=dest))

    return tasks


def generate_abangle_task(
    entry: SAbDabEntry,
    builder: SAbDabUrlBuilder,
    output_path: Path,
    downloaded_abangles: set[str],
) -> DownloadTask | None:
    """Generate download task for abangle file if applicable.

    Args:
        entry: Summary entry to generate task for.
        builder: URL builder instance.
        output_path: Base output directory.
        downloaded_abangles: Set of already downloaded abangle PDB IDs.

    Returns:
        Download task if applicable, None otherwise.
    """
    if entry.pdb in downloaded_abangles:
        return None

    url = builder.build_abangle_url(entry)
    if not url:  # Only if entry is paired
        return None

    dest = output_path / "abangle" / f"{entry.pdb}.abangle"
    return DownloadTask(url=url, dest=dest)


def count_total_files(
    entries: list[SAbDabEntry], grouped_by_pdb: dict, options: DownloadOptions
) -> int:
    """Count the total number of files to download based on options.

    Args:
        entries: List of all entries.
        grouped_by_pdb: Dictionary mapping PDB IDs to list of entries.
        options: Download options.

    Returns:
        Total number of files to download.
    """
    count = 0

    # PDB files: one per unique PDB
    if options.original_pdb:
        count += len(grouped_by_pdb)
    if options.chothia_pdb:
        count += len(grouped_by_pdb)

    # Per-entry files with chain-specific downloads
    for entry in entries:
        if options.sequences:
            count += 1  # raw sequence
            if entry.has_heavy_chain:
                count += 1  # VH
            if entry.has_light_chain:
                count += 1  # VL

        if options.annotation:
            if entry.has_heavy_chain:
                count += 1  # VH annotation
            if entry.has_light_chain:
                count += 1  # VL annotation

        if options.imgt:
            if entry.has_heavy_chain:
                count += 1  # H IMGT
            if entry.has_light_chain:
                count += 1  # L IMGT

    # AbAngle: one per PDB if any entry is paired
    if options.abangle:
        for pdb_entries in grouped_by_pdb.values():
            if any(e.is_paired for e in pdb_entries):
                count += 1

    return count
