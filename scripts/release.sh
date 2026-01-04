#!/bin/bash
# Release script.
#
# Usage: ./scripts/release.sh <major|minor|patch> [--dry-run]

set -e

DRY_RUN=false
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}"

if [ -z "$1" ]; then
    echo "Usage: $0 <major|minor|patch> [--dry-run]"
    exit 1
fi

BUMP_TYPE=$1

# Helper function to run commands unless dry run is enabled
run_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would execute: $*"
    else
        "$@"
    fi
}

# 0. Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: You have uncommitted changes. Please commit or stash them before releasing."
    exit 1
fi

# 1. Bump version
echo "Bumping version ($BUMP_TYPE)..."
if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] uv version --bump $BUMP_TYPE"
    # Try to get current version for display purposes
    CURRENT_VERSION=$(uv version --short)
    VERSION="$CURRENT_VERSION+next"
    echo "New version: $VERSION (simulated)"
else
    uv version --bump "$BUMP_TYPE"
    # Get the new version
    VERSION=$(uv version --short)
    echo "New version: $VERSION"
fi

# 2. Build the package
echo "Building package..."
run_cmd uv build

# 3. Generate release notes
echo "Generating release notes..."
if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] uv run scripts/generate_release_notes.py $VERSION > RELEASE_NOTES.md"
else
    uv run scripts/generate_release_notes.py "$VERSION" > RELEASE_NOTES.md
    echo "Release notes generated in RELEASE_NOTES.md"
fi

# 4. Publish to PyPI
# uv publish uses UV_PUBLISH_TOKEN by default if available.
if [ -z "$UV_PUBLISH_TOKEN" ]; then
    echo "Warning: UV_PUBLISH_TOKEN not set in environment."
    echo "If you have another environment variable for the token, please set UV_PUBLISH_TOKEN to it."
    echo "Example: export UV_PUBLISH_TOKEN=\$PYPI_API_TOKEN"
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would prompt for continuation without token."
    else
        read -p "Do you want to continue without publishing to PyPI? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "Publishing to PyPI..."
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] uv publish --dry-run"
    else
        uv publish
    fi
fi

# 5. Git operations
echo "Committing version bump and release notes..."
run_cmd uv lock
run_cmd git add pyproject.toml uv.lock
if [ ! -f RELEASE_NOTES.md ] && [ "$DRY_RUN" != true ]; then
    # This shouldn't happen if not dry run, but just in case
    :
else
    # Only add if it exists or in dry run (where we simulate its existence)
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] git add RELEASE_NOTES.md"
    else
        git add RELEASE_NOTES.md
    fi
fi
run_cmd git commit -m "chore: release $VERSION"

echo "Creating tag $VERSION..."
run_cmd git tag "$VERSION"

echo "Pushing to origin..."
run_cmd git push origin main

if [ "$DRY_RUN" = true ]; then
    echo "Dry run of release $VERSION complete!"
else
    echo "Release $VERSION complete!"
fi
