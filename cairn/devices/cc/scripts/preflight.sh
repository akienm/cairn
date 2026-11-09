#!/bin/bash
# preflight.sh <component> <pre-build-commit> <proof> <build-file...>
# Before PROVEME: (1) build_inspector over the component, minus the findings a commit/seal clears;
# (2) the proof in a commons-less git worktree at HEAD (expect green) and with the build files
# reverted to <pre-build-commit> (expect the declared teeth red). Run after the build is COMMITTED.
set -u
COMP=$1; PRE=$2; PROOF=$3; shift 3
cd ~/dev/src/cairn
echo "--- build_inspector($COMP), real findings only"
PYTHONPATH=. python3 -c "
from cairn.machines.build_inspector import inspector as bi
r=bi.inspect(component='$COMP')
skip=('component_color','history_integrity','working_tree_clean')
for m in r['gate'].get('mismatches',[]):
    if m['identity'] in skip: continue
    for f in m['values'].get('findings',[m]): print(' ', m['identity'], '|', f.get('about'), f.get('values',''))
print('  (gate', r['gate']['passed'], 'of', r['gate']['checks'], ')')"
WT=$(mktemp -d)
rm -rf $WT; git worktree prune; git worktree add -q --detach $WT/cairn HEAD
echo "--- worktree at HEAD"; (cd $WT/cairn && PYTHONPATH=. timeout 900 python3 $PROOF 2>&1 | grep -E "PASS|FAIL|passed|failed|ok  " | tail -12)
(cd $WT/cairn && git checkout -q $PRE -- "$@" 2>/dev/null || for f in "$@"; do git cat-file -e $PRE:$f 2>/dev/null || rm -f $f; done)
echo "--- worktree with build reverted to $PRE"; (cd $WT/cairn && PYTHONPATH=. timeout 900 python3 $PROOF 2>&1 | grep -E "PASS|FAIL|passed|failed|ok  " | tail -12)
git worktree remove --force $WT/cairn
