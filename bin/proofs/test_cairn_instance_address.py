"""Proof for the dispatcher's INSTANCE ADDRESS — ticket 55fc9263bf5a.

`cairn <device>[.<instance>] <verb>` resolves to ~/.cairn/devices/<device>/<instance>/bin/<verb>,
and a bare `cairn <device> <verb>` still resolves instance 0 — by DEFAULT, not by a second
code path. The ticket's falsifier names three DONE-when clauses and its proves_red numbers
none, so ``proof_coverage.clauses`` reads ONE clause, ``all``, and one composite tooth carries
it. The clause bodies are spelled once as ``_clause_a/_b/_c`` and driven twice: by the
composite tooth the ticket declares, and by a tooth apiece so a red says WHICH clause broke.

Teeth a hollow build could not pass:

  (a) A DOTTED ADDRESS REACHES THE NAMED INSTANCE. The fixture device stands at instances
      0 AND 1 with a DIFFERENT script at each, so a dispatcher that read the dot and then
      resolved 0 anyway prints the wrong path and trips.
  (b) EVERY BARE ADDRESS STILL RESOLVES INSTANCE 0 — EXHAUSTIVELY, never by sampling. The
      fixture MIRRORS the live device population (whatever stands under ~/.cairn/devices at
      run time — the count is read, never written down here, because a number in a comment is
      a snapshot and the population grows) and every one is driven; stdout must equal
      the instance-0 path EXACTLY. An empty enumeration FAILS rather than passing vacuously,
      because a table over nothing is the hollow green this clause exists to refuse.
  (c) A KNOWN DEVICE AT AN ABSENT INSTANCE REFUSES BY NAMING THE INSTANCES THAT EXIST, and
      it never collapses into "no such device" — the two lacks are different and a reader
      acts on them differently (Law 7).
  + FOLD BEFORE SPLIT. `FIXTURE_INSTANCE_ADDRESS.1` is the same address as its lowercase
      twin. A build that split the token before folding it would fold only one half and miss
      the folder; this tooth is the ordering's only witness.
  + A NON-NUMERIC INSTANCE IS ITS OWN REFUSAL, fired before the folder lookup: a typo in the
      instance must not come back as a missing device.
  + ARGS RIDE VERBATIM. Everything after the two resolved tokens passes through unfolded and
      unreordered, empty strings included — the address is a system word, the payload is not.
  + THE DOT GATES THE LEGACY FALLBACK. `cairn <legacy-verb>` still runs bin/cmd/<verb>;
      `cairn <legacy-verb>.1` does not, because the legacy verbs have no instances to ask for.

Never touches ~/.cairn: CAIRN_INSTANCE_ROOT and CAIRN_CMD_DIR point at a temp tree, and the
live root is READ (to mirror its names) and never written.

    python3 bin/proofs/test_cairn_instance_address.py     # exit 0 = green
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

PROVES = {"55fc9263bf5a": {"all": "test_the_instance_is_part_of_the_address"}}

_DISPATCHER = Path(__file__).resolve().parents[1] / "cairn"   # bin/proofs -> bin -> bin/cairn
_LIVE_ROOT = Path.home() / ".cairn" / "devices"
_FIXTURE_DEVICE = "fixture_instance_address"


def _write_verb(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\n" + body + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _echoes_its_own_path(path: Path) -> None:
    """The verb prints the path it was reached at. The dispatcher `exec`s it, so $0 IS the
    resolved target — which makes the assertion an identity, not a proxy for one."""
    _write_verb(path, 'printf "%s\\n" "$0"')


def _echoes_its_args(path: Path) -> None:
    """The verb prints its arguments, one per line, between markers. D8's $0 stub cannot
    witness argument passing at all — it prints one thing and that thing is the path — so
    the one clause about ARGS gets its own stub rather than being dropped for want of one."""
    _write_verb(path, 'printf "ARGS\\n"; printf "%s\\n" "$@"; printf "END\\n"')


def _mirror(root: Path) -> list[str]:
    """Every live device name, at instance 0, with a self-named verb that says where it is.

    The names come from the LIVE root because the clause is about the live population; the
    bytes are all fixture. Reading the live folder is a read, and the only one this proof
    makes outside its temp tree."""
    names = sorted(p.name for p in _LIVE_ROOT.iterdir() if p.is_dir()) if _LIVE_ROOT.is_dir() else []
    for name in names:
        _echoes_its_own_path(root / name / "0" / "bin" / name)
    return names


def _fixture_world(root: Path) -> None:
    """The fixture device at instances 0 AND 1 — two instances, two different scripts, so
    'the dot was read' and 'the dot was ignored' cannot print the same line."""
    for n in ("0", "1"):
        _echoes_its_own_path(root / _FIXTURE_DEVICE / n / "bin" / "verb")
        _echoes_its_own_path(root / _FIXTURE_DEVICE / n / "bin" / _FIXTURE_DEVICE)
        _echoes_its_args(root / _FIXTURE_DEVICE / n / "bin" / "echoargs")


def _run(root: Path, cmd_dir: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ,
           "CAIRN_INSTANCE_ROOT": str(root),
           "CAIRN_CMD_DIR": str(cmd_dir)}
    return subprocess.run([str(_DISPATCHER), *args], capture_output=True, text=True, env=env)


# --- the clause bodies, spelled once -----------------------------------------------------

def _clause_a(root: Path, cmd_dir: Path) -> None:
    """(a) `cairn <device>.<n> <verb>` resolves to <root>/<device>/<n>/bin/<verb>."""
    for n in ("0", "1"):
        r = _run(root, cmd_dir, f"{_FIXTURE_DEVICE}.{n}", "verb")
        want = str(root / _FIXTURE_DEVICE / n / "bin" / "verb")
        assert r.returncode == 0, f"{_FIXTURE_DEVICE}.{n} verb exited {r.returncode}: {r.stderr!r}"
        assert r.stdout == want + "\n", f"{_FIXTURE_DEVICE}.{n} verb resolved {r.stdout!r}, want {want!r}"
    # the verb defaults to the device name on a dotted address too
    r = _run(root, cmd_dir, f"{_FIXTURE_DEVICE}.1")
    want = str(root / _FIXTURE_DEVICE / "1" / "bin" / _FIXTURE_DEVICE)
    assert r.stdout == want + "\n", f"the self-named launcher at instance 1 resolved {r.stdout!r}"
    print(f"  ok  (a) a dotted address reaches the named instance, 0 and 1 alike")


def _clause_b(root: Path, cmd_dir: Path, names: list[str]) -> None:
    """(b) every bare `cairn <device> <verb>` still resolves instance 0 — the whole table."""
    assert names, ("the mirror enumerated NO devices, so this clause would pass over an empty "
                   f"table: {_LIVE_ROOT} held no device folders")
    for name in names:
        r = _run(root, cmd_dir, name)
        want = str(root / name / "0" / "bin" / name)
        assert r.returncode == 0, f"bare `cairn {name}` exited {r.returncode}: {r.stderr!r}"
        assert r.stdout == want + "\n", f"bare `cairn {name}` resolved {r.stdout!r}, want {want!r}"
        assert r.stderr == "", f"bare `cairn {name}` wrote to stderr: {r.stderr!r}"
    # and with a verb named, not only the self-named launcher
    r = _run(root, cmd_dir, _FIXTURE_DEVICE, "verb")
    want = str(root / _FIXTURE_DEVICE / "0" / "bin" / "verb")
    assert r.stdout == want + "\n", f"bare `cairn {_FIXTURE_DEVICE} verb` resolved {r.stdout!r}"
    print(f"  ok  (b) all {len(names)} mirrored devices still resolve instance 0, byte for byte")


def _clause_c(root: Path, cmd_dir: Path) -> None:
    """(c) a known device at an absent instance refuses by naming the instances that exist."""
    r = _run(root, cmd_dir, f"{_FIXTURE_DEVICE}.7", "verb")
    assert r.returncode == 127, f"an absent instance must exit 127, got {r.returncode}"
    assert r.stdout == "", f"a refusal must write nothing to stdout: {r.stdout!r}"
    lines = r.stderr.splitlines()
    assert lines[0] == f"cairn {_FIXTURE_DEVICE}.7: no such instance: 7", \
        f"the refusal must name the address as typed: {lines[:1]!r}"
    assert lines[1] == f"instances for {_FIXTURE_DEVICE}:", f"it must list what there is: {lines[1:2]!r}"
    assert lines[2:4] == ["  0", "  1"], f"one instance per line, in order: {lines[2:4]!r}"
    assert "no such device" not in r.stderr, \
        "a device we HAVE at an instance we do not may never read as a missing device"
    # the other half of the distinction: a device we do not have IS a missing device, and the
    # refusal echoes the token AS TYPED, dot and all.
    r = _run(root, cmd_dir, "no_such_fixture_device.3", "verb")
    assert r.returncode == 127, f"an unknown device must exit 127, got {r.returncode}"
    assert "cairn: no such device or command: no_such_fixture_device.3" in r.stderr, \
        f"the unknown-device refusal must echo the whole token: {r.stderr!r}"
    print("  ok  (c) an absent instance names the instances that exist, and is not a missing device")


def _fold_before_split(root: Path, cmd_dir: Path) -> None:
    r = _run(root, cmd_dir, f"{_FIXTURE_DEVICE.upper()}.1", "VERB")
    want = str(root / _FIXTURE_DEVICE / "1" / "bin" / "verb")
    assert r.returncode == 0, f"an upper-case dotted address exited {r.returncode}: {r.stderr!r}"
    assert r.stdout == want + "\n", \
        f"FOLD BEFORE SPLIT: {_FIXTURE_DEVICE.upper()}.1 resolved {r.stdout!r}, want {want!r}"
    print("  ok  the token folds BEFORE it splits, so CC.1 and cc.1 are one address")


def _non_numeric_instance(root: Path, cmd_dir: Path) -> None:
    r = _run(root, cmd_dir, f"{_FIXTURE_DEVICE}.x", "verb")
    assert r.returncode == 127, f"a non-numeric instance must exit 127, got {r.returncode}"
    assert f"cairn {_FIXTURE_DEVICE}.x: instance must be a number, got: x" in r.stderr, \
        f"it must name the real lack: {r.stderr!r}"
    assert "no such device" not in r.stderr, \
        "a typo in the instance must not come back as a missing device"
    print("  ok  a non-numeric instance refuses as an instance, never as a missing device")


def _args_ride_verbatim(root: Path, cmd_dir: Path) -> None:
    """Everything after the two resolved tokens rides through UNTOUCHED — same bytes, same
    order, same case, empty strings included. The dispatcher folds the address it resolves;
    an address is a system word and the rest is somebody's data, and folding data would be
    the same defect one rung down (`cairn cc.1 restart spawn 1` must not become `spawn 1`
    with a case-folded payload)."""
    given = ["Mixed Case", "--flag=VALUE", "", "spawn", "1"]
    r = _run(root, cmd_dir, f"{_FIXTURE_DEVICE}.1", "echoargs", *given)
    assert r.returncode == 0, f"echoargs exited {r.returncode}: {r.stderr!r}"
    want = "ARGS\n" + "".join(a + "\n" for a in given) + "END\n"
    assert r.stdout == want, f"args did not ride verbatim: {r.stdout!r}, want {want!r}"
    print("  ok  args after the two resolved tokens ride verbatim and unfolded")


def _the_dot_gates_the_legacy_fallback(root: Path, cmd_dir: Path) -> None:
    _write_verb(cmd_dir / "fixture_legacy_verb", 'printf "LEGACY\\n"')
    r = _run(root, cmd_dir, "fixture_legacy_verb")
    assert r.stdout == "LEGACY\n", f"an undotted legacy verb must still run: {r.stdout!r} {r.stderr!r}"
    r = _run(root, cmd_dir, "fixture_legacy_verb.1")
    assert r.returncode == 127 and "LEGACY" not in r.stdout, \
        "a DOTTED token asked for an instance of a device; the legacy verbs have none"
    print("  ok  the legacy fallback answers an undotted token only")


# --- the teeth ---------------------------------------------------------------------------

def _world(fn):
    with tempfile.TemporaryDirectory(prefix="cairn_instance_address_fixture_") as d:
        root = Path(d) / "devices"
        cmd_dir = Path(d) / "cmd"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        names = _mirror(root)
        _fixture_world(root)
        return fn(root, cmd_dir, names)


def test_the_instance_is_part_of_the_address():
    """THE COMPOSITE TOOTH the ticket declares: all three clauses plus the three teeth that
    guard the ordering, the typo and the fallback. One clause in the falsifier, one tooth."""
    def body(root, cmd_dir, names):
        _clause_a(root, cmd_dir)
        _clause_b(root, cmd_dir, names)
        _clause_c(root, cmd_dir)
        _fold_before_split(root, cmd_dir)
        _non_numeric_instance(root, cmd_dir)
        _args_ride_verbatim(root, cmd_dir)
        _the_dot_gates_the_legacy_fallback(root, cmd_dir)
    _world(body)


def test_a_dotted_address_reaches_the_named_instance():
    _world(lambda root, cmd_dir, names: _clause_a(root, cmd_dir))


def test_every_bare_address_still_resolves_instance_zero():
    _world(lambda root, cmd_dir, names: _clause_b(root, cmd_dir, names))


def test_an_absent_instance_names_the_instances_that_exist():
    _world(lambda root, cmd_dir, names: _clause_c(root, cmd_dir))


def test_the_address_folds_before_it_splits():
    _world(lambda root, cmd_dir, names: _fold_before_split(root, cmd_dir))


def test_a_non_numeric_instance_is_its_own_refusal():
    _world(lambda root, cmd_dir, names: _non_numeric_instance(root, cmd_dir))


def test_args_after_the_address_ride_verbatim():
    _world(lambda root, cmd_dir, names: _args_ride_verbatim(root, cmd_dir))


def test_the_dot_gates_the_legacy_fallback():
    _world(lambda root, cmd_dir, names: _the_dot_gates_the_legacy_fallback(root, cmd_dir))


def main() -> int:
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
        except AssertionError as e:
            print(f"  RED  {name}: {e}")
            failed += 1
        else:
            print(f"  ok   {name}")
    print("RED" if failed else "GREEN")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
