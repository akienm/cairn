#!/usr/bin/env python3
"""Proof that the artifact door removes a read-only record (ticket aa1459b4ccd4).

WHAT IT PROVES: the validation store writes seals read-only (-r--r--r--). On Windows
``Path.unlink`` of a read-only file raises PermissionError [WinError 5], so ``artifact remove``
could not remove a seal there. The door clears the read-only bit before it unlinks, on every OS;
the store's read-only mode for new seals is deliberate and is not touched.

Teeth, one per falsifier clause (PROVES below), over a scratch world (``set_diagnostic_roots``).
Each tooth prints the OS it ran on (``sys.platform``); the read-only unlink failure is a
Windows behaviour, so on posix tooth 1 passes today and the Windows run is the red-first one.
  (1) a record written 0o444 through the door under a validations path is removed through the
      door: the file is gone and a ``remove`` entry with sha_after absent is journaled;
  (2) a writable record still removes the same way, and a seal written read-only through the
      door is still read-only after the door writes it (the mode is not changed).

    bin/cairn test cairn/tools/artifact/proofs/test_remove_clears_the_read_only_bit.py
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

# Bound at CALL time, never at import, so a reverted subject reds the teeth instead of crashing.
A = None  # type: ignore[assignment]

PROVES = {"aa1459b4ccd4": {
    "1": "test_a_read_only_record_is_removed_through_the_door",
    "2": "test_a_writable_record_still_removes_and_a_seal_is_still_written_read_only",
}}

FAILURES: list[str] = []
OS = sys.platform


def _body(doc) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  [{OS}] {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world(tmp: Path) -> Path:
    commons = tmp / "CairnCommons"
    commons.mkdir()
    cairn = tmp / "cairn"
    (cairn / "tools" / "comp" / "validations").mkdir(parents=True)
    for r in (commons, cairn):
        subprocess.run(["git", "-C", str(r), "init", "-q"], check=True)
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    return cairn


def _journal_entries(cairn: Path) -> list[dict]:
    j = A.journal_path(cairn)
    if not j.exists():
        return []
    return [json.loads(line) for line in j.read_text(encoding="utf-8").splitlines() if line.strip()]


def _writable(p: Path) -> bool:
    return bool(p.stat().st_mode & stat.S_IWRITE)


def test_a_read_only_record_is_removed_through_the_door(cairn: Path) -> None:
    name = "test_a_read_only_record_is_removed_through_the_door"
    seal = cairn / "tools" / "comp" / "validations" / "a_seal.json"
    A.write(seal, _body({'verdict': 'green'}), verb="seal", why="proof: a read-only seal", mode=0o444)
    if _writable(seal):
        check(name, False, "setup: the seal is not read-only, so the tooth would prove nothing")
        return
    try:
        out = A.remove(seal, why="proof: remove a read-only seal")
    except Exception as exc:  # noqa: BLE001 — the unfixed door raises PermissionError on Windows
        check(name, False, f"{type(exc).__name__}: {exc}")
        return
    removes = [e for e in _journal_entries(cairn)
               if e.get("verb") == "remove" and str(e.get("path", "")).endswith("a_seal.json")]
    ok = (not seal.exists() and out.get("journaled") is True and len(removes) == 1)
    check(name, ok, f"gone={not seal.exists()} journaled={out.get('journaled')} remove entries={len(removes)}")


def test_a_writable_record_still_removes_and_a_seal_is_still_written_read_only(cairn: Path) -> None:
    name = "test_a_writable_record_still_removes_and_a_seal_is_still_written_read_only"
    plain = cairn / "tools" / "comp" / "validations" / "plain.json"
    seal = cairn / "tools" / "comp" / "validations" / "held.json"
    try:
        A.write(plain, _body({'n': 1}), verb="seal", why="proof: a writable record")
        A.write(seal, _body({'n': 2}), verb="seal", why="proof: a read-only seal", mode=0o444)
        read_only_after_write = not _writable(seal)
        out = A.remove(plain, why="proof: remove a writable record")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")
        return
    ok = read_only_after_write and not plain.exists() and out.get("journaled") is True and seal.exists()
    check(name, ok, f"seal read-only after write={read_only_after_write} plain gone={not plain.exists()}")


def main() -> int:
    global A
    try:
        from cairn.tools.artifact import artifact as door
    except Exception as exc:  # noqa: BLE001
        print(f"the subject cairn.tools.artifact.artifact does not load: {exc!r}")
        for n in PROVES["aa1459b4ccd4"].values():
            check(n, False, "subject absent")
        return 1
    A = door
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-remove-readonly-proof-") as d:
            tmp = Path(d)
            try:
                cairn = _world(tmp)
                test_a_read_only_record_is_removed_through_the_door(cairn)
                test_a_writable_record_still_removes_and_a_seal_is_still_written_read_only(cairn)
            finally:
                A.set_diagnostic_roots(None)
                # a failed tooth leaves a read-only file the temp dir cannot delete on Windows
                for f in tmp.rglob("*"):
                    if f.is_file():
                        try:
                            os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
                        except OSError:
                            pass
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["aa1459b4ccd4"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
