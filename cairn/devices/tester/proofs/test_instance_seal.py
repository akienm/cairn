#!/usr/bin/env python3
"""A proof cannot seed the tree it reads — the instance seal, measured.

WHAT THIS DEFENDS. The tester is the one process that runs every component in the corpus.
Since 2026-08-18 every device emits its diagnostic trail without being wired
(``a-device-logs-without-being-wired``), so every proof the tester runs writes into
``~/.cairn/logs/``. Measured that evening: 2,080 records across eight devices, all of it
spanning SEVENTEEN MINUTES — the window of two corpus runs. The tree built to show what the
system does was showing only what the tester does, and the earlier instance of the same
defect (``test_askscan`` writing 15 of the prebuild ledger's first 19 rows) had already cost
a 4.75x inflation of an instrument's own denominator.

THE CLAIM, and it has two halves that pull against each other:
  - a proof WRITES nowhere in the live instance root, and
  - a proof READS the live instance root exactly as it would on the host.

The second half is not a convenience. The first build of this seal bound an EMPTY directory
over the instance root and turned seven proofs red — proofs that read the live corpus and
refuse, correctly and out loud, to go green over an empty one ("an invariant over an empty
corpus is a hollow green, and this assertion is the thing that says so"). An isolation that
blinds honest invariants has traded a measured defect for an unmeasured one. So the seal is
a SNAPSHOT, and both halves are teeth here.

THE POSITIVE CONTROL IS THE POINT OF THE FILE. A seal that reports SEALED because nothing
ever writes is indistinguishable from one that works, so this proof produces a real BREACHED
and a real INDETERMINATE, against a FAKE instance root, and asserts the detector names them.
Nothing here touches ``~/.cairn``, and the last tooth is the witness that says so.

Proof: exit 0 = green.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.tester import isolation as iso_mod          # noqa: E402
from cairn.devices.tester.device import TesterDevice           # noqa: E402
from cairn.devices.tester.scratch import scratch_dir           # noqa: E402
from cairn.devices.tester.isolation import (                   # noqa: E402
    BREACHED, INDETERMINATE, SEALED, NoIsolation, check_instance_seal,
    snapshot_instance_space, venvs_under_instance_space,
)

LIVE = Path.home() / ".cairn"

# A proof that writes into instance-space the ordinary way — through nothing special, just a
# path under the instance root, which is exactly how every device's trail gets written.
_WRITER = '''
from pathlib import Path
root = Path.home() / ".cairn"
(root / "logs" / "fixture_device" / "0").mkdir(parents=True, exist_ok=True)
(root / "logs" / "fixture_device" / "0" / "diagnostics.jsonl").write_text(
    '{"gate": "fixture", "at": "seeded-by-a-proof"}\\n')
(root / "SEEDED-BY-A-PROOF").write_text("if you can read this on the host, the seal failed")
raise SystemExit(0)
'''

# A proof that READS instance-space and refuses to pass over an empty one — the shape of the
# seven proofs the empty-room build broke, reduced to its smallest honest form.
_READER = '''
from pathlib import Path
root = Path.home() / ".cairn"
entries = sorted(p.name for p in root.iterdir())
assert "devices" in entries, f"read an empty world: {entries} — a hollow green"
print("SAW:" + ",".join(entries))
raise SystemExit(0)
'''


# Every path any fixture DECLARED it wrote, harvested from the seal's own report. This is the
# witness's attribution key: the seal already knows exactly what the subject wrote, so the
# question "did any of it reach the host" can be asked by name instead of by inference.
_DECLARED_WRITES: set = set()


def _run(fixture: Path) -> dict:
    """Run a fixture through the real path and harvest what the seal says it wrote."""
    v = TesterDevice().run_proof(fixture, sink="none")
    wrote = (v["evidence"].get("instance_seal") or {}).get("wrote_to_instance") or {}
    _DECLARED_WRITES.update(wrote.get("paths") or [])
    return v


def _fixture(body: str) -> Path:
    d = scratch_dir("instance-seal-fixture-")
    p = d / "fixture_proof.py"
    p.write_text(body, encoding="utf-8")
    return p


def _live_manifest() -> dict:
    """Every file under the live instance root as ``(size, sha256)``. The witness this whole
    file rests on.

    Venvs are excluded: they hold ~4,800 files that no tooth here can touch, and hashing them
    twice would make the witness cost more than everything it witnesses. The seal binds them
    READ-ONLY, so the kernel is the guarantee there, not this walk.
    """
    out = {}
    venvs = tuple(venvs_under_instance_space())
    for p in LIVE.rglob("*"):
        if p.is_symlink() or not p.is_file() or str(p).startswith(venvs):
            continue
        try:
            data = p.read_bytes()
            out[str(p)] = (len(data), hashlib.sha256(data).hexdigest())
        except OSError:
            out[str(p)] = (-1, "UNREADABLE")
    return out


def _classify(path: str, before: tuple, after: tuple) -> str:
    """``append`` if the old bytes are still the file's prefix, else ``rewrite``.

    USED TO REPORT AND TO SCAN, NEVER TO EXEMPT. It tells the witness where a changed file's
    new bytes begin, so the fingerprint scan reads only the tail of an append instead of the
    whole file, and it makes the closing line say what actually moved on the host.

    It is NOT an authorship test, and the first draft of this proof learned that the hard way
    by treating it as one: it asserted that concurrent writers only ever append, which sounded
    right and was false within one corpus run — ground_loop's ``liveness.json`` and
    sudo_relay's ``daemon.status`` are STATUS files, rewritten whole every beat. Shape does not
    identify a writer on a live host. Authorship is asked by name instead, against the paths
    the seal itself recorded the subject writing.
    """
    if after[0] >= before[0]:
        with open(path, "rb") as fh:
            if hashlib.sha256(fh.read(before[0])).hexdigest() == before[1]:
                return "append"
    return "rewrite"


# ── the two halves of the claim ──────────────────────────────────────────────


def test_a_proof_that_writes_to_instance_space_seeds_nothing_live():
    """The core tooth. A fixture proof writes a trail record and a top-level file the way any
    device would; neither may exist on the host afterwards."""
    v = _run(_fixture(_WRITER))
    assert v["verdict"] == "green", f"the fixture itself failed: {v['evidence']['stderr_tail']}"

    assert not (LIVE / "SEEDED-BY-A-PROOF").exists(), (
        "a proof's write reached the LIVE instance root — the seal did not hold, and this is "
        "the exact failure that filled the trail tree with 2,080 records of proof exhaust")
    assert not (LIVE / "logs" / "fixture_device").exists(), (
        "a proof seeded a device trail in the live logs tree")

    seal = v["evidence"]["instance_seal"]
    assert seal["verdict"] == SEALED, f"expected a sealed run, got {seal}"


def test_the_writes_are_MEASURED_not_merely_discarded():
    """The seal has to hold the writes somewhere in order to throw them away, so the record
    answers a question that had no instrument before: what does this proof write, and where?"""
    v = _run(_fixture(_WRITER))
    wrote = v["evidence"]["instance_seal"]["wrote_to_instance"]
    assert wrote["measured"] is True, wrote
    assert wrote["count"] >= 2, f"the fixture wrote two files; the record saw {wrote}"
    assert any(p.endswith("SEEDED-BY-A-PROOF") for p in wrote["paths"]), wrote["paths"]
    assert any("fixture_device" in p for p in wrote["paths"]), wrote["paths"]


def test_a_proof_still_READS_the_live_world():
    """The half the first build got wrong. Reads are not the defect; blinding them turns
    honest invariants into hollow greens, which is a worse instrument than the one we had."""
    v = _run(_fixture(_READER))
    assert v["verdict"] == "green", (
        "a proof reading the live instance root went red under the seal — the snapshot did "
        f"not carry the reads across: {v['evidence']['stdout_tail']}\n"
        f"{v['evidence']['stderr_tail']}")
    live_top = sorted(p.name for p in LIVE.iterdir())
    seen = next(ln[4:].split(",") for ln in v["evidence"]["stdout_tail"].splitlines()
                if ln.startswith("SAW:"))
    assert sorted(seen) == live_top, (
        f"the sealed world differs from the live one: sealed={sorted(seen)} live={live_top}")


def test_an_unsealed_run_reports_UNMEASURED_and_never_an_empty_list():
    """CP1. "We did not measure" and "we measured zero" are different facts, and a run that
    could not be sealed must not read like a clean one."""
    from cairn.devices.tester.device import _instance_writes
    assert _instance_writes(None, None)["measured"] is False
    assert "paths" not in _instance_writes(None, None), (
        "an unmeasured run must not carry an empty paths list — that reads as 'wrote nothing'")


# ── the detector is not vacuous: a real BREACHED and a real INDETERMINATE ─────
#
# Both run against a FAKE instance root, so the positive controls cost the live tree nothing.
# That is not squeamishness: an instrument that has to dirty the store to prove it is not
# dirtying the store would be the joke version of this seal.


def _with_fake_root(fake: Path):
    """Point the seal's notion of the instance root at ``fake``. Returns a restore callable."""
    original = iso_mod._INSTANCE_ROOT
    iso_mod._INSTANCE_ROOT = str(fake)
    return lambda: setattr(iso_mod, "_INSTANCE_ROOT", original)


