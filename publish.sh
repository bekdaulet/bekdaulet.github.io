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

# Ask GitHub whether the Pages build for this commit has finished.
REPO_API="https://api.github.com/repos/bekdaulet/bekdaulet.github.io/actions/runs?per_page=3"
for i in $(seq 1 30); do
  sleep 5
  state="$(curl -s "$REPO_API" | python3 -c "
import sys, json
sha = sys.argv[1]
for r in json.load(sys.stdin).get('workflow_runs', []):
    if r['head_sha'].startswith(sha):
        print(r['status'], r['conclusion'] or '')
        break
" "$sha" 2>/dev/null || true)"
  case "$state" in
    "completed success") echo "Live: $SITE"; exit 0 ;;
    completed*)          echo "Build finished with a problem ($state). Check https://github.com/bekdaulet/bekdaulet.github.io/actions"; exit 1 ;;
  esac
done
echo "Pushed, but the build is taking longer than usual. Check https://github.com/bekdaulet/bekdaulet.github.io/actions"
