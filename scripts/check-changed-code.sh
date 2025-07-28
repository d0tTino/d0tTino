#!/usr/bin/env bash
set -euo pipefail

# Determine base commit to compare against
if [ "${EVENT_NAME:-}" = "pull_request" ]; then
    BASE="$BASE_PR"
else
    BASE="${BEFORE:-}"
fi

# Ensure base commit is fetched
if [ -n "$BASE" ]; then
    git fetch origin "$BASE" --depth=1 || true
fi

only_docs_or_comments=true
for file in $(git diff --name-only "$BASE" "${HEAD_SHA:-}" ); do
    if [[ "$file" =~ ^docs/ || "$file" =~ \.md$ ]]; then
        continue
    fi
    diff_lines=$(git diff -U0 "$BASE" "${HEAD_SHA:-}" -- "$file" | grep -E '^[+-]' | grep -vE '^\+\+\+|^---')
    while IFS= read -r line; do
        line="${line:1}"
        trimmed="$(echo "$line" | sed 's/^\s*//')"
        if [[ -z "$trimmed" || "$trimmed" =~ ^(#|//) ]]; then
            continue
        fi
        only_docs_or_comments=false
        break 2
    done <<< "$diff_lines"
done

if [ "$only_docs_or_comments" = false ]; then
    echo "code_changed=true" >> "$GITHUB_OUTPUT"
else
    echo "code_changed=false" >> "$GITHUB_OUTPUT"
fi
