"""A DEVICE NOBODY WIRED LEAVES A TRAIL — the proof of ticket ``a-device-logs-without-being-wired``.

WHAT WAS MEASURED THE DAY THIS WAS WRITTEN (2026-08-18), and it is the thing being closed: 17
components in class-space hold ``emit`` sites, and exactly TWO trails existed on disk. Not because
the mechanism was broken — ``BreadcrumbLog`` was built 2026-08-12 and its own proof is green — but
because reaching it required an assembly step nobody but ``ground_loop/__main__.py`` performed. The
other 15 marked every record ``home='held'`` and appended it to a list on an object inside a process
that was about to exit. Akien's question is what dissolved it: *"if every class inherits logging,
and the logging is writing to the correct tree, what is the role of a reciever?"*

WHY IT IS NOT HOLLOW (Law 8), and it is the same reason ``test_breadcrumb_log.py`` gives for the
same shape: THE CENTRAL TOOTH RUNS IN A CHILD PROCESS. A record that only exists in the emitting
process's memory is the exact failure being closed, so an in-process assertion would go green on
the failure itself. The child emits and exits; the parent reads the file. Nothing shared but the
disk.

AND THE DERIVATION IS MEASURED TWICE, NEVER ASSERTED ONCE. A device now derives its own name from
its class's module address, and a trail filed under a WRONG name would be worse than no trail — a
record of truth pointing at an owner that does not exist (Law 7). So the cheap string derivation
(``component_of_module``, a split, asked at every construction) is checked against the expensive
honest one (``component_of``, which walks the real tree) across every component in class-space.
Two independent derivations agreeing over the whole corpus is a measurement; one of them agreeing
with a name retyped in this file would be a fixture agreeing with its author.

THE PROOF DOES NOT WRITE TO THE LIVE TREE, and does not merely say so. Every device it constructs
is pointed at a temp world through ``set_diagnostic_roots``, and a BEFORE/AFTER byte witness over
``~/.cairn/logs`` is one of the teeth — because the failure being fixed here is precisely "the
default writes without being asked", which is one wrong ``roots`` away from a proof that seeds the
instrument it is about to read.

    python3 cairn/tools/base/proofs/test_device_logs_unwired.py     # exit 0 = green
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.address import (  # noqa: E402
    ROOTS,
    component_dirs,
    component_of,
    component_of_module,
    log_path,
)
from cairn.tools.base.breadcrumb_log import RECORD_NAME, BreadcrumbLog  # noqa: E402
from cairn.tools.base.diagnostic import DiagnosticBase  # noqa: E402

_PASSES: list[str] = []


def ok(condition, why: str) -> None:
    if not condition:
        raise AssertionError(why)
    _PASSES.append(why)


def _roots(tmp: Path) -> dict:
    return {"repo": _REPO_ROOT, "commons": _REPO_ROOT.parent / "CairnCommons", "instance": tmp}


class _Rungless(DiagnosticBase):
    """Defined in a proof, so its module sits under no rung — the honest-absence case."""

_Rungless.__module__ = "__main__"


# ── 1. THE ADDRESS ───────────────────────────────────────────────────────────

def test_log_path_is_the_ruled_shape() -> None:
    """``instance/logs/<device>/<instance>`` — Akien 2026-08-18, verbatim shape."""
    tmp = Path("/nowhere-this-proof-never-touches-disk")
    p = log_path("some_device", 3, {"repo": tmp, "commons": tmp, "instance": tmp})
    ok(p == tmp / "logs" / "some_device" / "3",
       f"log_path resolves instance/logs/<device>/<instance>; got {p}")
    ok(log_path("d", roots={"repo": tmp, "commons": tmp, "instance": tmp}) == tmp / "logs" / "d" / "0",
       "the instance segment is never optional — a singleton is 0, not an omission")


def test_the_logs_root_is_not_the_state_root() -> None:
    """The two addresses answer different questions and must not collapse into one.

    ``instance_path`` is where a device keeps what is TRUE of it (its own, its own to gate);
    ``log_path`` is where it writes what HAPPENED. If these ever returned the same path the
    30-day sweep would be deleting device state, which is the whole reason they are separate."""
    from cairn.tools.base.address import instance_path
    tmp = Path("/nowhere")
    r = {"repo": tmp, "commons": tmp, "instance": tmp}
    ok(log_path("bus", 0, r) != instance_path("bus", 0, r),
       "the logs tree and a device's state space must be different addresses — the sweep "
       "deletes one of them wholesale")


# ── 2. THE DERIVATION, MEASURED AGAINST THE REAL TREE ────────────────────────

def test_derivation_agrees_with_the_tree_walk_corpus_wide() -> None:
    """Every component in class-space: the cheap split and the honest walk name it the same.

    No component name is typed in this file. The population is whatever ``component_dirs``
    finds today, so a component added tomorrow is covered without touching this proof."""
    components, unreadable = component_dirs()
    ok(not unreadable, f"the component walk hit unreadable entries: {unreadable}")
    ok(len(components) > 20,
       f"the census must actually see the tree — HollowScan's lesson; found {len(components)}")
    disagreements = []
    for c in components:
        rel = c.relative_to(_REPO_ROOT)
        dotted = ".".join(rel.parts) + ".some_module"
        derived = component_of_module(dotted)
        walked = component_of(c)
        if derived != c.name or walked is None or walked.name != c.name:
            disagreements.append({"component": str(rel), "split_says": derived,
                                  "walk_says": str(walked)})
    ok(not disagreements,
       f"the string derivation and the tree walk must name every component identically; "
       f"{len(disagreements)} disagree: {disagreements[:5]}")
    _PASSES.append(f"  (population: {len(components)} components, both derivations agreeing)")


def test_real_device_classes_name_their_own_component() -> None:
    """The two devices that HAD hand-spelled names now derive them, and the derived name is
    checked against where the class's file actually lives — not against the string that used
    to be in the runner, which is gone precisely because this works."""
    from cairn.devices.bus.bus import BusDevice
    from cairn.devices.ground_loop.loop import GroundLoopDevice
    import inspect
    for cls in (BusDevice, GroundLoopDevice):
        derived = component_of_module(cls.__module__)
        home = component_of(Path(inspect.getfile(cls)))
        ok(home is not None and derived == home.name,
           f"{cls.__name__} derives {derived!r} but its file lives in {home}")
        ok(issubclass(cls, DiagnosticBase),
           f"{cls.__name__} must carry the emit surface structurally")


def test_a_rungless_class_gets_no_invented_name() -> None:
    """Under no rung, no name — and therefore no trail, rather than a trail filed under a
    device that does not exist."""
    ok(_Rungless().diagnostic_device is None,
       "a class defined outside the rungs must not be given a component name")


# ── 3. THE HEART: UNWIRED, ANOTHER PROCESS, ON DISK ──────────────────────────

_CHILD = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from cairn.tools.base.diagnostic import DiagnosticBase

# A class whose MODULE PATH is a real component's, faked the only honest way — by telling the
# class where it lives, which is the same string Python would have given it had this file been
# saved there. Nothing else is wired: no receiver, no log, no address.
class Dev(DiagnosticBase):
    pass
Dev.__module__ = "cairn.devices.bus.bus"

tmp = Path(sys.argv[2])
dev = Dev()
dev.set_diagnostic_roots({"repo": tmp, "commons": tmp, "instance": tmp})
rec = dev.emit("subscribe", pointer="ticket/nobody-wired-me", values={"pid": "child"})
assert rec["home"] == "sent", rec
assert dev.held_diagnostics() == [], dev.held_diagnostics()
print(rec["ts"])
"""


