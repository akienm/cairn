#!/bin/bash
# revert_build.sh <pre-build-commit> <build-file...> — run in the tree to revert (preflight's worktree).
# Per file: a file the pre-build commit holds goes back to its pre-build bytes; a file it does not hold
# (added by the build) is removed. Per file, because one checkout over the whole list fails whole on an
# added file and left the changed files at HEAD (measured 2026-11-18, ticket b7068b1ba431; 3f515c7e1d31).
set -u
PRE=$1; shift
for f in "$@"; do
  if git cat-file -e "$PRE:$f" 2>/dev/null; then
    git checkout -q "$PRE" -- "$f" || { echo "revert_build: checkout of $f at $PRE failed" >&2; exit 1; }
  else
    rm -f -- "$f"
  fi
done