class _LeakyIsolation(NoIsolation):
    """An isolation that ACCEPTS the swap and then ignores it — the shape of every way this
    could silently regress: a dropped flag, a refactor that loses the keyword, a subclass that
    forgets to pass it on. The seal must catch it by measuring, not by trusting the call."""

    def wrap(self, argv, cwd, *, instance_swap=None):
        return list(argv)


def test_a_seal_that_does_not_hold_is_reported_BREACHED():
    fake = scratch_dir("fake-instance-") / "cairn"
    (fake / "devices").mkdir(parents=True)
    (fake / "devices" / "marker").write_text("live")
    restore = _with_fake_root(fake)
    try:
        swap = snapshot_instance_space()
        seal = check_instance_seal(_LeakyIsolation(), swap, cwd=str(fake))
        assert seal.verdict == BREACHED, (
            f"a run whose swap was ignored must be BREACHED, got {seal.verdict}: {seal.detail}")
        assert seal.trustworthy is False, "a breached seal must never earn trust"
        leaked = [p.name for p in fake.iterdir() if p.name.startswith("instance-seal-probe")]
        assert leaked, "the probe's own marker should be sitting in the fake live root"
    finally:
        restore()


def test_a_seal_that_blinds_the_reads_is_INDETERMINATE_not_SEALED():
    """The regression tooth for the seven reds. An empty room hides the writes AND the reads,
    and the seal must refuse to call that a success — it is the failure it was built from."""
    fake = scratch_dir("fake-instance-") / "cairn"
    (fake / "devices").mkdir(parents=True)
    restore = _with_fake_root(fake)
    try:
        empty = str(scratch_dir("empty-swap-") / "cairn")
        Path(empty).mkdir(parents=True)
        seal = check_instance_seal(NoIsolation(), empty, cwd=str(fake))
        assert seal.verdict == INDETERMINATE, (
            f"an empty swap hides the live world from the subject; that is not SEALED "
            f"(got {seal.verdict}: {seal.detail})")
        assert "reads" in seal.detail.lower(), seal.detail
    finally:
        restore()


