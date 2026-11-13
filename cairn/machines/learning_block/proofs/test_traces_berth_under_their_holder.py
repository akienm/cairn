"""A learning block's traces berth under the device that holds it (ticket 17d4d1899545;
outline 16.4.3, CLAUDE.md's three roots).

learning_block is a shared machine (outline 16): the librarian, CodeMother and the web server
hold it, and a held machine's data hangs off its holder, at
``~/.cairn/devices/<holder>/<n>/machines/learning_block/traces/``. Measured 2026-11-13, every
trace instead sat at ``~/.cairn/devices/learning_block/0/traces``, the space of a device that
does not exist.

  1. A trace written with ``holder='librarian/0'`` lands at the librarian's address and reads
     back there, and nothing is made under ``devices/learning_block``.
  2. With neither a holder nor a root (nor the CAIRN_LB_TRACE_ROOT override), every writer and
     reader refuses, naming holder, and writes nothing; the shell door's trace and dial exit 2
     without --holder.
  3. No class-space source outside learning_block spells ``devices/learning_block``, and the
     two bash writers pass --holder.
  4. migrate moves each mapped flat file to its holder (appending, no line twice), removes it,
     leaves and names an unmapped one, and a second run moves nothing.
  5. The learning_block and skill_block proofs stay green.

Every write runs in a subprocess under a scratch HOME, so the live instance space is never
touched.

    python3 cairn/machines/learning_block/proofs/test_traces_berth_under_their_holder.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"17d4d1899545": {
    "1": "test_a_trace_lands_under_its_holder",
    "2": "test_a_call_naming_no_holder_is_refused",
    "3": "test_no_source_spells_the_flat_address",
    "4": "test_migrate_moves_the_flat_files_to_their_holders",
    "5": "test_the_neighbouring_proofs_stay_green",
}}

_HOLDER_DIR = Path(".cairn/devices/librarian/0/machines/learning_block/traces")
_FLAT = Path(".cairn/devices/learning_block")


def _env(home: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CAIRN_LB_TRACE_ROOT"}
    env.update(HOME=str(home), PYTHONPATH=str(_REPO_ROOT))
    return env


def _py(home: Path, code: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          env=_env(home), cwd=str(_REPO_ROOT), timeout=120)


def _door(home: Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "cairn.machines.learning_block", *argv],
                          capture_output=True, text=True, env=_env(home),
                          cwd=str(_REPO_ROOT), timeout=120)


def test_a_trace_lands_under_its_holder():
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        r = _py(home, (
            "import json\n"
            "from cairn.machines.learning_block import learning_block as lb\n"
            "lb.write_trace('b', 'door_pass', 'training', {'op': 'x'}, holder='librarian/0')\n"
            "print(json.dumps({'read': len(lb.read_trace('b', holder='librarian/0')),\n"
            "                  'lines': len(lb.trace_lines('b', holder='librarian/0')),\n"
            "                  'firings': lb.dial('b', holder='librarian/0')['firings']}))\n"))
        assert r.returncode == 0, f"the holder write failed: {r.stderr[-600:]}"
        got = json.loads(r.stdout.strip().splitlines()[-1])
        assert (home / _HOLDER_DIR / "b.jsonl").is_file(), (
            f"no trace at {_HOLDER_DIR}/b.jsonl: {sorted(str(p.relative_to(home)) for p in home.rglob('*.jsonl'))}")
        assert got == {"read": 1, "lines": 1, "firings": 1}, f"the holder read-back: {got}"
        assert not (home / _FLAT).exists(), "something was made under devices/learning_block"


_NO_HOLDER = {
    "write_trace": "lb.write_trace('b', 'door_pass', 'training', {})",
    "read_trace": "lb.read_trace('b')",
    "trace_lines": "lb.trace_lines('b')",
    "dial": "lb.dial('b')",
    "fire_door": "lb.fire_door(lb.declare_contract('b', {'x': 'why'}), {'x': 1})",
    "traced": "exec('with lb.traced(\\'b\\', \\'op\\'):\\n    pass')",
    "run_block": "__import__('cairn.machines.learning_block.engine', fromlist=['x']).run_block({'block': 'b'}, {})",
}


def test_a_call_naming_no_holder_is_refused():
    bad = []
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        for name, call in _NO_HOLDER.items():
            r = _py(home, (
                "from cairn.machines.learning_block import learning_block as lb\n"
                f"try:\n    {call}\n"
                "except lb.TraceRefused as e:\n"
                "    print('REFUSED', 'holder' in str(e))\n"
                "else:\n    print('ACCEPTED')\n"))
            if r.stdout.strip().splitlines()[-1:] != ["REFUSED True"]:
                bad.append(f"{name}: {(r.stdout + r.stderr)[-300:]!r}")
        made = sorted(str(p.relative_to(home)) for p in home.rglob("*") if p.is_file())
        for argv in (("trace", "b", "door_pass", "op"), ("dial", "b")):
            r = _door(home, *argv)
            if r.returncode != 2:
                bad.append(f"shell door {argv[0]} without --holder exited {r.returncode}")
    assert not bad, "a holderless call was not refused naming holder:\n  " + "\n  ".join(bad)
    assert not made, f"a refused call wrote {made}"


_SPELLED = re.compile(r"devices/learning_block")
_SKIP_PARTS = {"proofs", "validations", ".git", "__pycache__"}


def test_no_source_spells_the_flat_address():
    hits = []
    for p in _REPO_ROOT.rglob("*"):
        if not p.is_file() or _SKIP_PARTS & set(p.relative_to(_REPO_ROOT).parts):
            continue
        rel = p.relative_to(_REPO_ROOT).as_posix()
        if rel.startswith("cairn/machines/learning_block/") or "history" in p.name:
            continue
        if p.suffix not in (".py", ".sh", "") or p.stat().st_size > 2_000_000:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if _SPELLED.search(line):
                hits.append(f"{rel}:{n}")
    assert not hits, "the flat trace address is spelled outside learning_block:\n  " + "\n  ".join(hits)
    for rel in ("cairn/devices/cc/superclaude", "bin/logger_for_bash"):
        calls = [l for l in (_REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
                 if "cairn.machines.learning_block trace" in l]
        assert calls, f"{rel} no longer calls the shell door"
        bare = [l.strip() for l in calls if "--holder" not in l]
        assert not bare, f"{rel} calls the shell door without --holder: {bare}"


def test_migrate_moves_the_flat_files_to_their_holders():
    def line(i: int, block: str) -> str:
        return json.dumps({"block": block, "consumer": "training", "data": {}, "event": "door_pass",
                           "id": f"{i:012x}", "when": "2026-11-13T00:00:00+00:00"}, sort_keys=True)
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        flat = home / _FLAT / "0" / "traces"
        flat.mkdir(parents=True)
        ask = [line(1, "librarian-ask"), line(2, "librarian-ask")]
        (flat / "librarian-ask.jsonl").write_text("\n".join(ask) + "\n")
        (flat / "skill__intent.jsonl").write_text(line(3, "skill:intent") + "\n")
        (flat / "skill:note.jsonl").write_text(line(4, "skill:note") + "\n")
        (flat / "nobody-holds-this.jsonl").write_text(line(5, "nobody-holds-this") + "\n")
        held = home / _HOLDER_DIR
        held.mkdir(parents=True)
        (held / "librarian-ask.jsonl").write_text(ask[0] + "\n")
        r = _door(home, "migrate")
        assert r.returncode == 0, f"migrate exited {r.returncode}: {(r.stdout + r.stderr)[-600:]}"
        lib = (held / "librarian-ask.jsonl").read_text().splitlines()
        assert sorted(lib) == sorted(ask), f"librarian-ask moved wrong: {lib}"
        cc = home / ".cairn/devices/cc/0/machines/learning_block/traces"
        assert (cc / "skill__intent.jsonl").read_text().splitlines() == [line(3, "skill:intent")]
        assert (cc / "skill__note.jsonl").read_text().splitlines() == [line(4, "skill:note")]
        left = sorted(p.name for p in flat.iterdir())
        assert left == ["nobody-holds-this.jsonl"], f"the flat root keeps {left}"
        assert "nobody-holds-this" in r.stdout, f"the unmapped block is not named: {r.stdout!r}"
        again = _door(home, "migrate")
        assert again.returncode == 0 and "moved" not in again.stdout.replace("moved 0", ""), (
            f"a second migrate moved something: {again.stdout!r}")
        assert sorted(lib) == sorted((held / "librarian-ask.jsonl").read_text().splitlines())


def test_the_neighbouring_proofs_stay_green():
    red = []
    for proof in ("cairn/machines/learning_block/proofs/test_learning_block.py",
                  *sorted(str(p.relative_to(_REPO_ROOT)) for p in
                          (_REPO_ROOT / "cairn/machines/skill_block/proofs").glob("test_*.py"))):
        r = subprocess.run([sys.executable, str(_REPO_ROOT / proof)], capture_output=True,
                           text=True, cwd=str(_REPO_ROOT), timeout=400,
                           env=dict(os.environ, PYTHONPATH=str(_REPO_ROOT)))
        if r.returncode != 0:
            red.append(f"{proof}: {(r.stdout + r.stderr)[-400:]}")
    assert not red, "a neighbouring proof went red:\n  " + "\n  ".join(red)


def main() -> int:
    fails = 0
    teeth = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in teeth:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not fails else 'RED'} — {len(teeth) - fails}/{len(teeth)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
