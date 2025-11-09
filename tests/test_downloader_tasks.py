"""Tests for downloader.tasks module."""

from __future__ import annotations

from pathlib import Path

import pytest

from sabdab_cli.downloader.core import DownloadOptions
from sabdab_cli.downloader.tasks import (
    count_total_files,
    generate_abangle_task,
    generate_annotation_tasks,
    generate_imgt_tasks,
    generate_pdb_tasks,
    generate_sequence_tasks,
)
from sabdab_cli.summary import SAbDabEntry
from sabdab_cli.urls import SAbDabUrlBuilder
from conftest import DUMMY_BASE_URL


@pytest.fixture
def url_builder() -> SAbDabUrlBuilder:
    """Create a SAbDabUrlBuilder instance."""
    return SAbDabUrlBuilder(base_url=DUMMY_BASE_URL)


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    return tmp_path / "output"


@pytest.fixture
def download_options(tmp_path: Path) -> DownloadOptions:
    """Create DownloadOptions with all options enabled."""
    return DownloadOptions(
        summary_file=tmp_path / "summary.csv",
        output_path=tmp_path / "output",
        original_pdb=True,
        chothia_pdb=True,
        sequences=True,
        annotation=True,
        abangle=True,
        imgt=True,
        threads=4,
        retries=3,
        timeout=30.0,
        http2=False,
        verbose=False,
    )


@pytest.fixture
def paired_entry() -> SAbDabEntry:
    """Create a paired antibody entry."""
    return SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")


@pytest.fixture
def heavy_only_entry() -> SAbDabEntry:
    """Create an entry with only heavy chain."""
    return SAbDabEntry(pdb="1abc", hchain="H", lchain="NA", model="0")


@pytest.fixture
def light_only_entry() -> SAbDabEntry:
    """Create an entry with only light chain."""
    return SAbDabEntry(pdb="2w0l", hchain="NA", lchain="A", model="0")


