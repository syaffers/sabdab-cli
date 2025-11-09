"""Tests for URL building."""

from __future__ import annotations

import pytest

from sabdab_cli.summary import SAbDabEntry
from sabdab_cli.urls import SAbDabUrlBuilder
from conftest import DUMMY_BASE_URL


@pytest.fixture
def url_builder() -> SAbDabUrlBuilder:
    return SAbDabUrlBuilder(DUMMY_BASE_URL)


@pytest.mark.unit
class TestPdbUrls:
    """Test PDB structure URL building."""

    def test_build_original_pdb_url(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building original PDB URL."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_original_pdb_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/structure/3fct.pdb"
        assert url == expected

    def test_build_chothia_pdb_url(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building Chothia PDB URL."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_chothia_pdb_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/structure/chothia/3fct.pdb"
        assert url == expected


@pytest.mark.unit
class TestSequenceUrls:
    """Test sequence URL building."""

    def test_build_sequence_raw_url(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building raw sequence URL."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_sequence_raw_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/sequences/3fct_raw.fa"
        assert url == expected

    def test_build_sequence_vh_url_with_heavy(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building VH sequence URL when heavy chain exists."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_sequence_vh_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/sequences/3fct_B_VH.fa"
        assert url == expected

    def test_build_sequence_vh_url_without_heavy(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building VH sequence URL when heavy chain is NA."""
        entry = SAbDabEntry(pdb="2w0l", hchain="NA", lchain="A", model="0")
        url = url_builder.build_sequence_vh_url(entry)
        assert url is None

    def test_build_sequence_vl_url_with_light(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building VL sequence URL when light chain exists."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_sequence_vl_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/sequences/3fct_A_VL.fa"
        assert url == expected

    def test_build_sequence_vl_url_without_light(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building VL sequence URL when light chain is NA."""
        entry = SAbDabEntry(pdb="6qpg", hchain="M", lchain="NA", model="0")
        url = url_builder.build_sequence_vl_url(entry)
        assert url is None


@pytest.mark.unit
class TestAnnotationUrls:
    """Test annotation URL building."""

    def test_build_annotation_vh_url_with_heavy(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building VH annotation URL when heavy chain exists."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_annotation_vh_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/annotation/3fct_B_VH.ann"
        assert url == expected

    def test_build_annotation_vh_url_without_heavy(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building VH annotation URL when heavy chain is NA."""
        entry = SAbDabEntry(pdb="2w0l", hchain="NA", lchain="A", model="0")
        url = url_builder.build_annotation_vh_url(entry)
        assert url is None

    def test_build_annotation_vl_url_with_light(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building VL annotation URL when light chain exists."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_annotation_vl_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/annotation/3fct_A_VL.ann"
        assert url == expected

    def test_build_annotation_vl_url_without_light(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building VL annotation URL when light chain is NA."""
        entry = SAbDabEntry(pdb="6qpg", hchain="M", lchain="NA", model="0")
        url = url_builder.build_annotation_vl_url(entry)
        assert url is None


@pytest.mark.unit
class TestAbAngleUrls:
    """Test AbAngle URL building."""

    def test_build_abangle_url_paired(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building AbAngle URL for paired antibody."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_abangle_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/abangle/3fct.abangle"
        assert url == expected

    def test_build_abangle_url_nanobody(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building AbAngle URL for nanobody returns None."""
        entry = SAbDabEntry(pdb="6qpg", hchain="M", lchain="NA", model="0")
        url = url_builder.build_abangle_url(entry)
        assert url is None

    def test_build_abangle_url_light_only(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building AbAngle URL for light chain only returns None."""
        entry = SAbDabEntry(pdb="2w0l", hchain="NA", lchain="A", model="0")
        url = url_builder.build_abangle_url(entry)
        assert url is None


@pytest.mark.unit
class TestImgtUrls:
    """Test IMGT URL building."""

    def test_build_imgt_h_url_with_heavy(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building IMGT heavy chain URL when heavy chain exists."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_imgt_h_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/imgt/3fct_B_H.imgt"
        assert url == expected

    def test_build_imgt_h_url_without_heavy(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building IMGT heavy chain URL when heavy chain is NA."""
        entry = SAbDabEntry(pdb="2w0l", hchain="NA", lchain="A", model="0")
        url = url_builder.build_imgt_h_url(entry)
        assert url is None

    def test_build_imgt_l_url_with_light(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building IMGT light chain URL when light chain exists."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")
        url = url_builder.build_imgt_l_url(entry)
        expected = f"{DUMMY_BASE_URL}/entries/3fct/imgt/3fct_A_L.imgt"
        assert url == expected

    def test_build_imgt_l_url_without_light(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test building IMGT light chain URL when light chain is NA."""
        entry = SAbDabEntry(pdb="6qpg", hchain="M", lchain="NA", model="0")
        url = url_builder.build_imgt_l_url(entry)
        assert url is None


@pytest.mark.unit
class TestUrlConsistency:
    """Test URL consistency across different entry types."""

    def test_paired_antibody_all_urls(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test that paired antibody generates all appropriate URLs."""
        entry = SAbDabEntry(pdb="3fct", hchain="B", lchain="A", model="0")

        # Should have all URLs
        assert url_builder.build_original_pdb_url(entry) is not None
        assert url_builder.build_chothia_pdb_url(entry) is not None
        assert url_builder.build_sequence_raw_url(entry) is not None
        assert url_builder.build_sequence_vh_url(entry) is not None
        assert url_builder.build_sequence_vl_url(entry) is not None
        assert url_builder.build_annotation_vh_url(entry) is not None
        assert url_builder.build_annotation_vl_url(entry) is not None
        assert url_builder.build_abangle_url(entry) is not None
        assert url_builder.build_imgt_h_url(entry) is not None
        assert url_builder.build_imgt_l_url(entry) is not None

    def test_nanobody_limited_urls(self, url_builder: SAbDabUrlBuilder) -> None:
        """Test that nanobody generates only appropriate URLs."""
        entry = SAbDabEntry(pdb="6qpg", hchain="M", lchain="NA", model="0")

        # Should have PDB and heavy chain URLs
        assert url_builder.build_original_pdb_url(entry) is not None
        assert url_builder.build_chothia_pdb_url(entry) is not None
        assert url_builder.build_sequence_raw_url(entry) is not None
        assert url_builder.build_sequence_vh_url(entry) is not None
        assert url_builder.build_annotation_vh_url(entry) is not None
        assert url_builder.build_imgt_h_url(entry) is not None

        # Should NOT have light chain or AbAngle URLs
        assert url_builder.build_sequence_vl_url(entry) is None
        assert url_builder.build_annotation_vl_url(entry) is None
        assert url_builder.build_abangle_url(entry) is None
        assert url_builder.build_imgt_l_url(entry) is None
