#!/usr/bin/env bash
set -euo pipefail

# Requires GitHub CLI (gh) and an existing GitHub repo remote.
# This script creates a project board and seeds issues from docs/backlog.md

project_name="CMP Project"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required. Install: https://cli.github.com/" >&2
  exit 1
fi

repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)

echo "Creating project: $project_name"
project_id=$(gh project create --title "$project_name" --format json -q .id)

echo "Linking repository to project"
gh project item-add $project_id --url "https://github.com/$repo"

echo "Seeding issues from docs/backlog.md (if present)"
if [[ -f docs/backlog.md ]]; then
  # Create one issue per top-level heading
  awk '/^# /{if (title){print title}; title=substr($0,3); next} END{print title}' docs/backlog.md | while read -r title; do
    [[ -z "$title" ]] && continue
    issue_url=$(gh issue create --title "$title" --body "Seeded from backlog.md" --repo "$repo" --json url -q .url)
    gh project item-add $project_id --url "$issue_url"
  done
else
  echo "No docs/backlog.md found; skipping issue seeding."
fi

echo "Done. Open your project at:"
owner=$(echo "$repo" | cut -d/ -f1)
proj_num=$(gh project list --owner "$owner" --format json | jq -r --arg title "$project_name" '.[] | select(.title==$title) | .number')
echo "https://github.com/orgs/$owner/projects/$proj_num"
