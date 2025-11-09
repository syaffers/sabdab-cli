"""Tests for summary TSV parsing."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest

from sabdab_cli.summary import (
    SAbDabEntry,
    SummaryParseError,
    group_entries_by_pdb,
    parse_summary_file,
    parse_summary_stream,
)


@pytest.mark.unit
class TestSAbDabEntry:
    """Test SAbDabEntry dataclass."""

    def test_entry_id(self) -> None:
        """Test entry ID generation."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")

        assert entry.entry_id == "3fct_B_A_0"

    def test_has_heavy_chain_true(self) -> None:
        """Test has_heavy_chain when chain exists."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")

        assert entry.has_heavy_chain is True

    def test_has_heavy_chain_false(self) -> None:
        """Test has_heavy_chain when chain is NA."""
        entry = SAbDabEntry(pdb="2w0l", hchain="NA", lchain="A", model="0")

        assert entry.has_heavy_chain is False

    def test_has_light_chain_true(self) -> None:
        """Test has_light_chain when chain exists."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")

        assert entry.has_light_chain is True

    def test_has_light_chain_false(self) -> None:
        """Test has_light_chain when chain is NA."""
        entry = SAbDabEntry(pdb="6qpg", hchain="M", lchain="NA", model="0")

        assert entry.has_light_chain is False

    def test_is_paired_true(self) -> None:
        """Test is_paired when both chains exist."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")

        assert entry.is_paired is True

    def test_is_paired_false_no_heavy(self) -> None:
        """Test is_paired when heavy chain missing."""
        entry = SAbDabEntry(pdb="2w0l", hchain="NA", lchain="A", model="0")

        assert entry.is_paired is False

    def test_is_paired_false_no_light(self) -> None:
        """Test is_paired when light chain missing."""
        entry = SAbDabEntry(pdb="6qpg", hchain="M", lchain="NA", model="0")

        assert entry.is_paired is False


@pytest.mark.unit
class TestParseSummaryStream:
    """Test summary stream parsing."""

    def test_parse_valid_stream(self) -> None:
        """Test parsing a valid TSV stream."""
        content = "pdb\tHchain\tLchain\tmodel\n3fct\tB\tA\t0\n3dgg\tD\tC\t0\n"
        stream = StringIO(content)
        entries = parse_summary_stream(stream)

        assert len(entries) == 2
        assert entries[0].pdb == "3fct"
        assert entries[0].hchain == "B"
        assert entries[0].lchain == "A"
        assert entries[0].model == "0"
        assert entries[1].pdb == "3dgg"

    def test_parse_empty_file(self) -> None:
        """Test parsing an empty file raises error."""
        stream = StringIO("")

        with pytest.raises(SummaryParseError, match="empty or missing header"):
            parse_summary_stream(stream)

    def test_parse_header_only(self) -> None:
        """Test parsing file with only header raises error."""
        content = "pdb\tHchain\tLchain\tmodel\n"
        stream = StringIO(content)

        with pytest.raises(SummaryParseError, match="no data rows"):
            parse_summary_stream(stream)

    def test_parse_missing_required_column(self) -> None:
        """Test parsing file missing required column raises error."""
        content = "pdb\tHchain\tmodel\n3fct\tB\t0\n"
        stream = StringIO(content)

        with pytest.raises(SummaryParseError, match=r"missing required columns.*Lchain"):
            parse_summary_stream(stream)

    def test_parse_with_extra_columns(self) -> None:
        """Test parsing file with extra columns succeeds."""
        content = "pdb\tHchain\tLchain\tmodel\tresolution\tmethod\n"
        content += "3fct\tB\tA\t0\t2.4\tX-RAY DIFFRACTION\n"
        stream = StringIO(content)
        entries = parse_summary_stream(stream)

        assert len(entries) == 1
        assert entries[0].pdb == "3fct"

    def test_parse_with_whitespace(self) -> None:
        """Test parsing strips whitespace from fields."""
        content = "pdb\tHchain\tLchain\tmodel\n  3fct  \t  B  \t  A  \t  0  \n"
        stream = StringIO(content)
        entries = parse_summary_stream(stream)

        assert len(entries) == 1
        assert entries[0].pdb == "3fct"
        assert entries[0].hchain == "B"

    def test_parse_nanobody_entry(self) -> None:
        """Test parsing entry with NA for light chain."""
        content = "pdb\tHchain\tLchain\tmodel\n6qpg\tM\tNA\t0\n"
        stream = StringIO(content)
        entries = parse_summary_stream(stream)

        assert len(entries) == 1
        assert entries[0].lchain == "NA"
        assert not entries[0].has_light_chain


@pytest.mark.unit
class TestParseSummaryFile:
    """Test summary file parsing from Path."""

    def test_parse_real_file(self, tmp_path: Path) -> None:
        """Test parsing a real file from filesystem."""
        test_file = tmp_path / "test_summary.tsv"
        content = "pdb\tHchain\tLchain\tmodel\n3fct\tB\tA\t0\n"
        test_file.write_text(content, encoding="utf-8")

        entries = parse_summary_file(test_file)

        assert len(entries) == 1
        assert entries[0].pdb == "3fct"

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """Test parsing non-existent file raises FileNotFoundError."""
        test_file = tmp_path / "nonexistent.tsv"
        with pytest.raises(FileNotFoundError, match="not found"):
            parse_summary_file(test_file)

    def test_parse_test_data_file(self) -> None:
        """Test parsing the actual test data file."""
        test_data = Path(__file__).parent / "data" / "summary.csv"
        if test_data.exists():
            entries = parse_summary_file(test_data)

            assert len(entries) > 0
            assert entries[0].pdb == "2w0l"
            assert entries[0].hchain == "NA"
            assert entries[0].lchain == "A"


@pytest.mark.unit
class TestGroupEntriesByPdb:
    """Test grouping entries by PDB ID."""

    def test_group_single_entry_per_pdb(self) -> None:
        """Test grouping when each PDB has one entry."""
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),
            SAbDabEntry(pdb="3dgg", hchain="D", lchain="C", model="0"),
        ]
        grouped = group_entries_by_pdb(entries)

        assert len(grouped) == 2
        assert "3fct" in grouped
        assert "3dgg" in grouped
        assert len(grouped["3fct"]) == 1
        assert len(grouped["3dgg"]) == 1

    def test_group_multiple_entries_per_pdb(self) -> None:
        """Test grouping when PDBs have multiple entries."""
        entries = [
            SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0"),
            SAbDabEntry(pdb="3fct", hchain="D", lchain="C", model="0"),
            SAbDabEntry(pdb="3dgg", hchain="B", lchain="A", model="0"),
        ]
        grouped = group_entries_by_pdb(entries)

        assert len(grouped) == 2
        assert len(grouped["3fct"]) == 2
        assert len(grouped["3dgg"]) == 1

    def test_group_empty_list(self) -> None:
        """Test grouping empty list returns empty dict."""
        entries: list[SAbDabEntry] = []
        grouped = group_entries_by_pdb(entries)
        assert len(grouped) == 0
