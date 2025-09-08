#!/bin/bash

BRANCH="$1"

if [ -z "$BRANCH" ]; then
    echo "Usage: $0 <branch-name>"
    exit 1
fi

git checkout "$BRANCH" && \
git pull origin "$BRANCH" && \
git merge master && \
npx prettier --write *.md && \
git add . && \
git commit -m "lint" && \
git push origin "$BRANCH"
