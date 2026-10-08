This section is standing. It holds for every code-seam ticket, and a step it answers is settled, not a gap. Where a ticket's own decision lines say something different, the ticket governs.

1. COMMITS. A voyage makes three commits in ~/dev/src/cairn, in this order, each with `git commit -F <message file>` staging named paths only:
   - the proof commit stages only the ticket's proof files. Message: `<ticket id>: proof — <ticket title>`.
   - the build commit stages the ticket's writes_to files, never a proof. Message: `<ticket id>: build — <ticket title>`. The pre-commit hook reseals the component's proofs and stages their validation records into this same commit; that is expected, and the builder does not unstage them.
   - the seal commit, after sealing, stages the validation records and the component's history.json, state.json and .artifact-journal.jsonl. Message: `<ticket id>: seal — <ticket title>`.
   Every commit message ends with one blank line and then the session's attribution trailer lines (Co-Authored-By and Claude-Session). The builder holds those lines for its session, so they are settled, not a gap.

2. RECORDS BETWEEN DOORS. Every crossing (BUILDME, PROVEME) and every seal writes records:
   - in CairnCommons: .artifact-journal.jsonl and the ticket;
   - in cairn: .artifact-journal.jsonl and the component's history.json and state.json.
   Commit them in both repos before the next door. A crossing over a dirty tree is refused.

3. RUN AND SEAL. From ~/dev/src/cairn:
   - run a proof with `bin/cairn test --exec "<venv python3> <proof>"`;
   - seal with `bin/cairn test --seal <proof>`, one proof per command.
   Every proof of the touched component is resealed and must land green.

4. PREDICT. Type it in full; never run it from a session-scratchpad script. From ~/dev/src/cairn, with A = the proof commit and B = the build commit:
   1. `W=$(mktemp -d /tmp/claude-1000/bare.XXXX)`, then `git worktree add -q --detach $W B`.
   2. Count the CairnCommons siblings with `ls $(dirname $W) | grep -c ^CairnCommons$`. It must print 0, or the predict does not count.
   3. In $W, run the proof with `PYTHONPATH=.`. It is green.
   4. Restore each writes_to file from A with `git checkout A -- <path>`. A file that is new in the build is removed instead with `git rm -q <path>`. Keep every `rm` and `git rm` in a command of its own: a command that also names the ~/.cairn venv is refused by the delete gate.
   5. Run the proof again. The teeth the ticket names go red.
   6. Clean up with `git worktree remove --force $W` and then `git worktree prune`.

5. PROVEME. Run `PYTHONPATH=. <venv python3> -m cairn.tools.base.cross <ticket id> PROVEME --actor cc --why "<what was measured: the teeth green as built, the predict's reds, the seals>" --proven-by <proof path, repo-relative>`.
   The --why states the measured results. If a result differs from what the ticket predicts, the builder does not cross. It reports the actual result instead.

6. HOLLOW. After PROVEME, run `bin/cairn test --hollow <ticket id> --seal`. It reverts the writes_to files and must red the teeth the ticket names. Commit its records.

7. PROVED. Push both repos first. Then:
   1. Call cairn.devices.codemother.machines.verdict.verdict.write_verdict with:
      - ticket;
      - validate_ref: the claiming validate berth, which is the chart chain's validate stage;
      - verdicts: one per criterion of that berth, in its order. Each copies the criterion's claim, instrument, expect_exit and timeout_s verbatim and adds outcome, discriminating_observation (the measured red before and green after, with commit hashes) and evidence;
      - dispositions: one per hypothesis piece of the berth's hypothesize_ref, with the piece named verbatim, disposition 'confirmed' and by 'cc'.
   2. Call cairn.devices.cairn.machines.harbor_master.clearance.clear to PROVED, with proven_by and the component's history and state paths.
   3. Write the moved cursor back to the ticket through cairn.tools.artifact.artifact.write, verb 'cast'.
   4. Commit and push both repos.
