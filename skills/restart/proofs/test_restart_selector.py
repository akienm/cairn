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

The same composite tooth also holds the three files the selector is useless without, each
read so its absence reds here (the 2026-09-24 hollow reading found all three unchecked):
(g) SKILL.md orders MEASURE -> SAVE -> HAND OFF, aborts on any slate refusal, and says the
spawn branch kills nothing; (h) the charter parses and names its owner and its proof; (i)
the WATCHME probe is a Probe carrying both carry and enough. The selector is reached at call
time, not import time, so a build reverted to before selector.py reds a tooth instead of
crashing the proof before its first check.

Run bare: ``python3 skills/restart/proofs/test_restart_selector.py``.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

_SKILL = Path(__file__).resolve().parents[1]
_ROOT = _SKILL.parents[1]
sys.path.insert(0, str(_SKILL))
sys.path.insert(1, str(_ROOT))


def _selector():
    """The sibling module, resolved at call time: a build without it reds, never crashes."""
    try:
        return importlib.import_module("selector")
    except ImportError as exc:
        raise AssertionError(f"skills/restart/selector.py is not importable: {exc!r}") from exc

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
    selector = _selector()
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

    skill_md = _SKILL / "SKILL.md"
    assert skill_md.is_file(), "(g) skills/restart/SKILL.md is absent"
    text = skill_md.read_text(encoding="utf-8")
    steps = [text.find(h) for h in ("## 1. MEASURE", "## 2. SAVE", "## 3. HAND OFF")]
    assert -1 not in steps and steps == sorted(steps), f"(g) the steps are not MEASURE, SAVE, HAND OFF in order: {steps}"
    assert "A refusal ABORTS the restart" in text, "(g) the skill does not abort on a slate refusal"
    assert "Nothing dies." in text, "(g) the skill does not say the spawn branch kills nothing"
    print("  ok  (g) the skill orders measure, save, hand off; aborts on refusal; spawn kills nothing")

    charter = _SKILL / "intention+why.json"
    try:
        c = json.loads(charter.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AssertionError(f"(h) the charter does not parse: {exc!r}") from exc
    assert c.get("owner") and c.get("proof") == "skills/restart/proofs/test_restart_selector.py", (
        "(h) the charter does not name its owner and this proof")
    print("  ok  (h) the charter parses and names its owner and its proof")

    try:
        probe_mod = importlib.import_module("cairn.devices.cc.probes.a_restart_leaves_a_slate_behind_it")
        from cairn.tools.base.probe import Probe
    except ImportError as exc:
        raise AssertionError(f"(i) the WATCHME probe is not importable: {exc!r}") from exc
    pr = probe_mod.PROBE
    assert isinstance(pr, Probe) and pr.carry and pr.enough and pr.why, (
        "(i) the probe is not a Probe carrying why, carry and enough")
    print("  ok  (i) the WATCHME probe is a Probe carrying why, carry and enough")


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
