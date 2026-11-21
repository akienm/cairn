#!/usr/bin/env python3
"""Proof for ticket 83eaa778101e: an instance seal swaps on a disk, not on a tmpfs, unless its
caller names a temp dir.

MEASURED 2026-11-20 on akiendelllinux: /tmp is a 7.7G tmpfs, and every instance seal copies the
live instance root twice (the batch's pristine snapshot, then the proof's swap), ~1.4G, into the
default temp dir, no caller naming one. The long-running processes started by systemd-run (the
bus, the ground loop, the superclaude sessions) carry no TMPDIR, so every seal they start lands
in RAM, and two at once filled /tmp ("No space left on device").

Teeth, one per falsifier clause. Each drives ``snapshot_instance_space`` over a small scratch
instance root (``isolation._INSTANCE_ROOT`` pointed at it), and reads the filesystem of what it
made from /proc/self/mountinfo, an instrument this proof carries itself.
  (1) TMPDIR unset: the pristine snapshot and the swap are made on a dir that is not a tmpfs;
  (2) TMPDIR unset, and the default temp dir a tmpfs too small for one snapshot (a sized fake:
      a read-only dir that the subject's mountinfo seam names a tmpfs): two concurrent seals of
      a ~1.5M root both complete;
  (3) TMPDIR set by the caller: the swap is made under it.

Linux only: mountinfo is Linux's.

    bin/cairn test cairn/devices/tester/proofs/test_an_instance_seal_swaps_on_a_disk.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"83eaa778101e": {
    "1": "test_with_tmpdir_unset_the_snapshot_and_swap_are_not_on_a_tmpfs",
    "2": "test_two_concurrent_seals_complete_over_a_small_tmpfs_default",
    "3": "test_a_tmpdir_the_caller_names_is_honored",
}}

FAILURES: list[str] = []
# The scratch lives on a named disk dir, never the default temp dir, which tooth 1 measures.
SCRATCH_PARENT = "/var/tmp"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def fs_type(path: str) -> str:
    """The filesystem type of the mount holding ``path``, read from /proc/self/mountinfo."""
    real = os.path.realpath(path)
    best, kind = "", "?"
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left, _, right = line.partition(" - ")
        point = left.split()[4].replace("\\040", " ")
        inside = real == point or real.startswith(point.rstrip("/") + "/")
        if inside and len(point) >= len(best):
            best, kind = point, right.split()[0]
    return kind


def make_root(base: Path, size: int) -> Path:
    root = base / "instance"
    (root / "devices" / "x" / "0").mkdir(parents=True)
    (root / "devices" / "x" / "0" / "blob").write_bytes(b"\0" * size)
    return root


CHILD = r"""
import os, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import cairn.devices.tester.isolation as I
I._INSTANCE_ROOT, tempfile.tempdir, I._MOUNTINFO = sys.argv[2], sys.argv[3], sys.argv[4]
swap = I.snapshot_instance_space()
print("swap", swap, flush=True)
shutil.rmtree(Path(swap).parent, ignore_errors=True)
"""


def _seal_once(I, root: Path) -> tuple[str, str]:
    """(pristine dir, swap dir) of one seal over ``root``, made in-process and then removed."""
    saved = I._INSTANCE_ROOT
    I._INSTANCE_ROOT = str(root)
    try:
        I._drop_pristine()
        swap = I.snapshot_instance_space()
        pristine = I._pristine["dir"]
        return pristine, swap
    finally:
        I._INSTANCE_ROOT = saved


def _clean(I, swap: str | None) -> None:
    if swap:
        shutil.rmtree(Path(swap).parent, ignore_errors=True)
    I._drop_pristine()


def tooth_1(I, base: Path) -> None:
    os.environ.pop("TMPDIR", None)
    tempfile.tempdir = None
    root = make_root(base / "t1", 4096)
    swap = None
    try:
        pristine, swap = _seal_once(I, root)
        kinds = {"pristine": fs_type(pristine), "swap": fs_type(swap)}
        check(PROVES["83eaa778101e"]["1"], "tmpfs" not in kinds.values(),
              # The default temp dir as the subject itself resolved it: swap_root() asked the
              # tempfile module with tempdir None and TMPDIR unset, which caches the answer in
              # tempfile.tempdir, so this reads the subject's reach and makes none of its own.
              f"pristine={pristine} swap={swap} kinds={kinds} default={tempfile.tempdir}"
              f" ({fs_type(tempfile.tempdir) if tempfile.tempdir else '?'})")
    finally:
        _clean(I, swap)


def tooth_2(base: Path) -> None:
    # The sized fake: the default temp dir is a scratch dir with a cap of 0 (read-only), and the
    # subject's mountinfo seam names it a tmpfs. An unprivileged mount of a real small tmpfs is
    # refused inside the tester's own sandbox (measured 2026-11-20: "unshare failed: Operation
    # not permitted"), so the cap is a permission and the tmpfs is a mountinfo line.
    root = make_root(base / "t2", 1_500_000)
    small = base / "small-default"
    small.mkdir()
    real = Path("/proc/self/mountinfo").read_text()
    fake = base / "mountinfo"
    fake.write_text(real + f"999 1 0:999 / {small} rw,nosuid - tmpfs tmpfs rw,size=1024k\n")
    small.chmod(0o500)
    env = {k: v for k, v in os.environ.items() if k not in ("TMPDIR", "TEMP", "TMP")}
    script = base / "child.py"
    script.write_text(CHILD)
    argv = [sys.executable, str(script), str(REPO), str(root), str(small), str(fake)]
    try:
        kids = [subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True) for _ in (1, 2)]
        outs = [k.communicate(timeout=600)[0] for k in kids]
    finally:
        small.chmod(0o700)
    rcs = [k.returncode for k in kids]
    check(PROVES["83eaa778101e"]["2"], rcs == [0, 0],
          f"rcs={rcs} outs={[o[-300:] for o in outs]!r}")


def tooth_3(I, base: Path) -> None:
    named = base / "named-tmp"
    named.mkdir()
    os.environ["TMPDIR"] = str(named)
    tempfile.tempdir = None
    root = make_root(base / "t3", 4096)
    swap = None
    try:
        pristine, swap = _seal_once(I, root)
        under = all(Path(p).resolve().is_relative_to(named.resolve()) for p in (pristine, swap))
        check(PROVES["83eaa778101e"]["3"], under, f"named={named} pristine={pristine} swap={swap}")
    finally:
        _clean(I, swap)
        os.environ.pop("TMPDIR", None)
        tempfile.tempdir = None


def main() -> int:
    if not sys.platform.startswith("linux"):
        print("SKIP: Linux only (mountinfo is Linux's)")
        return 0
    caller_tmpdir = os.environ.get("TMPDIR")
    # Through the scratch door (ticket f92d213f7dd0), placed on SCRATCH_PARENT: the door makes its
    # dir under tempfile's current dir, so that is pointed at the disk dir for this one call.
    from cairn.tools.scratch.scratch import scratch_dir
    saved, tempfile.tempdir = tempfile.tempdir, SCRATCH_PARENT
    try:
        base = Path(scratch_dir("testing-swap-on-disk-"))
    finally:
        tempfile.tempdir = saved
    try:
        # Bound at call time: a world without the subject reds every tooth by name.
        import cairn.devices.tester.isolation as I
        for t in (lambda: tooth_1(I, base), lambda: tooth_2(base), lambda: tooth_3(I, base)):
            try:
                t()
            except Exception as exc:  # noqa: BLE001 — a tooth that crashed is a red, named
                check(f"(a tooth crashed: {exc!r})", False)
    finally:
        shutil.rmtree(base, ignore_errors=True)
        if caller_tmpdir is not None:
            os.environ["TMPDIR"] = caller_tmpdir
        tempfile.tempdir = None
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
