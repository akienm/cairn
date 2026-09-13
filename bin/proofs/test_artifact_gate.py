"""Proof for the artifact PreToolUse gate — the friction in front of the artifact door.

The door's commit check is the physics (cairn/tools/artifact/proofs/test_artifact_door.py);
``bin/cmd/artifactgate`` refuses an Edit/Write/Bash aimed at a record of truth at the tool
call, so CC learns at one retype rather than at a park. Teeth a hollow gate could not pass:

  - A WRITE TOOL AIMED AT A RECORD IS REFUSED, in both roots and for every record class the
    jurisdiction declares — read from the jurisdiction, so a class added there is gated
    here without a second spelling.
  - A WRITE TOOL AIMED AT CODE, PROSE, OR A DERIVED SURFACE IS ALLOWED. A gate that fires
    on artifact.py itself is a wall.
  - A BASH READ OF A RECORD IS ALLOWED, redirects included: `cat <record> > /tmp/x` and
    `grep ... tickets/ 2>&1 | head` are the commonest honest shapes.
  - A BASH WRITE INTO A RECORD IS REFUSED: a redirect whose TARGET is a record, sed -i,
    cp/mv/rm, write_text, json.dump, open(..., "w").
  - THE DOOR IS NOT REFUSED: `cairn artifact ...`, a skill door, `cairn ruling`.
  - THE REFUSAL CARRIES THE WAY THROUGH.
  - THE HOOK CONTRACT: exit 2 with the refusal on stderr; exit 0 to allow; unreadable
    stdin allows and says so.

    python3 bin/proofs/test_artifact_gate.py     # exit 0 = green
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_GATE = _REPO_ROOT / "bin" / "cmd" / "artifactgate"

# The declared tooth for the artifact-door ticket: the PreToolUse gate is the build-time half
# of clause (1) — a hand edit to a record is refused before the commit question ever sees it.
PROVES = {"30531f6e1c5d": {"gate": "test_the_pretooluse_gate_refuses_a_write_to_a_record",
                           "wired": "test_the_gate_is_wired_at_pretooluse_for_every_writing_tool"}}
_COMMONS = _REPO_ROOT.parent / "CairnCommons"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_loader(
        name, importlib.machinery.SourceFileLoader(name, str(path)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The subject is bound at CALL time, never at import: the hollow reading takes
# bin/cmd/artifactgate away and reruns this proof; an absent subject reds both declared
# teeth instead of crashing the reader.
gate = None
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _red_every_declared_tooth(reason: str) -> None:
    for name in PROVES["30531f6e1c5d"].values():
        if name not in FAILURES:
            check(name, False, reason)


def main() -> int:
    global gate
    if not _GATE.exists():
        print(f"the subject {_GATE} is absent")
        _red_every_declared_tooth("subject absent")
        return 1
    try:
        gate = _load(_GATE, "artifactgate")
        return _teeth()
    except Exception as exc:  # noqa: BLE001 — a subject whose world was taken away
        print(f"the teeth could not run to the end: {exc!r}")
        _red_every_declared_tooth(f"aborted: {type(exc).__name__}")
        return 1


def _teeth() -> int:
    print("WRITE TOOLS")
    for rel in ("tickets/x.json", "troubles/x.json", "decisions/x.json", "slates/x.json",
                "ideas/x.json", "questions/x.json", "adjudications/x.json"):
        check(f"Write to CairnCommons/{rel} is refused",
              gate.verdict("Write", {"file_path": str(_COMMONS / rel)}) is not None)
    for rel in ("cairn/tools/x/state.json", "cairn/tools/x/history.json",
                "cairn/tools/x/intention+why.json", "cairn/tools/x/validations/test_x.json",
                "cairn/tools/artifact/jurisdiction.json"):
        check(f"Edit of {rel} is refused",
              gate.verdict("Edit", {"file_path": str(_REPO_ROOT / rel)}) is not None)
    check("MultiEdit of a ticket is refused",
          gate.verdict("MultiEdit", {"file_path": str(_COMMONS / "tickets" / "a.json")}) is not None)
    for rel in ("cairn/tools/artifact/artifact.py", "CLAUDE.md", "bin/cmd/artifactgate",
                "cairn/tools/x/proofs/test_x.py"):
        check(f"Write to {rel} is allowed", gate.verdict("Write", {"file_path": str(_REPO_ROOT / rel)}) is None)
    for rel in ("intentions-congruency-lab/x.json", "node_classes/x.json", "notes/x.md",
                "intentions-not-beside-code/I-x.md"):
        check(f"Write to CairnCommons/{rel} is allowed (not a record yet)",
              gate.verdict("Write", {"file_path": str(_COMMONS / rel)}) is None)
    check("a Write outside both roots is allowed",
          gate.verdict("Write", {"file_path": "/tmp/scratch/tickets/x.json"}) is None)
    r = gate.verdict("Write", {"file_path": str(_COMMONS / "tickets" / "x.json")})
    check("the refusal carries the way through", "cairn artifact hand-edit" in r and "--verb" in r)

    print("BASH")
    allowed = [
        "cat CairnCommons/tickets/x.json > /tmp/y",
        "grep -rn foo CairnCommons/tickets/ 2>&1 | head",
        "cat ../CairnCommons/troubles/a.json | python3 -c 'import sys,json;print(len(sys.stdin.read()))'",
        "git -C ../CairnCommons commit -am x && git push",
        "bin/cairn artifact write ../CairnCommons/tickets/x.json --verb cast --why x --from /tmp/p",
        "bin/cairn artifact hand-edit cairn/tools/x/state.json --why 'x'",
        "PYTHONPATH=. python3 skills/sorted/door.py /tmp/packet.json",
        "bin/cairn ruling open /tmp/ruling.json",
        "ls cairn/tools/x/validations/",
        "python3 - <<EOF\nopen('cairn/tools/x/x.py','w').write('')\nEOF",
    ]
    for c in allowed:
        check(f"allowed: {c[:70]!r}", gate.verdict("Bash", {"command": c}) is None)
    refused = [
        "echo {} > ../CairnCommons/tickets/x.json",
        "python3 gen.py >> cairn/tools/x/history.json",
        "sed -i s/a/b/ cairn/tools/x/intention+why.json",
        "cp /tmp/x.json CairnCommons/decisions/2026-x.json",
        "mv CairnCommons/tickets/a.json CairnCommons/tickets/b.json",
        "rm CairnCommons/slates/2026-x.json",
        "python3 - <<EOF\nopen(\"cairn/tools/x/state.json\",\"w\").write(\"{}\")\nEOF",
        "python3 -c \"import json;json.dump({}, open('CairnCommons/ideas/x.json','w'))\"",
        "python3 -c \"from pathlib import Path; Path('cairn/tools/x/validations/test_x.json').write_text('{}')\"",
    ]
    for c in refused:
        check(f"refused: {c[:70]!r}", gate.verdict("Bash", {"command": c}) is not None)
    check("an empty command is allowed", gate.verdict("Bash", {"command": ""}) is None)
    check("an unrelated tool is allowed", gate.verdict("Read", {"file_path": str(_COMMONS / "tickets" / "x.json")}) is None)

    print("THE HOOK CONTRACT")
    p = subprocess.run([sys.executable, str(_GATE)], input=json.dumps(
        {"tool_name": "Write", "tool_input": {"file_path": str(_COMMONS / "tickets" / "x.json")}}),
        capture_output=True, text=True)
    check("test_the_pretooluse_gate_refuses_a_write_to_a_record", p.returncode == 2 and "REFUSED" in p.stderr)
    p = subprocess.run([sys.executable, str(_GATE)], input=json.dumps(
        {"tool_name": "Write", "tool_input": {"file_path": str(_REPO_ROOT / "x.py")}}),
        capture_output=True, text=True)
    check("exit 0 to allow", p.returncode == 0 and not p.stderr)
    p = subprocess.run([sys.executable, str(_GATE)], input="not json", capture_output=True, text=True)
    check("unreadable stdin allows and says so", p.returncode == 0 and "unguarded" in p.stderr)

    print("THE WIRING — the gate stands at PreToolUse for every tool that can write a record")
    try:
        settings = json.loads((_REPO_ROOT / ".claude" / "settings.json").read_text())
    except (OSError, ValueError):
        settings = {}
    wired = [h for h in settings.get("hooks", {}).get("PreToolUse", [])
             if any("bin/cmd/artifactgate" in (c.get("command") or "") for c in h.get("hooks", []))]
    matchers = {m for h in wired for m in (h.get("matcher") or "").split("|")}
    check("test_the_gate_is_wired_at_pretooluse_for_every_writing_tool",
          {"Write", "Edit", "MultiEdit", "Bash"} <= matchers, f"matchers={sorted(matchers)}")

    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