# ── the two things the seal has to keep working ──────────────────────────────


def test_every_venv_in_instance_space_is_found_and_bound_back():
    """A venv is an installed interpreter, not state. The interpreter running the subject
    LIVES in instance-space on this box, and a second one (aider_shim's) was found only when
    dropping it reded 28 of that device's teeth — so they are discovered by PEP 405's own
    definition, never by a roster someone has to remember to extend."""
    found = venvs_under_instance_space()
    assert found, "no venv found under instance-space — the discovery is broken, not the box"
    for v in found:
        assert (Path(v) / "pyvenv.cfg").exists(), f"{v} is not a venv by PEP 405"
    if str(LIVE) in str(Path(sys.executable).resolve()):
        assert any(str(Path(sys.executable).resolve()).startswith(v) for v in found), (
            "the interpreter running this proof lives in instance-space and was NOT found — "
            "binding a snapshot over the root would swap python out from under a running exec")

    flags = iso_mod.instance_bind_flags("/tmp/whatever")
    for v in found:
        assert ["--ro-bind", v, v] == flags[flags.index(v) - 1:flags.index(v) + 2], (
            f"{v} is not bound back read-only: {flags}")
    assert flags[0] == "--bind" and flags.index("--bind") < flags.index("--ro-bind"), (
        "the swap must go down BEFORE the venvs are bound back on top of it")


