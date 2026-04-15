#!/bin/bash
# Usage: ./new.sh "My note title"
# Creates a dated markdown file in posts/

TITLE="${1:-untitled}"
DATE=$(date +%Y-%m-%d)
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
FILE="posts/${DATE}-${SLUG}.md"

if [ -f "$FILE" ]; then
  echo "File already exists: $FILE"
  exit 1
fi

cat > "$FILE" << EOF
---
title: ${TITLE}
date: ${DATE}
---

EOF

echo "Created: $FILE"
echo "Edit it, then run ./publish.sh to deploy."

# Open in default editor if $EDITOR is set
if [ -n "$EDITOR" ]; then
  $EDITOR "$FILE"
fi