def test_an_unwired_device_reaches_disk_from_another_process() -> None:
    """THE TOOTH. No ``set_diagnostic_receiver`` anywhere in the child. The child exits; the
    file is read by this process."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        child = subprocess.run([sys.executable, "-c", _CHILD, str(_REPO_ROOT), str(tmp)],
                               capture_output=True, text=True)
        ok(child.returncode == 0,
           f"the child process must emit cleanly; stderr:\n{child.stderr}")
        ts = child.stdout.strip()
        trail = tmp / "logs" / "bus" / "0" / RECORD_NAME
        ok(trail.exists(),
           f"an unwired device's trail must exist at {trail} after the process that wrote it "
           f"has exited — this is the whole ticket")
        lines = [json.loads(x) for x in trail.read_text().splitlines() if x.strip()]
        ok(len(lines) == 1, f"exactly one record, got {len(lines)}")
        ok(lines[0]["ts"] == ts,
           "the record read back must be the one the dead process wrote, byte for byte")
        ok(lines[0]["gate"] == "subscribe" and lines[0]["home"] == "sent",
           f"the crossing and its home must survive the process: {lines[0]}")


def test_the_trail_is_appended_never_rewritten() -> None:
    """Two emissions, two lines, first one unchanged — a record of truth (Law 7)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        dev = _Rungless()
        dev.set_diagnostic_roots(_roots(tmp))
        dev.set_diagnostic_receiver(BreadcrumbLog("bus", 0, roots=_roots(tmp)))
        dev.emit("first", pointer="a")
        first = (tmp / "logs" / "bus" / "0" / RECORD_NAME).read_text()
        dev.emit("second", pointer="b")
        both = (tmp / "logs" / "bus" / "0" / RECORD_NAME).read_text()
        ok(both.startswith(first), "an already-written line is never rewritten")
        ok(len(both.splitlines()) == 2, "one line per crossing")


