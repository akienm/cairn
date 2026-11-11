#!/bin/bash
# prove.sh <id> <reflection.json> <proof> — reflection, seal, commit both repos, cross PROVEME at
# codemother's clearance gate (it derives the proofs from their PROVES), commit, hollow --seal.
set -u
ID=$1; REFL=$2; P=$3; shift 3
C=~/dev/src/cairn; CC=~/dev/src/CairnCommons
X=~/dev/src/cairn/cairn/devices/cc/scripts/sail.py
TR=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: '"${CLAUDE_SESSION_URL:?set CLAUDE_SESSION_URL to the session URL}"
commit_all() {
  (cd $C && git add -u && git commit -qm "$ID: $1$TR" 2>&1 | grep -E " red |FAIL|REFUSED" )
  (cd $CC && git add -A tickets/ certificates/ questions/ outline_checks/ .artifact-journal.jsonl && git commit -qm "$ID: $1" -q >/dev/null 2>&1)
}
cd $C
echo "--- reflection"; PYTHONPATH=. python3 -m skills.sail.reflection $REFL 2>&1 | tail -1
echo "--- seal"; bin/cairn test --seal $P 2>&1 | grep -E "proof ·"
git add $(dirname $(dirname $P))/validations 2>/dev/null
commit_all "proof sealed"
echo "--- PROVEME"; python3 $X cross $ID 2>&1 | tail -1
commit_all "PROVEME"
(cd $C && git status --short); (cd $CC && git status --short | head -3)
echo "--- hollow"; timeout 1500 bin/cairn test --hollow $ID --seal 2>&1 | tail -4
