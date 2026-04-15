#!/bin/bash
# Usage: ./publish.sh ["commit message"]
# Builds the site and pushes to GitHub.

set -e

MSG="${1:-update notes}"

echo "Building..."
python3 build.py

echo "Committing..."
git add -A
git commit -m "$MSG" || echo "Nothing to commit."

echo "Pushing..."
git push

echo "Done. Site will deploy via GitHub Actions shortly."
