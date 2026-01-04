import os
from pathlib import Path


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory to create.
    """
    path.mkdir(parents=True, exist_ok=True)


def get_concurrency_limit(threads: int | None) -> int:
    """Determine the concurrency limit based on user input or system defaults.

    Args:
        threads: User-specified thread count, or None for auto-detection.

    Returns:
        Number of concurrent downloads to allow.
    """
    if threads is not None:
        return threads

    # Auto-detect based on CPU count with reasonable limits
    cpu_count = os.cpu_count() or 1

    return min(cpu_count * 2, 20)
