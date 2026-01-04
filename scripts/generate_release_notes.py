import datetime
import sys
import re
from collections import defaultdict

import git


def get_latest_tag():
    try:
        repo = git.Repo(".")
        # Get all tags sorted by creation date, most recent first
        tags = repo.git.tag(sort="-creatordate").splitlines()
        return tags[0] if tags and tags[0] else None
    except (git.InvalidGitRepositoryError, git.GitCommandError):
        return None


def get_commits_since(tag):
    try:
        repo = git.Repo(".")
        if tag:
            # Equivalent to git log tag..HEAD --oneline --reverse
            commits = list(repo.iter_commits(f"{tag}..HEAD", reverse=True))
        else:
            commits = list(repo.iter_commits(reverse=True))

        return [f"{c.hexsha[:7]} {c.summary}" for c in commits]
    except (git.InvalidGitRepositoryError, git.GitCommandError):
        return []


def parse_commits(commits):
    categories = defaultdict(list)
    # Mapping of conventional commit types to release note sections
    type_map = {
        "feat": "New features",
        "fix": "Bug fixes",
        "refactor": "Refactors",
        "chore": "Chores",
        "docs": "Documentation",
        "test": "Tests",
        "perf": "Performance",
        "style": "Style",
        "ci": "CI/CD",
    }

    for commit in commits:
        if not commit:
            continue
        # Format is "hash type(scope): message" or "hash type: message"
        # We want to match conventional commits
        match = re.match(r"^[a-f0-9]+ (\w+)(?:\(([^)]+)\))?:\s*(.+)$", commit)
        if match:
            ctype, scope, msg = match.groups()
            section = type_map.get(ctype, "Misc")
            if scope:
                categories[section].append(f"- {ctype}({scope}): {msg}")
            else:
                categories[section].append(f"- {ctype}: {msg}")
        else:
            # Skip if it doesn't look like a conventional commit or a merge commit
            if "Merge" in commit:
                continue
            # Try to catch simple types like "chore: description"
            parts = commit.split(" ", 1)
            if len(parts) > 1:
                categories["Misc"].append(f"- {parts[1]}")

    return categories


def generate_release_notes(version):
    tag = get_latest_tag()
    commits = get_commits_since(tag)
    # Reversed chronological order as requested (commits are oldest to newest from git log --reverse)
    # So we want them newest to oldest
    commits.reverse()

    categories = parse_commits(commits)

    date = datetime.date.today().strftime("%Y-%m-%d")

    lines = []
    lines.append("## Release Notes")
    lines.append("")
    lines.append(f"Released on {date}")
    lines.append("")

    # Priority order for sections
    order = [
        "New features",
        "Bug fixes",
        "Refactors",
        "Chores",
        "Documentation",
        "Tests",
        "Performance",
        "Misc",
    ]

    for section in order:
        if section in categories and categories[section]:
            lines.append(f"### {section}")
            for item in categories[section]:
                lines.append(item)
            lines.append("")

    # Add sections that are not in the priority order but have commits
    remaining_sections = sorted([s for s in categories.keys() if s not in order])
    for section in remaining_sections:
        if categories[section]:
            lines.append(f"### {section}")
            for item in categories[section]:
                lines.append(item)
            lines.append("")

    lines.append(f"## Install sabdab-cli {version}")
    lines.append("")
    lines.append("```bash")
    lines.append(f"pip install sabdab-cli=={version}")
    lines.append("```")

    return "\n".join(lines).strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_release_notes.py <version>")
        sys.exit(1)

    print(generate_release_notes(sys.argv[1]))
