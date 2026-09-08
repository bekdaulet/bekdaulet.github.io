#!/usr/bin/env bash
# Publish the site: commit every change in this folder and push to GitHub Pages.
#
#   ./publish.sh                    -> asks for a short description of the change
#   ./publish.sh "Added new paper"  -> uses that description directly
#
# Afterwards it waits until the live site reports the new version.

set -euo pipefail
cd "$(dirname "$0")"

SITE="https://bekdaulet.github.io"

if [[ -z "$(git status --porcelain)" ]]; then
  echo "Nothing to publish: no files have changed."
  exit 0
fi

echo "Changed files:"
git status --short
echo

msg="${1:-}"
if [[ -z "$msg" ]]; then
  read -r -p "Describe the change (one line): " msg
fi
if [[ -z "$msg" ]]; then
  msg="Update site $(date '+%Y-%m-%d %H:%M')"
fi

git add -A
git commit -q -m "$msg"
git push -q
sha="$(git rev-parse --short HEAD)"
echo "Pushed commit $sha. Waiting for GitHub Pages to rebuild..."

# GitHub serves the new commit's files once the build finishes; poll the
# page until index.html changes, up to about two minutes.
before="$(curl -s "$SITE/" | md5 2>/dev/null || true)"
for i in $(seq 1 24); do
  sleep 5
  now="$(curl -s "$SITE/" | md5 2>/dev/null || true)"
  if [[ "$now" != "$before" ]]; then
    echo "Live: $SITE"
    exit 0
  fi
done
echo "Pushed, but the live page has not changed yet. Give it another minute: $SITE"
