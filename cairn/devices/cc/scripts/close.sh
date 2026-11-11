#!/bin/bash
# close.sh <id> "<PROVED note>" — commit, push both repos, cross PROVED at codemother's clearance gate,
# cleanup, commit, push. The gate derives the proofs; the note rides the PROVED commit message.
set -u
ID=$1; NOTE=$2; shift 2
C=~/dev/src/cairn; CC=~/dev/src/CairnCommons
X=~/dev/src/cairn/cairn/devices/cc/scripts/sail.py
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: '"${CLAUDE_SESSION_URL:?set CLAUDE_SESSION_URL to the session URL}"
commit_all() {
  (cd $C && git add -u && git commit -qm "$ID: $1$TRAILER" >/dev/null 2>&1)
  (cd $CC && git add -A tickets/ certificates/ questions/ outline_checks/ .artifact-journal.jsonl && git commit -qm "$ID: $1" -q >/dev/null 2>&1)
  (cd $C && git push -q 2>&1 | tail -1); (cd $CC && git push -q 2>&1 | tail -1)
}
commit_all "hollow sealed, verdict"
# The commit is named for what the gate did, never for what was asked: a commit saying "PROVED"
# over a refused crossing is a false record (2026-11-09).
cd $C && OUT=$(python3 $X cross $ID 2>&1); RC=$?; echo "$OUT" | tail -2
if [ $RC -ne 0 ] || ! echo "$OUT" | grep -q -- '-> \[PROVED\]'; then
  commit_all "PROVED refused at clearance"; echo "--- PROVED REFUSED"; exit 1
fi
cd $C && bin/cairn cleanup 2>&1 | tail -1
commit_all "PROVED — $NOTE"
echo "--- status"; (cd $C && git status --short); (cd $CC && git status --short | head -5)
