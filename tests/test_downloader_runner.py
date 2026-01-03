"""Tests for downloader.runner module."""

from __future__ import annotations

from pathlib import Path

import pytest

from sabdab_cli.downloader import DownloadOptions, run_download


@pytest.mark.unit
class TestRunDownload:
    """Test run_download function."""

    def test_missing_summary_file(self, tmp_path: Path) -> None:
        """Test error handling when summary file is missing."""
        summary_file = tmp_path / "nonexistent.tsv"
        output_path = tmp_path / "output"

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=True,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=None,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        exit_code = run_download(options)

        assert exit_code == 1

    def test_invalid_summary_file_format(self, tmp_path: Path) -> None:
        """Test error handling for invalid summary file format."""
        summary_file = tmp_path / "invalid.tsv"
        summary_file.write_text("invalid content without proper headers")
        output_path = tmp_path / "output"

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=True,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=None,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        exit_code = run_download(options)

        assert exit_code == 1

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Test that output directory is created."""
        summary_file = tmp_path / "summary.tsv"
        summary_file.write_text("pdb\tHchain\tLchain\tmodel\n1a2b\tH\tL\t0\n")
        output_path = tmp_path / "output"

        assert not output_path.exists()

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=False,  # Don't actually download
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=None,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        run_download(options)

        assert output_path.exists()
        assert output_path.is_dir()

    def test_verbose_mode(self, tmp_path: Path) -> None:
        """Test that verbose mode doesn't crash on errors."""
        summary_file = tmp_path / "nonexistent.tsv"
        output_path = tmp_path / "output"

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=True,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=None,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=True,
        )

        exit_code = run_download(options)

        assert exit_code == 1

    def test_empty_summary_file(self, tmp_path: Path) -> None:
        """Test handling of empty summary file."""
        summary_file = tmp_path / "empty.tsv"
        summary_file.write_text("pdb\tHchain\tLchain\tmodel\n")
        output_path = tmp_path / "output"

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=True,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=None,
            retries=3,
            timeout=30.0,
            http2=False,
            verbose=False,
        )

        exit_code = run_download(options)

        # Should fail with empty file (no data rows)
        assert exit_code == 1


@pytest.mark.integration
class TestRunDownloadIntegration:
    """Integration tests for run_download function."""

    def test_with_real_summary_file(self, tmp_path: Path) -> None:
        """Test with a real summary file structure."""
        summary_file = tmp_path / "summary.tsv"
        summary_file.write_text(
            "pdb\tHchain\tLchain\tmodel\tantigen_chain\tantigen_name\tantigen_type\n"
            "1a2b\tH\tL\t0\t\t\t\n"
        )
        output_path = tmp_path / "output"

        options = DownloadOptions(
            summary_file=summary_file,
            output_path=output_path,
            original_pdb=False,
            chothia_pdb=False,
            sequences=False,
            annotation=False,
            abangle=False,
            imgt=False,
            threads=None,
            retries=1,
            timeout=5.0,
            http2=False,
            verbose=False,
        )

        exit_code = run_download(options)

        # Should succeed even if no downloads were requested
        assert exit_code == 0
