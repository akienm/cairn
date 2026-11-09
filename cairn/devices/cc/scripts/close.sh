#!/bin/bash
# close.sh <id> "<PROVED note>" <proof...> — commit, push both repos, cross PROVED, cleanup, commit, push.
set -u
ID=$1; NOTE=$2; shift 2
C=~/dev/src/cairn; CC=~/dev/src/CairnCommons
X=~/dev/src/cairn/cairn/devices/cc/scripts/cross.py
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: '"${CLAUDE_SESSION_URL:?set CLAUDE_SESSION_URL to the session URL}"
commit_all() {
  (cd $C && git add -u && git commit -qm "$ID: $1$TRAILER" >/dev/null 2>&1)
  (cd $CC && git add -A tickets/ certificates/ questions/ outline_checks/ .artifact-journal.jsonl && git commit -qm "$ID: $1" -q >/dev/null 2>&1)
  (cd $C && git push -q 2>&1 | tail -1); (cd $CC && git push -q 2>&1 | tail -1)
}
commit_all "hollow sealed, verdict"
cd $C && PYTHONPATH=. python3 $X $ID PROVED "$NOTE" "$@" 2>&1 | tail -2
cd $C && bin/cairn cleanup 2>&1 | tail -1
commit_all "PROVED"
echo "--- status"; (cd $C && git status --short); (cd $CC && git status --short | head -5)
