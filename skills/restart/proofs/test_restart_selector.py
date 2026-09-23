"""PROOF — only HOLDING selects the verb that ends this session.

Ticket 15b80c0c393c, D3. The /restart skill's one new artifact is the branch selector,
and the branch is the whole safety of the skill: `now` kills this Claude Code session
and trusts an inner loop to bring it back, `spawn` kills nothing. So the tooth drives
``selector.branch`` over the shapes a real ``cairn cc restart status`` produces — and
over the shapes a BROKEN one produces, which is where a hollow selector passes.

THE HOLLOW BUILD THIS COULD NOT PASS: ``return "now" if "HOLDING" in text else "spawn"``.
It answers (a), (b), (c) and (d) correctly and fails (e), because a tmux line carrying
the word HOLDING in another position is not a loop holding this session — and reading
it as one is a hang-up.

Run bare: ``python3 skills/restart/proofs/test_restart_selector.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import selector  # noqa: E402 — the sibling module, reached the way skills/saveslate's proof reaches door

PROVES = {"15b80c0c393c": {"all": "test_only_holding_selects_the_session_ending_verb"}}


# The captured shapes. (a) and (b) are the FULL output of `cairn cc restart status`, six
# lines each, as the verb prints them (cairn/devices/cc/0/bin/restart, cmd_status).
_HELD = """instance flags home: /home/akien/.cairn/launchers/superclaude/0
inner loop:          HOLDING (pid 12345)
claude under it:     pid 12346
claude on disk:      1.2.3
standing signals:     none
restarts on record:  4
tmux sessions:       cairn_cc_1: 1 windows
"""

_UNHELD = """instance flags home: <unset -- launched without the restart loop>
inner loop:          NONE -- this session cannot relaunch itself
claude on disk:      1.2.3
tmux sessions:       no tmux server
"""

# (e) the tooth a bare substring search cannot pass: the word appears, in another line.
_WORD_ELSEWHERE = """instance flags home: /home/akien/.cairn/launchers/superclaude/0
inner loop:          NONE -- this session cannot relaunch itself
tmux sessions:       cairn_cc_1: 1 windows (HOLDING)
"""

# (f) the system-word fold: HOLDING is a word the system prints, so it compares folded.
_HELD_LOWER = """instance flags home: /home/akien/.cairn/launchers/superclaude/0
inner loop:          holding (pid 12345)
"""

# (d) garbled: no colon, no newline, non-ascii.
_GARBLED = "\udcff\udcfe binary-ish nonsense with no structure at all ☃"


def test_only_holding_selects_the_session_ending_verb() -> None:
    assert selector.branch(_HELD) == "now", "(a) a HOLDING loop line must select now"
    print("  ok  (a) a held session selects now")

    assert selector.branch(_UNHELD) == "spawn", "(b) a NONE loop line must select spawn"
    print("  ok  (b) an unheld session selects spawn")

    assert selector.branch("") == "spawn", "(c) empty status must select spawn"
    print("  ok  (c) empty status selects spawn")

    assert selector.branch(_GARBLED) == "spawn", "(d) unparseable status must select spawn"
    print("  ok  (d) garbled status selects spawn")

    assert selector.branch(_WORD_ELSEWHERE) == "spawn", (
        "(e) HOLDING outside the loop line must NOT select now — this is the tooth a bare "
        "substring search fails, and failing it is a hang-up")
    print("  ok  (e) the word HOLDING in another line does not select now")

    assert selector.branch(_HELD_LOWER) == "now", "(f) HOLDING folds — it is a system word"
    print("  ok  (f) a lowercase holding still selects now")

    # The two words are the whole range: there is no third answer and no raise.
    for text in (_HELD, _UNHELD, "", _GARBLED, _WORD_ELSEWHERE, _HELD_LOWER):
        assert selector.branch(text) in (selector.NOW, selector.SPAWN)
    print("  ok  (range) every input answers with one of the two words, and none raises")


def main() -> int:
    failed = 0
    for name in sorted(globals()):
        if not name.startswith("test_"):
            continue
        fn = globals()[name]
        if not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as exc:
            print(f"  RED  {name}: {exc}")
            failed += 1
    print("RED" if failed else "GREEN")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
