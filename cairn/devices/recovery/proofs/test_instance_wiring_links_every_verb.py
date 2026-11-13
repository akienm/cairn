"""Proof for ticket f0ffa0db0952 — the wiring links missing verbs, not only missing directories.

Measured 2026-11-09: ``_cairn_wire_device`` in bootstrap.sh returned at its first line whenever
the instance bin was a directory, so a verb added to an already-wired device's class bin was
never linked; and 6 instance bins are whole-directory symlinks to their class bin, where a
per-file ``ln -sf`` would commit a self-pointing link into class-space. The function also wired
instance 0 only.

  1. a class verb added under a real-directory instance bin is linked; a correct link is not
     rewritten (lstat mtime unchanged).
  2. an instance bin that IS its class bin is left alone: listing unchanged, no self link.
  3. a hand-placed regular file stays byte-identical, is counted left, and its path is on stderr.
  4. ``cairn_wire_instances <device> <instance>`` wires only that bin; a bad argument is refused
     nonzero and creates nothing.
  5. the counts line is ``linked N already M left K`` and adds up; bootstrap_first_run.sh no
     longer calls the numbers devices.

Every tooth runs a COPY of bootstrap.sh inside a scratch repo (CAIRN_REPO_ROOT is derived from
the file's own path, so the copy walks only the fixture's devices) against a scratch
CAIRN_INSTANCE_ROOT. Never ~/.cairn, never the live repo's devices.

    python3 cairn/devices/recovery/proofs/test_instance_wiring_links_every_verb.py
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_BASH = (shutil.which("bash") or "bash") if os.name == "nt" else "bash"  # ticket 1cabffbba003: a bare bash is the WSL launcher on Windows

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "f0ffa0db0952": {
        "1": "tooth_1_a_new_class_verb_is_linked_and_a_correct_link_is_kept",
        "2": "tooth_2_a_bin_that_is_its_class_bin_is_left_alone",
        "3": "tooth_3_a_hand_placed_file_is_left_and_named",
        "4": "tooth_4_one_device_and_instance_is_wired_alone",
        "5": "tooth_5_the_counts_name_their_unit",
    },
}
BOOTSTRAP = REPO / "cairn" / "devices" / "recovery" / "bootstrap.sh"
FIRST_RUN = REPO / "cairn" / "devices" / "recovery" / "bootstrap_first_run.sh"
DEV = "fixture_wiring"
OTHER = "fixture_wiring_other"
FAILURES: list[str] = []
COUNTS = re.compile(r"^linked (\d+) already (\d+) left (\d+)$", re.M)


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:900]}", flush=True)
    if not ok:
        FAILURES.append(name)


def _stub(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$0\"\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class World:
    def __init__(self, verbs=("alpha",), other=("gamma",)) -> None:
        self.base = scratch_dir("testing-f0ffa0db0952-")
        self.repo = self.base / "repo"
        rec = self.repo / "cairn" / "devices" / "recovery"
        rec.mkdir(parents=True)
        shutil.copy2(BOOTSTRAP, rec / "bootstrap.sh")
        self.root = self.base / "instance"
        self.root.mkdir()
        self.cls = self.repo / "cairn" / "devices" / DEV / "0" / "bin"
        self.other_cls = self.repo / "cairn" / "devices" / OTHER / "0" / "bin"
        for v in verbs:
            _stub(self.cls / v)
        for v in other:
            _stub(self.other_cls / v)
        (self.cls / "notes.txt").write_text("not a verb\n")   # a file, not executable: never linked

    def inst(self, dev: str = DEV, n: str = "0") -> Path:
        return self.root / dev / n / "bin"

    def wire(self, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "CAIRN_INSTANCE_ROOT": str(self.root),
               "CAIRN_BOOT_LOG": str(self.base / "bootlog")}
        return subprocess.run(
            [_BASH, "-c", 'source "$1" >/dev/null 2>&1; cairn_wire_instances "${@:2}"', "_",
             str(self.repo / "cairn" / "devices" / "recovery" / "bootstrap.sh"), *args],
            capture_output=True, text=True, env=env, timeout=60)

    def done(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)


def _resolves(link: Path, target: Path) -> bool:
    return link.is_symlink() and link.resolve() == target.resolve()


def tooth_1() -> None:
    name = PROVES["f0ffa0db0952"]["1"]
    w = World()
    try:
        b = w.inst()
        b.mkdir(parents=True)
        (b / "alpha").symlink_to(w.cls / "alpha")
        before = os.lstat(b / "alpha").st_mtime_ns
        _stub(w.cls / "beta")
        r = w.wire()
        ok = (_resolves(b / "beta", w.cls / "beta") and _resolves(b / "alpha", w.cls / "alpha")
              and os.lstat(b / "alpha").st_mtime_ns == before and not (b / "notes.txt").exists())
        check(name, ok, f"listing={sorted(os.listdir(b))} rc={r.returncode} out={r.stdout!r} err={r.stderr[-300:]!r}")
    finally:
        w.done()


def tooth_2() -> None:
    name = PROVES["f0ffa0db0952"]["2"]
    w = World(verbs=("alpha", "beta"))
    try:
        b = w.inst()
        b.parent.mkdir(parents=True)
        b.symlink_to(w.cls)
        listing = sorted(os.listdir(w.cls))
        r = w.wire()
        after = sorted(os.listdir(w.cls))
        self_links = [n for n in after if (w.cls / n).is_symlink()]
        ok = after == listing and not self_links and b.is_symlink()
        check(name, ok, f"before={listing} after={after} self_links={self_links} out={r.stdout!r}")
    finally:
        w.done()


def tooth_3() -> None:
    name = PROVES["f0ffa0db0952"]["3"]
    w = World()
    try:
        b = w.inst()
        b.mkdir(parents=True)
        hand = b / "alpha"
        hand.write_bytes(b"#!/bin/sh\necho hand-placed\n")
        r = w.wire()
        m = COUNTS.search(r.stdout)
        ok = (not hand.is_symlink() and hand.read_bytes() == b"#!/bin/sh\necho hand-placed\n"
              and m is not None and int(m.group(3)) >= 1 and str(hand) in r.stderr)
        check(name, ok, f"out={r.stdout!r} err={r.stderr[-300:]!r}")
    finally:
        w.done()


def tooth_4() -> None:
    name = PROVES["f0ffa0db0952"]["4"]
    w = World(verbs=("alpha", "beta"))
    try:
        r = w.wire(DEV, "7")
        b7 = w.inst(DEV, "7")
        linked = sorted(os.listdir(b7)) if b7.is_dir() else []
        alone = (not w.inst(DEV, "0").exists() and not (w.root / OTHER).exists()
                 and not (w.root / "superclaude").exists())
        good = (r.returncode == 0 and linked == ["alpha", "beta"]
                and all(_resolves(b7 / v, w.cls / v) for v in linked) and alone)
        refusals = {}
        for args in (("notanumber",), (DEV, "notanumber"), (DEV, "-1"), ("nosuchdevice", "3")):
            snap = sorted(str(p) for p in w.root.rglob("*"))
            rr = w.wire(*args)
            created = sorted(str(p) for p in w.root.rglob("*")) != snap
            if rr.returncode == 0 or created or not rr.stderr.strip():
                refusals[" ".join(args)] = f"rc={rr.returncode} created={created} err={rr.stderr!r}"
        check(name, good and not refusals,
              f"rc={r.returncode} linked={linked} alone={alone} refusals={refusals} err={r.stderr[-200:]!r}")
    finally:
        w.done()


def tooth_5() -> None:
    name = PROVES["f0ffa0db0952"]["5"]
    w = World(verbs=("alpha", "beta", "delta"))
    try:
        b = w.inst()
        b.mkdir(parents=True)
        (b / "alpha").symlink_to(w.cls / "alpha")
        (b / "beta").write_text("hand\n")
        r = w.wire(DEV, "0")
        m = COUNTS.search(r.stdout)
        sums = m is not None and (int(m.group(1)), int(m.group(2)), int(m.group(3))) == (1, 1, 1)
        fr = FIRST_RUN.read_text()
        first_run_ok = "device(s)" not in fr
        check(name, sums and first_run_ok, f"out={r.stdout!r} first_run_says_devices={not first_run_ok}")
    finally:
        w.done()


def main() -> int:
    for t in (tooth_1, tooth_2, tooth_3, tooth_4, tooth_5):
        try:
            t()
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            check(PROVES["f0ffa0db0952"][t.__name__.split("_")[1]], False, f"{type(exc).__name__}: {exc}")
    print(f"{5 - len(FAILURES)} passed, {len(FAILURES)} failed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
