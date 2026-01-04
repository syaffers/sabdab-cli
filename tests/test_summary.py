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

    @pytest.mark.parametrize("hchain, expected_has_heavy_chain", [("B", True), ("NA", False)])
    def test_has_heavy_chain(self, hchain: str, expected_has_heavy_chain: bool) -> None:
        """Test has_heavy_chain property."""
        entry = SAbDabEntry(pdb="3fct", hchain=hchain, lchain="A", model="0")

        assert entry.has_heavy_chain is expected_has_heavy_chain

    @pytest.mark.parametrize("lchain, expected_has_light_chain", [("A", True), ("NA", False)])
    def test_has_light_chain(self, lchain: str, expected_has_light_chain: bool) -> None:
        """Test has_light_chain property."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain=lchain, model="0")

        assert entry.has_light_chain is expected_has_light_chain

    @pytest.mark.parametrize(
        "hchain, lchain, expected_is_paired",
        [("B", "A", True), ("NA", "A", False), ("B", "NA", False)],
    )
    def test_is_paired(self, hchain: str, lchain: str, expected_is_paired: bool) -> None:
        """Test is_paired property."""
        entry = SAbDabEntry(pdb="3fct", hchain=hchain, lchain=lchain, model="0")

        assert entry.is_paired is expected_is_paired


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

    def test_parse_valid_csv_stream(self) -> None:
        """Test parsing a valid CSV stream (comma-separated)."""
        content = "pdb,Hchain,Lchain,model\n3fct,B,A,0\n3dgg,D,C,0\n"
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

        with pytest.raises(SummaryParseError, match="first line is empty"):
            parse_summary_stream(stream)

    def test_parse_header_only(self) -> None:
        """Test parsing file with only header raises error."""
        content = "pdb\tHchain\tLchain\tmodel\n"
        stream = StringIO(content)

        with pytest.raises(SummaryParseError, match="no data rows"):
            parse_summary_stream(stream)

    def test_parse_invalid_delimiter(self) -> None:
        """Test parsing file with invalid delimiter raises error."""
        content = "pdb Hchain Lchain model\n3fct B A 0\n"
        stream = StringIO(content)

        with pytest.raises(SummaryParseError, match="Assumed delimiter"):
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
