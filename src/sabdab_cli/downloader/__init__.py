"""SAbDab downloader module.

This module provides functionality to download SAbDab antibody structure data
including PDB files, sequences, annotations, IMGT numbering, and AbAngle data.
"""

from sabdab_cli.downloader.core import DownloadOptions, DownloadStats, DownloadTask
from sabdab_cli.downloader.runner import run_download

__all__ = [
    "DownloadOptions",
    "DownloadStats",
    "DownloadTask",
    "run_download",
]
