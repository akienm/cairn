"""The /restart skill's branch selector — which relaunch verb this session may fire.

Ticket 15b80c0c393c, D2. The skill is three steps (measure, save, hand off) and the
FIRST one decides the third: `cairn cc restart status` prints what is behind this
session, and what is behind it decides whether the session may end itself.

WHY THIS IS CODE AND NOT A SENTENCE IN SKILL.md. The branch is the whole safety of
the skill — get it wrong and a session ends with nothing behind it to bring it back,
which is a hang-up and the one failure this skill must never cause. A branch condition
that lives only in prose is a branch nobody can red, so it lives here, where a proof
drives it (skills/restart/proofs/test_restart_selector.py).

THE RULE, AND IT IS ASYMMETRIC ON PURPOSE (this ticket's third constraint, verbatim:
"Match on HOLDING, and treat every other status output as NONE"). ``now`` — the verb
that KILLS this session and trusts a loop to bring it back — is returned only on a
positive, structured match: a line whose content begins ``inner loop:`` and whose
remainder begins with the word HOLDING. EVERYTHING else returns ``spawn``: no loop
line, a loop line saying NONE, an empty string, unparseable bytes, a status command
that failed and printed its error instead. There is no third return value and no
exception path — an unreadable status is not an error to raise, it is the safe
branch, because the safe branch is the one that kills nothing.

HOLDING folds (ruled 2026-09-07): it is a word the system PRINTS, so it compares
through ``cairn.tools.system_word.fold``. His own free text never folds; this is not
his text, it is ours.
"""

from __future__ import annotations

from cairn.tools.system_word import fold

#: The verb a session may fire on itself only when a loop is demonstrably behind it.
NOW = "now"
#: The verb that kills nothing — a second instance stood up beside this one.
SPAWN = "spawn"

#: The status line that decides the branch, and the word that decides it. Named here
#: so the proof and the prose cannot drift to two spellings of one string.
LOOP_LINE_PREFIX = "inner loop:"
HOLDING = "HOLDING"


def branch(status_text: str) -> str:
    """``"now"`` iff ``status_text`` shows a loop HOLDING this session; ``"spawn"`` otherwise.

    ``status_text`` is the captured stdout of ``cairn cc restart status``. Anything at
    all may be passed — None-ish, empty, binary-ish, a traceback — and the answer is
    still one of the two words.
    """
    try:
        lines = str(status_text).splitlines()
    except Exception:          # noqa: BLE001 — an unrenderable status is still the safe branch
        return SPAWN
    prefix = fold(LOOP_LINE_PREFIX)
    for line in lines:
        content = line.strip()
        if fold(content).startswith(prefix):
            remainder = content[len(LOOP_LINE_PREFIX):].strip()
            head = remainder.split()[0] if remainder.split() else ""
            if fold(head) == fold(HOLDING):
                return NOW
            # A loop line that does not say HOLDING settles nothing by itself; the scan
            # goes on, and falls through to SPAWN if no loop line ever says it. What the
            # scan will NOT do is read the word out of any other line — clause (e) of the
            # proof is exactly the `tmux sessions: ... (HOLDING)` a bare substring search
            # would promote.
    return SPAWN


if __name__ == "__main__":
    import sys
    print(branch(sys.stdin.read()))
