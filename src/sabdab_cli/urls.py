"""Build URLs for downloading SAbDab data."""

from __future__ import annotations

from sabdab_cli.summary import SAbDabEntry

# Base URL for SAbDab source data.
SABDAB_BASE_URL = "https://opig.stats.ox.ac.uk/webapps/abdb"


class SAbDabUrlBuilder:
    """Build URLs for downloading SAbDab data."""

    def __init__(self, base_url: str | None = None):
        """Initialize the URL builder.

        Usage
        ---
        ```
        >>> builder = SAbDabUrlBuilder()
        >>> builder.build_original_pdb_url(entry)
        'https://opig.stats.ox.ac.uk/webapps/abdb/entries/3fct/structure/3fct.pdb'
        ```

        Args
        ---
            `base_url`: Base URL for SAbDab source data.
        """
        self.base_url = base_url or SABDAB_BASE_URL

    def build_original_pdb_url(self, entry: SAbDabEntry) -> str:
        """Build URL for original PDB structure.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string for downloading the original PDB file.
        """
        return f"{self.base_url}/entries/{entry.pdb}/structure/{entry.pdb}.pdb"

    def build_chothia_pdb_url(self, entry: SAbDabEntry) -> str:
        """Build URL for Chothia-renumbered PDB structure.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string for downloading the Chothia PDB file.
        """
        return f"{self.base_url}/entries/{entry.pdb}/structure/chothia/{entry.pdb}.pdb"

    def build_sequence_raw_url(self, entry: SAbDabEntry) -> str:
        """Build URL for raw sequence file.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string for downloading the raw sequence file.
        """
        return f"{self.base_url}/entries/{entry.pdb}/sequences/{entry.pdb}_raw.fa"

    def build_sequence_vh_url(self, entry: SAbDabEntry) -> str | None:
        """Build URL for heavy chain variable region sequence.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string if entry has heavy chain, None otherwise.
        """
        if not entry.has_heavy_chain:
            return None

        return f"{self.base_url}/entries/{entry.pdb}/sequences/{entry.pdb}_{entry.hchain}_VH.fa"

    def build_sequence_vl_url(self, entry: SAbDabEntry) -> str | None:
        """Build URL for light chain variable region sequence.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string if entry has light chain, None otherwise.
        """
        if not entry.has_light_chain:
            return None

        return f"{self.base_url}/entries/{entry.pdb}/sequences/{entry.pdb}_{entry.lchain}_VL.fa"

    def build_annotation_vh_url(self, entry: SAbDabEntry) -> str | None:
        """Build URL for heavy chain annotation file.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string if entry has heavy chain, None otherwise.
        """
        if not entry.has_heavy_chain:
            return None

        return f"{self.base_url}/entries/{entry.pdb}/annotation/{entry.pdb}_{entry.hchain}_VH.ann"

    def build_annotation_vl_url(self, entry: SAbDabEntry) -> str | None:
        """Build URL for light chain annotation file.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string if entry has light chain, None otherwise.
        """
        if not entry.has_light_chain:
            return None

        return f"{self.base_url}/entries/{entry.pdb}/annotation/{entry.pdb}_{entry.lchain}_VL.ann"

    def build_abangle_url(self, entry: SAbDabEntry) -> str | None:
        """Build URL for AbAngle orientation angles file.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string if entry is paired, None otherwise.
        """
        if not entry.is_paired:
            return None

        return f"{self.base_url}/entries/{entry.pdb}/abangle/{entry.pdb}.abangle"

    def build_imgt_h_url(self, entry: SAbDabEntry) -> str | None:
        """Build URL for IMGT heavy chain annotation file.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string if entry has heavy chain, None otherwise.
        """
        if not entry.has_heavy_chain:
            return None

        return f"{self.base_url}/entries/{entry.pdb}/imgt/{entry.pdb}_{entry.hchain}_H.imgt"

    def build_imgt_l_url(self, entry: SAbDabEntry) -> str | None:
        """Build URL for IMGT light chain annotation file.

        Args:
            entry: SAbDab entry.

        Returns:
            URL string if entry has light chain, None otherwise.
        """
        if not entry.has_light_chain:
            return None

        return f"{self.base_url}/entries/{entry.pdb}/imgt/{entry.pdb}_{entry.lchain}_L.imgt"
