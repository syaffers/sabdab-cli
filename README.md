# SAbDab CLI

A fast, multithreaded CLI for downloading data from [SAbDab](https://opig.stats.ox.ac.uk/webapps/newsabdab/sabdab/) (the Structural Antibody Database).

This tool is an alternative to the [SAbDab downloader script](https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/sabdab/downloads/sabdab_downloader.py).

## Highlights

- ⚡ **Concurrent Downloads**: High-performance async I/O for rapid data acquisition.
- 🛡️ **Robust Retries**: Built-in exponential backoff for transient network issues.
- 📊 **Rich Progress**: Beautiful terminal progress bars and informative feedback.
- 📦 **Atomic Writes**: Prevents data corruption by using temporary files during downloads.

## Installation

With `uv` (recommended):
```bash
uv add sabdab-cli
```

With `pip`:
```bash
pip install sabdab-cli
```

Or run directly without installing:
```bash
uvx sabdab-cli download -s summary.csv -o ./data --original-pdb
```

## Usage

You can invoke with `sabdab-cli` or `sabdabc`.

Download selected data types for entries in a SAbDab summary file:

```bash
sabdab-cli download \
  --summary-file summary.csv \
  --output-path ./data \
  --original-pdb \
  --chothia-pdb \
  --sequences \
  --annotation \
  --threads 10
```

### Available Data Types

| Flag | Description |
| :--- | :--- |
| `--original-pdb` | Original PDB structures |
| `--chothia-pdb` | Chothia-renumbered PDB structures |
| `--sequences` | Sequence FASTA files |
| `--annotation` | Chothia-numbered sequence annotations |
| `--abangle` | AbAngle orientation angles |
| `--imgt` | IMGT annotations |

### Summary File Format

The `--summary-file` (or `-s`) argument should be a TSV or CSV file containing at least the following columns: `pdb`, `Hchain`, `Lchain`, and `model`. See the test [summary file](tests/data/summary.csv) for an example.

### Performance Tuning

By default, `sabdab-cli` uses adaptive concurrency based on your CPU count. You can manually adjust this for your environment:

```bash
# High-concurrency mode (e.g., 20 threads)
sabdabc download -s summary.csv -o ./data --original-pdb --threads 20

# Synchronous mode (single thread)
sabdabc download -s summary.csv -o ./data --original-pdb --threads 1
```

## License

[MIT](LICENSE)