class TestGeneratePdbTasks:
    """Tests for generate_pdb_tasks function."""

    def test_both_pdb_types_enabled(
        self,
        paired_entry: SAbDabEntry,
        url_builder: SAbDabUrlBuilder,
        output_path: Path,
        download_options: DownloadOptions,
    ) -> None:
        """Test generating tasks when both PDB types are enabled."""
        tasks = generate_pdb_tasks(paired_entry, url_builder, output_path, download_options, set())

        assert len(tasks) == 2
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/3fct/structure/3fct.pdb"
        assert tasks[0].dest == output_path / "original" / "3fct.pdb"
        assert tasks[1].url == f"{DUMMY_BASE_URL}/entries/3fct/structure/chothia/3fct.pdb"
        assert tasks[1].dest == output_path / "chothia" / "3fct.pdb"

    def test_original_pdb_only(
        self,
        paired_entry: SAbDabEntry,
        url_builder: SAbDabUrlBuilder,
        output_path: Path,
        download_options: DownloadOptions,
    ) -> None:
        """Test generating tasks when only original PDB is enabled."""
        options = DownloadOptions(
            summary_file=download_options.summary_file,
            output_path=output_path,
            original_pdb=True,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=4,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        tasks = generate_pdb_tasks(paired_entry, url_builder, output_path, options, set())

        assert len(tasks) == 1
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/3fct/structure/3fct.pdb"
        assert tasks[0].dest == output_path / "original" / "3fct.pdb"

    def test_chothia_pdb_only(
        self,
        paired_entry: SAbDabEntry,
        url_builder: SAbDabUrlBuilder,
        output_path: Path,
        download_options: DownloadOptions,
    ) -> None:
        """Test generating tasks when only Chothia PDB is enabled."""
        options = DownloadOptions(
            summary_file=download_options.summary_file,
            output_path=output_path,
            original_pdb=False,
            chothia_pdb=True,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=4,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        tasks = generate_pdb_tasks(paired_entry, url_builder, output_path, options, set())

        assert len(tasks) == 1
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/3fct/structure/chothia/3fct.pdb"
        assert tasks[0].dest == output_path / "chothia" / "3fct.pdb"

    def test_already_downloaded(
        self,
        paired_entry: SAbDabEntry,
        url_builder: SAbDabUrlBuilder,
        output_path: Path,
        download_options: DownloadOptions,
    ) -> None:
        """Test that no tasks are generated for already downloaded PDBs."""
        downloaded_pdbs = {"3fct"}

        tasks = generate_pdb_tasks(
            paired_entry, url_builder, output_path, download_options, downloaded_pdbs
        )

        assert len(tasks) == 0

    def test_no_pdb_options_enabled(
        self,
        paired_entry: SAbDabEntry,
        url_builder: SAbDabUrlBuilder,
        output_path: Path,
        download_options: DownloadOptions,
    ) -> None:
        """Test that no tasks are generated when no PDB options are enabled."""
        options = DownloadOptions(
            summary_file=download_options.summary_file,
            output_path=output_path,
            original_pdb=False,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=4,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        tasks = generate_pdb_tasks(paired_entry, url_builder, output_path, options, set())

        assert len(tasks) == 0


class TestGenerateSequenceTasks:
    """Tests for generate_sequence_tasks function."""

    def test_paired_entry(
        self, paired_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating sequence tasks for paired entry."""
        tasks = generate_sequence_tasks(paired_entry, url_builder, output_path)

        assert len(tasks) == 3
        # Raw sequence
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/3fct/sequences/3fct_raw.fa"
        assert tasks[0].dest == output_path / "sequences" / "3fct_raw.fa"
        # VH sequence
        assert tasks[1].url == f"{DUMMY_BASE_URL}/entries/3fct/sequences/3fct_B_VH.fa"
        assert tasks[1].dest == output_path / "sequences" / "3fct_B_VH.fa"
        # VL sequence
        assert tasks[2].url == f"{DUMMY_BASE_URL}/entries/3fct/sequences/3fct_A_VL.fa"
        assert tasks[2].dest == output_path / "sequences" / "3fct_A_VL.fa"

    def test_heavy_only_entry(
        self, heavy_only_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating sequence tasks for heavy-only entry."""
        tasks = generate_sequence_tasks(heavy_only_entry, url_builder, output_path)

        assert len(tasks) == 2
        # Raw sequence
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/1abc/sequences/1abc_raw.fa"
        assert tasks[0].dest == output_path / "sequences" / "1abc_raw.fa"
        # VH sequence
        assert tasks[1].url == f"{DUMMY_BASE_URL}/entries/1abc/sequences/1abc_H_VH.fa"
        assert tasks[1].dest == output_path / "sequences" / "1abc_H_VH.fa"

    def test_light_only_entry(
        self, light_only_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating sequence tasks for light-only entry."""
        tasks = generate_sequence_tasks(light_only_entry, url_builder, output_path)

        assert len(tasks) == 2
        # Raw sequence
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/2w0l/sequences/2w0l_raw.fa"
        assert tasks[0].dest == output_path / "sequences" / "2w0l_raw.fa"
        # VL sequence
        assert tasks[1].url == f"{DUMMY_BASE_URL}/entries/2w0l/sequences/2w0l_A_VL.fa"
        assert tasks[1].dest == output_path / "sequences" / "2w0l_A_VL.fa"


class TestGenerateAnnotationTasks:
    """Tests for generate_annotation_tasks function."""

    def test_paired_entry(
        self, paired_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating annotation tasks for paired entry."""
        tasks = generate_annotation_tasks(paired_entry, url_builder, output_path)

        assert len(tasks) == 2
        # VH annotation
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/3fct/annotation/3fct_B_VH.ann"
        assert tasks[0].dest == output_path / "annotation" / "3fct_B_VH.ann"
        # VL annotation
        assert tasks[1].url == f"{DUMMY_BASE_URL}/entries/3fct/annotation/3fct_A_VL.ann"
        assert tasks[1].dest == output_path / "annotation" / "3fct_A_VL.ann"

    def test_heavy_only_entry(
        self, heavy_only_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating annotation tasks for heavy-only entry."""
        tasks = generate_annotation_tasks(heavy_only_entry, url_builder, output_path)

        assert len(tasks) == 1
        # VH annotation
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/1abc/annotation/1abc_H_VH.ann"
        assert tasks[0].dest == output_path / "annotation" / "1abc_H_VH.ann"

    def test_light_only_entry(
        self, light_only_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating annotation tasks for light-only entry."""
        tasks = generate_annotation_tasks(light_only_entry, url_builder, output_path)

        assert len(tasks) == 1
        # VL annotation
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/2w0l/annotation/2w0l_A_VL.ann"
        assert tasks[0].dest == output_path / "annotation" / "2w0l_A_VL.ann"


class TestGenerateImgtTasks:
    """Tests for generate_imgt_tasks function."""

    def test_paired_entry(
        self, paired_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating IMGT tasks for paired entry."""
        tasks = generate_imgt_tasks(paired_entry, url_builder, output_path)

        assert len(tasks) == 2
        # H IMGT
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/3fct/imgt/3fct_B_H.imgt"
        assert tasks[0].dest == output_path / "imgt" / "3fct_B_H.imgt"
        # L IMGT
        assert tasks[1].url == f"{DUMMY_BASE_URL}/entries/3fct/imgt/3fct_A_L.imgt"
        assert tasks[1].dest == output_path / "imgt" / "3fct_A_L.imgt"

    def test_heavy_only_entry(
        self, heavy_only_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating IMGT tasks for heavy-only entry."""
        tasks = generate_imgt_tasks(heavy_only_entry, url_builder, output_path)

        assert len(tasks) == 1
        # H IMGT
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/1abc/imgt/1abc_H_H.imgt"
        assert tasks[0].dest == output_path / "imgt" / "1abc_H_H.imgt"

    def test_light_only_entry(
        self, light_only_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating IMGT tasks for light-only entry."""
        tasks = generate_imgt_tasks(light_only_entry, url_builder, output_path)

        assert len(tasks) == 1
        # L IMGT
        assert tasks[0].url == f"{DUMMY_BASE_URL}/entries/2w0l/imgt/2w0l_A_L.imgt"
        assert tasks[0].dest == output_path / "imgt" / "2w0l_A_L.imgt"


class TestGenerateAbAngleTask:
    """Tests for generate_abangle_task function."""

    def test_paired_entry(
        self, paired_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test generating abangle task for paired entry."""
        task = generate_abangle_task(paired_entry, url_builder, output_path, set())

        assert task is not None
        assert task.url == f"{DUMMY_BASE_URL}/entries/3fct/abangle/3fct.abangle"
        assert task.dest == output_path / "abangle" / "3fct.abangle"

    def test_heavy_only_entry(
        self, heavy_only_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test that no abangle task is generated for heavy-only entry."""
        task = generate_abangle_task(heavy_only_entry, url_builder, output_path, set())

        assert task is None

    def test_light_only_entry(
        self, light_only_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test that no abangle task is generated for light-only entry."""
        task = generate_abangle_task(light_only_entry, url_builder, output_path, set())

        assert task is None

    def test_already_downloaded(
        self, paired_entry: SAbDabEntry, url_builder: SAbDabUrlBuilder, output_path: Path
    ) -> None:
        """Test that no task is generated for already downloaded abangle."""
        downloaded_abangles = {"3fct"}

        task = generate_abangle_task(paired_entry, url_builder, output_path, downloaded_abangles)

        assert task is None


class TestCountTotalFiles:
    """Tests for count_total_files function."""

    def test_all_options_enabled_paired_entry(self, download_options: DownloadOptions) -> None:
        """Test counting files with all options enabled for paired entry."""
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),
        ]
        grouped = {"3fct": entries}

        count = count_total_files(entries, grouped, download_options)

        # 1 original PDB + 1 chothia PDB
        # + 3 sequences (raw, VH, VL)
        # + 2 annotations (VH, VL)
        # + 2 IMGT (H, L)
        # + 1 abangle
        assert count == 10

    def test_all_options_enabled_heavy_only(self, download_options: DownloadOptions) -> None:
        """Test counting files with all options enabled for heavy-only entry."""
        entries = [
            SAbDabEntry(pdb="1abc", hchain="H", lchain="NA", model="0"),
        ]
        grouped = {"1abc": entries}

        count = count_total_files(entries, grouped, download_options)

        # 1 original PDB + 1 chothia PDB
        # + 2 sequences (raw, VH)
        # + 1 annotation (VH)
        # + 1 IMGT (H)
        # + 0 abangle (not paired)
        assert count == 6

    def test_all_options_enabled_light_only(self, download_options: DownloadOptions) -> None:
        """Test counting files with all options enabled for light-only entry."""
        entries = [
            SAbDabEntry(pdb="2w0l", hchain="NA", lchain="A", model="0"),
        ]
        grouped = {"2w0l": entries}

        count = count_total_files(entries, grouped, download_options)

        # 1 original PDB + 1 chothia PDB
        # + 2 sequences (raw, VL)
        # + 1 annotation (VL)
        # + 1 IMGT (L)
        # + 0 abangle (not paired)
        assert count == 6

    def test_only_pdb_files(self, tmp_path: Path) -> None:
        """Test counting only PDB files."""
        options = DownloadOptions(
            summary_file=tmp_path / "summary.csv",
            output_path=tmp_path / "output",
            original_pdb=True,
            chothia_pdb=True,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=4,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),
        ]
        grouped = {"3fct": entries}

        count = count_total_files(entries, grouped, options)

        assert count == 2

    def test_only_sequences(self, tmp_path: Path) -> None:
        """Test counting only sequence files."""
        options = DownloadOptions(
            summary_file=tmp_path / "summary.csv",
            output_path=tmp_path / "output",
            original_pdb=False,
            chothia_pdb=False,
            sequences=True,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=4,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),
        ]
        grouped = {"3fct": entries}

        count = count_total_files(entries, grouped, options)

        # raw + VH + VL
        assert count == 3

    def test_multiple_entries_same_pdb(self, download_options: DownloadOptions) -> None:
        """Test counting files for multiple entries with same PDB ID."""
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),
            SAbDabEntry(pdb="3fct", hchain="D", lchain="C", model="0"),
        ]
        grouped = {"3fct": entries}

        count = count_total_files(entries, grouped, download_options)

        # 1 original PDB + 1 chothia PDB (only one per PDB)
        # + 3 sequences per entry = 6 total
        # + 2 annotations per entry = 4 total
        # + 2 IMGT per entry = 4 total
        # + 1 abangle (only one per PDB, any paired)
        assert count == 17

    def test_multiple_different_pdbs(self, download_options: DownloadOptions) -> None:
        """Test counting files for multiple entries with different PDB IDs."""
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),
            SAbDabEntry(pdb="1abc", hchain="H", lchain="L", model="0"),
        ]
        grouped = {
            "3fct": [entries[0]],
            "1abc": [entries[1]],
        }

        count = count_total_files(entries, grouped, download_options)

        # 2 original PDB + 2 chothia PDB
        # + 3 sequences per entry = 6 total
        # + 2 annotations per entry = 4 total
        # + 2 IMGT per entry = 4 total
        # + 2 abangle (one per PDB)
        assert count == 20

    def test_no_options_enabled(self, tmp_path: Path) -> None:
        """Test counting with no options enabled."""
        options = DownloadOptions(
            summary_file=tmp_path / "summary.csv",
            output_path=tmp_path / "output",
            original_pdb=False,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=4,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),
        ]
        grouped = {"3fct": entries}

        count = count_total_files(entries, grouped, options)

        assert count == 0

    def test_abangle_only_for_paired_entries(self, tmp_path: Path) -> None:
        """Test that abangle is only counted for PDBs with paired entries."""
        options = DownloadOptions(
            summary_file=tmp_path / "summary.csv",
            output_path=tmp_path / "output",
            original_pdb=False,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=True,
            imgt=False,
            threads=4,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),  # paired
            SAbDabEntry(pdb="1abc", hchain="H", lchain="NA", model="0"),  # heavy only
        ]
        grouped = {
            "3fct": [entries[0]],
            "1abc": [entries[1]],
        }

        count = count_total_files(entries, grouped, options)

        # Only 1 abangle for 3fct (paired), none for 1abc
        assert count == 1