# ── 4. WHAT THE RECEIVER STILL DOES ──────────────────────────────────────────

def test_silence_is_still_askable_and_is_not_the_unwired_state() -> None:
    """``set_diagnostic_receiver(None)`` HOLDS. Never calling it WRITES. The two used to be the
    same state and now are not, which is the sentinel's entire job."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        silenced = _Rungless()
        silenced.__class__.__module__  # (no name; force the explicit path below)
        silenced.set_diagnostic_roots(_roots(tmp))
        silenced.set_diagnostic_receiver(None)
        rec = silenced.emit("gate", pointer="p")
        ok(rec["home"] == "held", f"a silenced device holds; got {rec['home']}")
        ok(len(silenced.held_diagnostics()) == 1, "and the record is retrievable, not dropped")

        class Named(DiagnosticBase):
            pass
        Named.__module__ = "cairn.devices.trouble.trouble"
        writer = Named()
        writer.set_diagnostic_roots(_roots(tmp))
        ok(writer.emit("gate", pointer="p")["home"] == "sent",
           "the same class NOT silenced must write — else the sentinel proves nothing")
        ok((tmp / "logs" / "trouble" / "0" / RECORD_NAME).exists(),
           "and it lands under its own derived name")


def test_the_override_still_diverts() -> None:
    """The receiver's one surviving job: send a stream somewhere else entirely."""
    caught: list[dict] = []

    class Catcher:
        def receive_diagnostic(self, record):
            caught.append(record)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        class Named(DiagnosticBase):
            pass
        Named.__module__ = "cairn.devices.bus.bus"
        dev = Named()
        dev.set_diagnostic_roots(_roots(tmp))
        dev.set_diagnostic_receiver(Catcher())
        dev.emit("gate", pointer="p")
        ok(len(caught) == 1, "an overridden receiver receives")
        ok(not (tmp / "logs" / "bus" / "0" / RECORD_NAME).exists(),
           "and the default trail is NOT also written — an override replaces, it does not tee")


def test_computing_an_address_creates_nothing() -> None:
    """Construction touches no disk (``address``'s own bound, Law 6: provisioning is a
    different act). A device that never emits must leave no directory behind, or the logs tree
    becomes a census of what exists instead of a record of what happened."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        class Named(DiagnosticBase):
            pass
        Named.__module__ = "cairn.devices.librarian.library"
        dev = Named()
        dev.set_diagnostic_roots(_roots(tmp))
        ok(dev.diagnostic_device == "librarian", "the name resolves without touching disk")
        BreadcrumbLog("librarian", 0, roots=_roots(tmp))
        ok(not (tmp / "logs").exists(),
           "neither the device nor the log may create anything before the first write")


# ── 5. THIS PROOF DOES NOT SEED THE INSTRUMENT ───────────────────────────────

def _live_logs_witness() -> list[tuple[str, int]]:
    live = ROOTS["instance"] / "logs"
    if not live.exists():
        return []
    return sorted((str(p.relative_to(live)), p.stat().st_size)
                  for p in live.rglob("*") if p.is_file())


def main() -> int:
    before = _live_logs_witness()
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    after = _live_logs_witness()
    ok(before == after,
       "THIS PROOF WROTE INTO THE LIVE LOGS TREE. The whole change under test is 'a device "
       "writes without being asked', so a proof that forgets a temp roots table seeds the "
       "instrument it is about to read. Diff: "
       f"{[x for x in after if x not in before]}")
    print("\n".join(f"  PASS  {p}" for p in _PASSES))
    print(f"\nGREEN — {len(_PASSES)} assertions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
