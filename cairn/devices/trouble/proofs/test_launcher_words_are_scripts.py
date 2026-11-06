#!/usr/bin/env python3
"""Proof for ticket 285a8f3f7599 — trouble's launcher words become scripts in its bin.

Measured 2026-11-05: cairn/devices/trouble/0/bin/trouble dispatched live, clear and drain in a
case statement. Under parent 41a70e789682 a word with no script in the device's bin goes onto
the bus, so those three would be stranded. Akien 2026-11-05 (Q#27, outline 8.4): "if there's a
script for it, run it, else get on the bus". Teeth, one per falsifier clause:

  1. live, clear, drain are each an executable in cairn/devices/trouble/0/bin whose first
     comment line names it ('# cairn trouble <word> — <what>');
  2. `live --json` prints the same troubles the store holds, over a scratch store: through the
     script itself and through the launcher (a word with a sibling script is handed to it), each
     equal to the store tool's own live() read in a process over the same HOME;
  3. the launcher carries no case arm for any of the three words, and none of their bodies.

Scratch HOME only — no live bus, no live store.

    python3 cairn/devices/trouble/proofs/test_launcher_words_are_scripts.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_BIN = _REPO / "cairn" / "devices" / "trouble" / "0" / "bin"
WORDS = ("live", "clear", "drain")

PROVES = {"285a8f3f7599": {
    "1": "clause_1_each_word_is_a_named_script",
    "2": "clause_2_live_json_prints_the_same_troubles",
    "3": "clause_3_the_launcher_has_no_arm_for_the_words",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:1200]}", flush=True)
    if not ok:
        FAILURES.append(name)


def _first_comment(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line.startswith("#"):
            return line
        if line.strip():
            break
    return ""


def clause_1_each_word_is_a_named_script() -> None:
    lacks = []
    for word in WORDS:
        p = _BIN / word
        if not p.is_file():
            lacks.append(f"{word}: no script")
            continue
        if not os.access(p, os.X_OK):
            lacks.append(f"{word}: not executable")
        first = _first_comment(p)
        if not re.match(rf"^# cairn trouble {word} — \S", first):
            lacks.append(f"{word}: first comment line is {first!r}")
    check("clause_1_each_word_is_a_named_script", not lacks, "; ".join(lacks))


def _trouble(ident: str, standing: str = "OPEN") -> dict:
    return {"id": ident, "standing": standing, "why": f"a 285a proof's trouble ({ident})", "count": 2,
            "first_seen": "2026-11-05T00:00:00+00:00", "last_seen": "2026-11-05T00:01:00+00:00",
            "occurrences": [{"at": "2026-11-05T00:00:00+00:00"}], "notified": ["cc"],
            "cleared_by": [], "recurred_after_clear": None, "prior_attempts": 0}


def _put(folder: Path, t: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{t['id']}.json").write_text(json.dumps(t, indent=2) + "\n", encoding="utf-8")


_REFERENCE = (
    "import json, sys\n"
    f"sys.path.insert(0, {str(_REPO)!r})\n"
    "from cairn.devices.trouble.tools.store import store\n"
    "print(json.dumps(store.live()))\n")


def clause_2_live_json_prints_the_same_troubles() -> None:
    from cairn.tools.base.address import log_path
    with tempfile.TemporaryDirectory(prefix="285a-live-") as d:
        home = Path(d) / "home"
        roots = {"repo": _REPO, "commons": _REPO.parent / "CairnCommons", "instance": home / ".cairn"}
        store = log_path("cairn", 0, roots) / "troubletickets"
        _put(store, _trouble("285a-proof-a"))
        _put(store, _trouble("285a-proof-b"))
        _put(store / "cleared", _trouble("285a-proof-gone", standing="CLEARED"))
        env = {**os.environ, "HOME": str(home), "PYTHONPATH": str(_REPO)}

        def run(argv):
            return subprocess.run(argv, capture_output=True, text=True, env=env, cwd=str(_REPO),
                                  timeout=180)

        lacks = []
        script = _BIN / "live"
        outs = {}
        if script.is_file():
            outs["bin/live"] = run(["bash", str(script), "--json"])
        else:
            lacks.append("bin/live absent")
        outs["bin/trouble live"] = run(["bash", str(_BIN / "trouble"), "live", "--json"])
        ref = run([sys.executable, "-c", _REFERENCE])
        try:
            want = json.loads(ref.stdout)
        except ValueError:
            want = None
            lacks.append(f"reference read failed rc={ref.returncode} {ref.stderr[-400:]!r}")
        if want is not None and sorted(t.get("id") for t in want) != ["285a-proof-a", "285a-proof-b"]:
            lacks.append(f"reference reads {[t.get('id') for t in want]}")
        for name, r in outs.items():
            try:
                got = json.loads(r.stdout)
            except ValueError:
                lacks.append(f"{name}: rc={r.returncode} not json: {(r.stdout + r.stderr)[-300:]!r}")
                continue
            if r.returncode != 0 or got != want:
                lacks.append(f"{name}: rc={r.returncode} ids={[t.get('id') for t in got]}")
    check("clause_2_live_json_prints_the_same_troubles", not lacks, "; ".join(lacks))


def clause_3_the_launcher_has_no_arm_for_the_words() -> None:
    text = (_BIN / "trouble").read_text(encoding="utf-8")
    lacks = []
    for word in WORDS:
        if re.search(rf"^\s*[^#\n]*\b{word}\)\s*$", text, re.M) or re.search(
                rf"^\s*[(]?[\w|]*\b{word}\b[\w|]*\)", text, re.M):
            lacks.append(f"a case arm names {word!r}")
    for body in ("store.live()", "clear_trouble(", "pending_before"):
        if body in text:
            lacks.append(f"the launcher still carries {body!r}")
    check("clause_3_the_launcher_has_no_arm_for_the_words", not lacks, "; ".join(lacks))


def main() -> int:
    os.chdir(_REPO)
    print("285a8f3f7599 — trouble's launcher words become scripts in its bin")
    for tooth in (clause_1_each_word_is_a_named_script, clause_2_live_json_prints_the_same_troubles,
                  clause_3_the_launcher_has_no_arm_for_the_words):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
