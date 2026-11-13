"""PROOF for ticket dfe6c1432fc8: the tester seals a host-seam's verify on this box.

Measured 2026-11-13 by the orchestrator on b1f182b6b818 and 496dcbeba174: clearance refuses
every host-seam crossing with "the crossing names no proof at all", because nothing turns a
host-seam intention's verify into a sealed validation. The installer runs the verify and
leaves no record; node_classes/host-seam.json's prove_gate names the tester as
"hand-run until built".

A host-seam seal is BOX-LOCAL: one file per box at
``<intentions dir>/validations/<stem>/<host>.json``, and ``standing()`` reads only this box's.

Every tooth runs the REAL ``cli.main(["--host-seam", <fixture>, ...])`` over a fixture
intention under a scratch dir, then asks the REAL ``standing()``. Host facts and the host
name are faked by wrapping ``validation_store.host_facts`` / ``host_name`` and restoring them.

    bin/cairn test <this file>
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _fixture(command: str) -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    d = Path(scratch_dir("dfe6-host-seam-"))
    p = d / "host-testing-dfe6c1432fc8.json"
    p.write_text(json.dumps({
        "id": "host-testing-dfe6c1432fc8", "node_class": "host-seam",
        "intention": "testing-dfe6c1432fc8 a fixture host-seam",
        "verify": {"command": command, "green": "testing-dfe6c1432fc8 exit 0",
                   "horizon": "testing-dfe6c1432fc8 after an OS upgrade"}}, indent=1),
        encoding="utf-8")
    return p


def _run(path: Path, *flags: str) -> tuple[int, str]:
    from cairn.devices.tester import cli
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        rc = cli.main(["--host-seam", str(path), *flags])
    text = out.getvalue()
    print("       " + text.replace("\n", "\n       ").rstrip())
    return rc, text


def _record_path(path: Path, host: str | None = None) -> Path:
    from cairn.tools.validation_store import validation_store as vs
    return path.parent / "validations" / path.stem / f"{host or vs.host_name()}.json"


@contextlib.contextmanager
def _patched(name: str, fn):
    from cairn.tools.validation_store import validation_store as vs
    was = getattr(vs, name)
    setattr(vs, name, fn)
    try:
        yield
    finally:
        setattr(vs, name, was)


def _standing(path: Path) -> dict:
    from cairn.tools.validation_store import validation_store as vs
    return vs.standing(str(path))


def test_a_green_verify_seals_this_box_and_stands_proven():
    seam = _fixture("true")
    rc, _ = _run(seam)
    assert rc == 0, f"a green verify without --seal exited {rc}"
    assert not (seam.parent / "validations").exists(), "a run without --seal landed a record"
    rc, _ = _run(seam, "--seal")
    rec_path = _record_path(seam)
    assert rc == 0, f"a green verify sealed with rc {rc}"
    assert rec_path.is_file(), f"no record landed at {rec_path}"
    rec = json.loads(rec_path.read_text(encoding="utf-8"))[-1]
    facts = rec["evidence"].get("host_facts") or {}
    assert rec["verdict"] == "green", rec
    for key in ("hostname", "os_id", "os_version_id", "kernel"):
        assert facts.get(key), f"the record carries no host fact {key!r}: {facts}"
    got = _standing(seam)
    assert got["proven"], f"a green seal on this box does not stand proven: {got['why']}"


def test_a_red_verify_seals_red_and_is_not_proven():
    seam = _fixture("false")
    rc, _ = _run(seam, "--seal")
    rec_path = _record_path(seam)
    assert rc == 1, f"a red verify exited {rc}"
    assert rec_path.is_file(), f"a red verify landed no record at {rec_path}"
    assert json.loads(rec_path.read_text(encoding="utf-8"))[-1]["verdict"] == "red"
    got = _standing(seam)
    assert not got["proven"], f"a red seal stands proven: {got['why']}"


def test_a_moved_host_fact_reads_not_proven():
    from cairn.tools.validation_store import validation_store as vs
    seam = _fixture("true")
    _run(seam, "--seal")
    real = vs.host_facts()
    moved = {**real, "kernel": "testing-dfe6c1432fc8-kernel"}
    with _patched("host_facts", lambda: moved):
        got = _standing(seam)
    print(f"       why: {got['why']}")
    assert not got["proven"], f"a host whose kernel moved still stands proven: {got['why']}"
    assert "kernel" in got["why"], f"the why does not name the fact that moved: {got['why']}"


def test_another_boxs_record_is_not_proven_here():
    seam = _fixture("true")
    with _patched("host_name", lambda: "testing-dfe6-other-box"):
        _run(seam, "--seal")
    assert _record_path(seam, "testing-dfe6-other-box").is_file(), "the other box's seal did not land"
    assert not _record_path(seam).exists(), "the other box's seal landed under this box's name"
    got = _standing(seam)
    print(f"       why: {got['why']}")
    assert not got["proven"], f"another box's green seal stands proven here: {got['why']}"


def test_an_edited_intention_reads_not_proven():
    seam = _fixture("true")
    _run(seam, "--seal")
    doc = json.loads(seam.read_text(encoding="utf-8"))
    doc["verify"]["command"] = "true && true"
    seam.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    got = _standing(seam)
    print(f"       why: {got['why']}")
    assert not got["proven"], f"an edited intention still stands proven: {got['why']}"


PROVES = {
    "dfe6c1432fc8": {
        "1": "test_a_green_verify_seals_this_box_and_stands_proven",
        "2": "test_a_red_verify_seals_red_and_is_not_proven",
        "3": "test_a_moved_host_fact_reads_not_proven",
        "4": "test_another_boxs_record_is_not_proven_here",
        "5": "test_an_edited_intention_reads_not_proven",
    },
}


if __name__ == "__main__":
    reds = 0
    for name, fn in [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]:
        try:
            fn()
            print(f"  ok   {name}")
        except BaseException as exc:  # noqa: BLE001 — each tooth's failure is said, verbatim
            reds += 1
            print(f"  RED  {name}: {type(exc).__name__}: {exc}")
    print("\nGREEN" if not reds else f"\nRED ({reds})")
    sys.exit(1 if reds else 0)
