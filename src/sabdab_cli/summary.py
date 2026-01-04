"""Parse and validate SAbDab summary TSV files."""

from __future__ import annotations

import csv
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


class SummaryParseError(Exception):
    """Raised when summary file parsing fails."""

    pass


@dataclass(frozen=True)
class SAbDabEntry:
    """Represents a single antibody entry from the SAbDab summary file.

    Attributes:
        - `id`: Alphanumeric Protein Data Bank (PDB) ID for an antibody.
        - `hchain`: Chain ID for the heavy chain of an antibody.
        - `lchain`: Chain ID for the light chain of an antibody.
        - `model`: The model number for the PDB entry.
    """

    pdb: str
    hchain: str
    lchain: str
    model: str

    @property
    def entry_id(self) -> str:
        """Unique identifier for this entry."""

        return f"{self.pdb}_{self.hchain}_{self.lchain}_{self.model}"

    @property
    def has_heavy_chain(self) -> bool:
        """Check if entry has a heavy chain."""

        return self.hchain != "NA"

    @property
    def has_light_chain(self) -> bool:
        """Check if entry has a light chain."""

        return self.lchain != "NA"

    @property
    def is_paired(self) -> bool:
        """Check if entry has both heavy and light chains."""

        return self.has_heavy_chain and self.has_light_chain


def parse_summary_file(file_path: Path) -> list[SAbDabEntry]:
    """Parse a SAbDab summary file into list of entries.

    For more information on a `SAbDabEntry`, see the `SAbDabEntry` class documentation.

    Usage
    ---

    ```
    >>> entries = parse_summary_file("tests/data/summary.csv")
    >>> print(entries)
    [
        SAbDabEntry(pdb='2w0l', hchain='NA', lchain='A', model='0'),
        SAbDabEntry(pdb='3fct', hchain='B', lchain='A', model='0'),
        ...
    ]
    ```

    Args
    ---
        `file_path`: Path to the summary file.

    Returns
    ---
        List of parsed `SAbDabEntry`s.

    Raises
    ---
        SummaryParseError: If the file format is invalid or required columns are missing.
        FileNotFoundError: If the file does not exist.
    """

    if not file_path.exists():
        raise FileNotFoundError(f"Summary file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return parse_summary_stream(f)


def parse_summary_stream(stream: TextIO) -> list[SAbDabEntry]:
    """Parse a SAbDab summary from an open file stream.

    Supports both tab-separated and comma-separated formats.

    Args:
        stream: Open text stream containing summary file data.

    Returns:
        List of parsed SAbDab entries.

    Raises:
        SummaryParseError: If the file format is invalid or required columns are missing.
    """

    # Peek at first line to detect delimiter
    header = stream.readline()
    if not header:
        raise SummaryParseError("Summary file's first line is empty")

    # SAbDab TSV usually uses tabs. If no tab is found, fallback to comma.
    delimiter = "\t" if "\t" in header else ","

    # Re-assemble the stream by chaining the header back
    reader = csv.DictReader(itertools.chain([header], stream), delimiter=delimiter)

    if reader.fieldnames is None:
        raise SummaryParseError("Summary file is empty or missing header")

    # Validate required columns exist
    required_columns = {"pdb", "Hchain", "Lchain", "model"}
    fieldnames_set = set(reader.fieldnames)

    missing_columns = required_columns - fieldnames_set
    if missing_columns:
        raise SummaryParseError(
            f"Summary file missing required columns: "
            f"{', '.join(sorted(missing_columns))}. "
            f"Assumed delimiter: {delimiter!r}"
        )

    entries: list[SAbDabEntry] = []
    # Line 1 is header, data starts at line 2.
    for line_num, row in enumerate(reader, start=2):
        try:
            entry = SAbDabEntry(
                pdb=row["pdb"].strip(),
                hchain=row["Hchain"].strip().upper(),  # Sometimes these are lowercase!
                lchain=row["Lchain"].strip().upper(),  # Sometimes these are lowercase!
                model=row["model"].strip(),
            )
            entries.append(entry)
        except KeyError as e:
            raise SummaryParseError(f"Missing column {e} on line {line_num}") from e
        except Exception as e:
            raise SummaryParseError(f"Error parsing line {line_num}: {e}") from e

    if not entries:
        raise SummaryParseError("Summary file contains no data rows")

    return entries


def group_entries_by_pdb(entries: list[SAbDabEntry]) -> dict[str, list[SAbDabEntry]]:
    """Group entries by their PDB ID.

    Args:
        entries: List of SAbDab entries.

    Returns:
        Dictionary mapping PDB ID to list of entries for that PDB.
    """

    grouped: dict[str, list[SAbDabEntry]] = {}

    for entry in entries:
        if entry.pdb not in grouped:
            grouped[entry.pdb] = []
        grouped[entry.pdb].append(entry)

    return grouped
