#!/bin/bash
# prove.sh <id> <reflection.json> <proof> — reflection, seal, commit both repos, cross PROVEME at
# codemother's clearance gate (it derives the proofs from their PROVES), commit, hollow --seal.
# Exit 5 = a commit did not land ("NOT COMMITTED:" names its paths); it stops before the next step.
# Exit 6 = the hollow did not finish ("HOLLOW DID NOT FINISH (exit N)"): no reading yet, not red (ae531c6b49db).
set -u
ID=$1; REFL=$2; P=$3; shift 3
C=~/dev/src/cairn; CC=~/dev/src/CairnCommons
X=~/dev/src/cairn/cairn/devices/cc/scripts/sail.py
TR=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: '"${CLAUDE_SESSION_URL:?set CLAUDE_SESSION_URL to the session URL}"
commit_all() {
  # the house stages only the seals this ticket's step wrote, never 'git add -u' (91908f3b3bb3)
  (cd $C && N=$(python3 $C/cairn/devices/cc/scripts/house_paths.py $ID $CC) && [ -n "$N" ] && git add -- $N \
     && git commit -qm "$ID: $1$TR" -- $N 2>&1 | grep -E " red |FAIL|REFUSED|HOLLOW VOIDED|will bounce on hollow" )
  # the commons stages only this ticket's records, never another session's (d3b8cdf81a41)
  (cd $CC && N=$(python3 $C/cairn/devices/cc/scripts/commons_paths.py $ID) && [ -n "$N" ] && git add -- $N && git commit -qm "$ID: $1$TR" -q -- $N >/dev/null 2>&1)
  # read whether the commits landed: the step's own paths left dirty mean one did not (979a63671481);
  # the shared journal is left out, since another hand's door write dirties it
  local left
  left=$( (cd $C && python3 $C/cairn/devices/cc/scripts/house_paths.py $ID $CC; cd $CC && python3 $C/cairn/devices/cc/scripts/commons_paths.py $ID) | grep -vx '\.artifact-journal\.jsonl')
  if [ -n "$left" ]; then echo "NOT COMMITTED: $(echo $left | cut -c1-300)"; return 1; fi
}
cd $C
echo "--- reflection"; PYTHONPATH=. python3 -m skills.sail.reflection $REFL 2>&1 | tail -1
echo "--- seal"; bin/cairn test --seal $P 2>&1 | grep -E "proof ·|HOLLOW VOIDED|will bounce on hollow"
commit_all "proof sealed" || exit 5
echo "--- PROVEME"; python3 $X cross $ID 2>&1 | tail -1
commit_all "PROVEME" || exit 5
(cd $C && git status --short); (cd $CC && git status --short | head -3)
# no wall-clock bound of its own: the hollow verb bounds each proof run (cairn/devices/tester/hollow.py)
echo "--- hollow"; bin/cairn test --hollow $ID --seal 2>&1 | tail -4
H=${PIPESTATUS[0]}
if [ "$H" -ne 0 ]; then echo "HOLLOW DID NOT FINISH (exit $H)"; exit 6; fi
