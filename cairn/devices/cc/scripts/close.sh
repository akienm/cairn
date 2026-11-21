#!/bin/bash
# close.sh <id> "<PROVED note>" — commit, push both repos, cross PROVED at codemother's clearance gate,
# cleanup, commit, push. The gate derives the proofs; the note rides the PROVED commit message.
# Exit 0 = PROVED; 1 = refused; 2 = hollow voided; 3 = clearance unanswered; 4 = a crossing accepted short of PROVED;
# 5 = a repo not committed or not pushed ("NOT PUSHED:"/"NOT COMMITTED:" names it), printed before any crossing line.
set -u
ID=$1; NOTE=$2; shift 2
C=~/dev/src/cairn; CC=~/dev/src/CairnCommons
X=~/dev/src/cairn/cairn/devices/cc/scripts/sail.py
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: '"${CLAUDE_SESSION_URL:?set CLAUDE_SESSION_URL to the session URL}"
# A commit's pre-commit hook may reseal, and a reseal names every ticket whose hollow it voided
# ("HOLLOW VOIDED"). That line was swallowed here, and the cross below then bounced to FIXME
# (measured 2026-11-13 by akienasus). It is surfaced now, and a void stops the close BEFORE the cross.
VOIDED=0
# Every commit, pull and push is read, never piped away (979a63671481). Measured 2026-11-20 closing
# 380d524e6e9c: the commons pull failed ('fatal: Cannot rebase onto multiple branches.'), the push was
# refused, nothing read either status, and the close printed CROSSED and exited 4 five commits ahead.
sync_repo() {
  local d=$1 out rc ahead
  out=$(cd "$d" && $C/bin/cairn artifact quiet -- git pull -q --rebase --autostash 2>&1); rc=$?
  if [ $rc -ne 0 ]; then
    # a stopped rebase would leave the tree mid-rewrite under every later door write: undo it
    (cd "$d" && [ -d "$(git rev-parse --git-path rebase-merge)" ] \
       && $C/bin/cairn artifact quiet -- git rebase --abort >/dev/null 2>&1)
  else
    out=$(cd "$d" && git push -q 2>&1); rc=$?
  fi
  ahead=$(cd "$d" && git rev-list --count '@{u}..HEAD' 2>&1) || { rc=1; out="$ahead"; }
  if [ $rc -ne 0 ] || [ "$ahead" != 0 ]; then
    echo "NOT PUSHED: $d: $(echo "$out" | grep -v '^[[:space:]]*$' | tail -1)${ahead:+ ($ahead commit(s) not on origin)}"
    return 1
  fi
}
commit_all() {
  # the house stages only the seals this ticket's step wrote, never 'git add -u' over another hand's edits (91908f3b3bb3)
  local out; out=$(cd $C && N=$(python3 $C/cairn/devices/cc/scripts/house_paths.py $ID $CC) && [ -n "$N" ] && git add -- $N && git commit -qm "$ID: $1$TRAILER" -- $N 2>&1)
  if echo "$out" | grep -q "HOLLOW VOIDED"; then
    echo "$out" | grep -A3 "HOLLOW VOIDED"; VOIDED=1
  fi
  # the commons stages only this ticket's records, never another session's (d3b8cdf81a41)
  (cd $CC && N=$(python3 $C/cairn/devices/cc/scripts/commons_paths.py $ID) && [ -n "$N" ] && git add -- $N && git commit -qm "$ID: $1" -q -- $N >/dev/null 2>&1)
  # A commit that did not land leaves the step's own paths dirty: read that, not the exit of a chain
  # whose empty selection also exits 1. The shared journal is left out: another hand's door write dirties it.
  local left rc=0
  left=$( (cd $C && python3 $C/cairn/devices/cc/scripts/house_paths.py $ID $CC; cd $CC && python3 $C/cairn/devices/cc/scripts/commons_paths.py $ID) | grep -vx '\.artifact-journal\.jsonl')
  if [ -n "$left" ]; then echo "NOT COMMITTED: $(echo $left | cut -c1-300)"; rc=1; fi
  # The pull runs under the door lock: an autostash cannot interleave with a door write (0f8aefbba1d0).
  sync_repo $C || rc=1
  sync_repo $CC || rc=1
  return $rc
}
commit_all "hollow sealed, verdict" || exit 5
if [ $VOIDED -ne 0 ]; then
  echo "--- HOLLOW VOIDED by the commit: retake 'bin/cairn test --hollow <id> --seal' for each ticket named, then re-run the verdict and close"; exit 2
fi
# The commit is named for what the gate did, never for what was asked: a commit saying "PROVED"
# over a refused crossing is a false record (2026-11-09).
cd $C && OUT=$(python3 $X cross $ID 2>&1); RC=$?; echo "$OUT" | tail -2
if [ $RC -eq 3 ]; then
  commit_all "clearance unanswered" || exit 5; echo "--- CLEARANCE UNANSWERED: the gate may still cross it; read the cursor with: cairn codemother show artifact $ID"; exit 3
fi
if [ $RC -ne 0 ] || ! echo "$OUT" | grep -q -- '-> \[PROVED\]'; then
  echo "$OUT" | grep -E '^\s*\[|refused|Red|Error' | cut -c1-700 | head -20
  # The subject names the crossing the gate answered, read from sail.py's own words (60ca4c6a9b50).
  if [ $RC -eq 0 ]; then
    T=$(echo "$OUT" | grep -o '\[[A-Z]\+' | tail -1 | tr -d '[')
    commit_all "${T:-a phase} crossed at clearance, not yet PROVED" || exit 5; echo "--- CROSSED TO ${T:-a phase}, NOT YET PROVED: close again to climb"; exit 4
  fi
  T=$(echo "$OUT" | grep -o "refused $ID at [A-Z]\+" | tail -1 | awk '{print $NF}')
  if [ "$T" = PROVED ]; then commit_all "PROVED refused at clearance" || exit 5; else commit_all "${T:-the crossing} refused at clearance" || exit 5; fi
  echo "--- ${T:-CROSSING} REFUSED"; exit 1
fi
cd $C && bin/cairn cleanup 2>&1 | tail -1
commit_all "PROVED — $NOTE" || exit 5
echo "--- status"; (cd $C && git status --short); (cd $CC && git status --short | head -5)
