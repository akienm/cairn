"""Proof for ticket e215f7524659 — a path crosses the inspect wire by its root, not by the asking box's disk.

A Path used to cross as its string, so the asking box's absolute spelling named a disk the answering CodeMother may not
share: the /sorted 'none, because <repo path>' reason, true on the asker's checkout, was judged False by a launched
CodeMother whose roots differ. A path now crosses as {root: cairn|CairnCommons, rel: <posix>} and is rebuilt under the
ANSWERER's roots. The teeth drive the codec with two different root sets (the caller's A and the answerer's B), so they
run on any OS; the through-ask() measurement of the /sorted reason needs a launched CodeMother (Linux) and is the
integrator's.

    python <this file>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.inspect_wire import inspect_wire as iw  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "e215f7524659": {
        "1": "a_path_rebuilds_under_the_answerers_roots",
        "2": "a_repo_file_the_caller_names_exists_under_the_answerers_different_checkout",
        "3": "a_path_under_neither_root_raises_at_either_end",
        "4": "a_backslash_rel_decodes_to_the_same_file",
    },
}


def _roots(tmp: Path, tag: str) -> dict:
    repo, commons = tmp / tag / "cairn", tmp / tag / "CairnCommons"
    repo.mkdir(parents=True)
    commons.mkdir(parents=True)
    return {"cairn": repo, "CairnCommons": commons}


class _As:
    """Make iw._roots answer as one process's roots, then put it back."""

    def __init__(self, roots: dict):
        self.roots = roots

    def __enter__(self):
        self.real = getattr(iw, "_roots", None)     # absent on the unfixed codec: the teeth must still RUN and fail on the wire form
        iw._roots = lambda: self.roots

    def __exit__(self, *exc):
        if self.real is None:
            del iw._roots
        else:
            iw._roots = self.real


def a_path_rebuilds_under_the_answerers_roots() -> None:
    tmp = Path(str(scratch_dir("wire_by_root_")))
    try:
        a, b = _roots(tmp, "caller"), _roots(tmp, "answerer")
        for name, rel in (("cairn", "cairn/tools/x/x.py"), ("CairnCommons", "tickets/abc-a-ticket.json")):
            sent = a[name] / Path(rel)
            with _As(a):
                wire = iw.wire_encode(sent)
            assert wire == {"__wire__": "path", "root": name, "rel": rel}, f"the wire form is not root+rel: {wire}"
            with _As(b):
                got = iw.wire_decode(wire)
            assert got == b[name] / Path(rel), f"{name}: {sent} rebuilt as {got}, not under the answerer's root {b[name]}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def a_repo_file_the_caller_names_exists_under_the_answerers_different_checkout() -> None:
    tmp = Path(str(scratch_dir("wire_by_root_")))
    try:
        a, b = _roots(tmp, "caller"), _roots(tmp, "answerer")
        rel = "cairn/devices/x/intention+why.json"
        for roots in (a, b):                       # the SAME file in two checkouts at two absolute places
            f = roots["cairn"] / Path(rel)
            f.parent.mkdir(parents=True)
            f.write_text("{}\n", encoding="utf-8", newline="\n")
        with _As(a):
            wire = iw.wire_encode(a["cairn"] / Path(rel))
        with _As(b):
            got = iw.wire_decode(wire)
        assert got.is_file(), f"the file the caller named does not resolve under the answerer's checkout: {got}"
        assert a["cairn"] not in got.parents, "the decoded path still names the CALLER's disk"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def a_path_under_neither_root_raises_at_either_end() -> None:
    tmp = Path(str(scratch_dir("wire_by_root_")))
    try:
        a = _roots(tmp, "caller")
        stray = tmp / "elsewhere" / "scratch.json"
        with _As(a):
            for bad in (stray, a["cairn"] / ".." / "escape.json"):
                try:
                    iw.wire_encode(bad)
                except ValueError as e:
                    assert str(bad) in str(e) or "neither root" in str(e), e
                else:
                    raise AssertionError(f"encode answered for a path under neither root: {bad}")
            for wire in ({"__wire__": "path", "root": "elsewhere", "rel": "x"},
                         {"__wire__": "path", "root": "cairn", "rel": "../x"}):
                try:
                    iw.wire_decode(wire)
                except ValueError:
                    pass
                else:
                    raise AssertionError(f"decode answered for {wire}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def a_backslash_rel_decodes_to_the_same_file() -> None:
    tmp = Path(str(scratch_dir("wire_by_root_")))
    try:
        b = _roots(tmp, "answerer")
        with _As(b):
            fwd = iw.wire_decode({"__wire__": "path", "root": "cairn", "rel": "cairn/tools/x/x.py"})
            back = iw.wire_decode({"__wire__": "path", "root": "cairn", "rel": "cairn\\tools\\x\\x.py"})
        assert fwd == back == b["cairn"] / "cairn" / "tools" / "x" / "x.py", (fwd, back)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TEETH = [a_path_rebuilds_under_the_answerers_roots,
         a_repo_file_the_caller_names_exists_under_the_answerers_different_checkout,
         a_path_under_neither_root_raises_at_either_end, a_backslash_rel_decodes_to_the_same_file]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
