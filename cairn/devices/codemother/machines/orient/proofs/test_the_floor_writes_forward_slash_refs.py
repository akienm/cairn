"""Proof for ticket b12a4b97b125: the orient floor writes forward-slash refs on every box.

Measured 2026-11-13: a9709b744bf5's orient, drafted on akiendell, was refused on Linux
with "refs the floor cannot verify exist: cairn\\devices\\cairn, cairn\\devices\\codemother,
...". floor_packet builds its in-repo refs from component_home and _repo_relative, and both
are os.path.relpath, which spells a Windows path with backslashes.

Windows is simulated here on Linux: the two sources are wrapped so they answer the way they
answer on Windows, and restored after. Teeth bind the subject at call time, never at import.

    bin/cairn test <this file>
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 6))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

# Three components the a9709 refusal named, plus one in-repo absolute path, so both
# sources (component_home and _repo_relative) feed the floor.
ABS_PATH = os.path.join(REPO, "cairn", "devices", "codemother", "intention+why.json")
REQUEST = ("the clearance gate in codemother and learning_block read "
           f"{ABS_PATH} on every box")


def _orient():
    from cairn.devices.codemother.machines.orient import orient
    return orient


@contextmanager
def _as_on_windows():
    """component_home and _repo_relative answer with backslashes, as relpath does on Windows."""
    o = _orient()
    home, rel = o.component_home, o._repo_relative

    def win(fn):
        def wrapped(*a, **kw):
            got = fn(*a, **kw)
            return got.replace("/", "\\") if isinstance(got, str) else got
        return wrapped

    o.component_home, o._repo_relative = win(home), win(rel)
    try:
        yield o
    finally:
        o.component_home, o._repo_relative = home, rel


def _floor():
    with _as_on_windows() as o:
        return o.floor_packet(REQUEST, root=REPO)


def test_the_floor_stores_forward_slash_refs_and_their_rungs():
    floor = _floor()
    refs = floor["refs"] or []
    print(f"       refs: {refs}")
    print(f"       domain: {floor['domain']}")
    assert any("\\" in r for r in [_orient().component_home("codemother", REPO).replace("/", "\\")]), \
        "the Windows simulation does not produce a backslash, so this tooth measures nothing"
    assert len(refs) >= 3, f"the floor found too few refs to judge: {refs}"
    assert "cairn/devices/codemother/intention+why.json" in refs, \
        f"the in-repo absolute path did not come back repo-relative and posix: {refs}"
    bad = [r for r in refs if "\\" in r]
    assert not bad, f"the floor stored backslash refs: {bad}"
    assert floor["domain"] and "cairn/devices/codemother (device)" in floor["domain"], \
        f"the domain did not name the refs' rungs: {floor['domain']!r}"


def test_orient_on_linux_finds_none_of_those_refs_invented():
    floor = _floor()
    record = _orient().inspect_orient({"refs": floor["refs"]}, root=REPO)
    entry = next(r for r in record if r.get("identity") == "every_ref_exists_on_disk")
    print(f"       every_ref_exists_on_disk: {entry.get('actual')!r}")
    assert entry.get("actual") == [], f"orient called these refs invented: {entry.get('actual')}"


PROVES = {
    "b12a4b97b125": {
        "1": "test_the_floor_stores_forward_slash_refs_and_their_rungs",
        "2": "test_orient_on_linux_finds_none_of_those_refs_invented",
    },
}


if __name__ == "__main__":
    reds = 0
    for name, fn in [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — each tooth's failure is said, verbatim
            reds += 1
            print(f"  RED  {name}: {type(exc).__name__}: {exc}")
    print("\nGREEN" if not reds else f"\nRED ({reds})")
    sys.exit(1 if reds else 0)
