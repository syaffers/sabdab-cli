from importlib import metadata

try:
    __version__ = metadata.version("sabdab-cli")
except metadata.PackageNotFoundError:
    # Package is not installed (e.g., during development without local install)
    __version__ = "unknown"