def test_the_subject_can_still_execute_and_import_inside_the_seal():
    """The bind is only correct if the world still works. This is what the aider_shim red
    actually measured, reduced to one tooth: a sealed subject must run and import."""
    v = _run(_fixture(
        "import sys, json, sqlite3, pathlib\n"
        "print('RAN', sys.executable)\n"
        "raise SystemExit(0)\n"))
    assert v["verdict"] == "green", v["evidence"]["stderr_tail"]
    assert "RAN" in v["evidence"]["stdout_tail"]


def _main() -> int:
    before = _live_manifest()

    checks = [
        test_a_proof_that_writes_to_instance_space_seeds_nothing_live,
        test_the_writes_are_MEASURED_not_merely_discarded,
        test_a_proof_still_READS_the_live_world,
        test_an_unsealed_run_reports_UNMEASURED_and_never_an_empty_list,
        test_a_seal_that_does_not_hold_is_reported_BREACHED,
        test_a_seal_that_blinds_the_reads_is_INDETERMINATE_not_SEALED,
        test_every_venv_in_instance_space_is_found_and_bound_back,
        test_the_subject_can_still_execute_and_import_inside_the_seal,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")

    # THE WITNESS, and it spans every tooth above — including the two that deliberately
    # produce a BREACHED. A proof of an isolation that itself leaked would be the most
    # expensive possible way to learn this lesson a third time.
    after = _live_manifest()
    added = sorted(set(after) - set(before))
    changed = sorted(k for k in set(after) & set(before) if after[k] != before[k])
    appended = [k for k in changed if _classify(k, before[k], after[k]) == "append"]
    rewritten = [k for k in changed if k not in appended]

    # (1) NO FILE WAS ADDED. Absolute, and it is the leak's own signature: every write the
    # fixtures make is a new path, so there is no benign reading of this one.
    assert not added, (
        f"THIS PROOF ADDED FILES TO THE LIVE INSTANCE ROOT: {added[:10]}")

    # (2) NOTHING THE SEAL SAW THE SUBJECT WRITE EXISTS ON THE HOST — asked BY NAME, using the
    # seal's own report as the attribution key rather than inferring authorship from the shape
    # of a change. This is the tooth that survives a busy host: it does not care what else
    # moved, only whether the subject's declared writes are among it.
    assert _DECLARED_WRITES, "no fixture declared a write — the attribution key is empty"
    for rel in sorted(_DECLARED_WRITES):
        assert not (LIVE / rel).exists(), (
            f"A WRITE THE SEAL RECORDED IS ON THE HOST: {LIVE / rel}\n"
            f"The seal reported holding it in the swap and it is here anyway — that is the "
            f"whole failure, stated by the instrument that was supposed to prevent it.")

    # (3) NO CHANGED FILE CARRIES A FIXTURE'S FINGERPRINT. This is the one that covers a leak
    # INTO an existing trail, which (1) cannot see and (2) only sees if the seal reported it.
    for path in changed:
        with open(path, "rb") as fh:
            if path in appended:
                fh.seek(before[path][0])
            body = fh.read().decode("utf-8", "replace")
        for token in ("SEEDED-BY-A-PROOF", "seeded-by-a-proof", "fixture_device"):
            assert token not in body, (
                f"A FIXTURE'S WRITE APPEARS IN A LIVE FILE: {token!r} in {path}")

    # WHAT THIS WITNESS DELIBERATELY DOES NOT ASSERT, and the honesty matters more than the
    # extra tooth would: it does not require the live root to be byte-identical. Three things
    # write here while this proof runs and none is the subject — the ground loop and sudo_relay
    # (daemons already running) and the TESTER ITSELF, which executes run_proof in this process,
    # unsealed, and logs that it ran. A first draft asserted "no rewrites, daemons only append"
    # and the very next corpus run measured it false: ground_loop's liveness.json and
    # sudo_relay's daemon.status are STATUS files, rewritten whole. The claim was tidy and
    # wrong. So the churn is REPORTED rather than forbidden, and the three teeth above are
    # aimed at authorship instead — which is the question actually being asked.
    print(f"  PASS  the live instance root is unleaked ({len(before)} files witnessed; "
          f"{len(_DECLARED_WRITES)} declared subject-write(s), none on the host; "
          f"{len(appended)} append(s) and {len(rewritten)} status rewrite(s) by the tester and "
          f"the running daemons, read and clean)")

    print("green — a proof writes nowhere in the live instance root and reads it exactly as "
          "the host does; the detector produces a real BREACHED and a real INDETERMINATE, so "
          "its SEALED means something")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
