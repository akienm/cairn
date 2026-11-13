#!/bin/bash
# close.sh <id> "<PROVED note>" — commit, push both repos, cross PROVED at codemother's clearance gate,
# cleanup, commit, push. The gate derives the proofs; the note rides the PROVED commit message.
set -u
ID=$1; NOTE=$2; shift 2
C=~/dev/src/cairn; CC=~/dev/src/CairnCommons
X=~/dev/src/cairn/cairn/devices/cc/scripts/sail.py
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: '"${CLAUDE_SESSION_URL:?set CLAUDE_SESSION_URL to the session URL}"
# A commit's pre-commit hook may reseal, and a reseal names every ticket whose hollow it voided
# ("HOLLOW VOIDED"). That line was swallowed here, and the cross below then bounced to FIXME
# (measured 2026-11-13 by akienasus). It is surfaced now, and a void stops the close BEFORE the cross.
VOIDED=0
commit_all() {
  local out; out=$(cd $C && git add -u && git commit -qm "$ID: $1$TRAILER" 2>&1)
  if echo "$out" | grep -q "HOLLOW VOIDED"; then
    echo "$out" | grep -A3 "HOLLOW VOIDED"; VOIDED=1
  fi
  (cd $CC && git add -A tickets/ certificates/ questions/ outline_checks/ berths/ .artifact-journal.jsonl && git commit -qm "$ID: $1" -q >/dev/null 2>&1)
  (cd $C && git pull -q --rebase --autostash && git push -q 2>&1 | tail -1); (cd $CC && git pull -q --rebase --autostash && git push -q 2>&1 | tail -1)
}
commit_all "hollow sealed, verdict"
if [ $VOIDED -ne 0 ]; then
  echo "--- HOLLOW VOIDED by the commit: retake 'bin/cairn test --hollow <id> --seal' for each ticket named, then re-run the verdict and close"; exit 2
fi
# The commit is named for what the gate did, never for what was asked: a commit saying "PROVED"
# over a refused crossing is a false record (2026-11-09).
cd $C && OUT=$(python3 $X cross $ID 2>&1); RC=$?; echo "$OUT" | tail -2
if [ $RC -ne 0 ] || ! echo "$OUT" | grep -q -- '-> \[PROVED\]'; then
  echo "$OUT" | grep -E '^\s*\[|refused|Red|Error' | cut -c1-700 | head -20
  commit_all "PROVED refused at clearance"; echo "--- PROVED REFUSED"; exit 1
fi
cd $C && bin/cairn cleanup 2>&1 | tail -1
commit_all "PROVED — $NOTE"
echo "--- status"; (cd $C && git status --short); (cd $CC && git status --short | head -5)
