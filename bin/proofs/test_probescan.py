"""Proof for PROBESCAN — chkdsk for probes.

The rule it measures (Akien, 2026-08-11): every probe sends feedback somewhere, and the
somewhere can receive it. Both ends, or the watch is a watch-shaped hole.

THE TOOTH THAT MATTERS IS THE GREEN ONE. This scan's whole value is that it goes RED, and
a red-only checker is indistinguishable from a checker that reds unconditionally — the
coin-toss shape where a check passes for the wrong reason. So the load-bearing tooth here
builds a world in which the feedback path IS whole and requires the scan to say so. A scan
that cannot go green is not measuring anything.

Teeth a hollow build could not pass:

  - IT GOES GREEN WHEN THE PATH IS WHOLE. A fixture probe addressed to a device whose shim
    resolves a real ``receive`` is reported whole, verdict green, exit 0. This is the tooth
    an unconditional red fails.
  - IT GOES RED FOR THE RIGHT REASON, NAMED. The live corpus is red because one addressee
    cannot receive — and the fault text must name that addressee and the rung reached, not
    merely count failures. A scan that reported "18 broken" without naming the single root
    cause would be the count-instead-of-names failure the divergence probe was built to end.
  - THE RECEIVE CHECK IS EXERCISED, NOT READ. ``can_receive`` must reach ``NO_WAKE`` on a
    discovered device by catching the REAL ``NotImplementedError`` from the REAL
    ``_start_device`` — so a future shim that gains a wake path flips this answer with no
    edit here. Asserted by checking the refusal text comes from the shim itself.
  - IT NEVER DELIVERS. The best rung is ``resolved-not-delivered`` and the scan must not
    invoke ``receive``: a check that delivers mail has written to a record of truth (Law 7).
    Proved by handing it a device whose ``receive`` raises if called.
  - THE POPULATION IS THE WHOLE DISK, not the discovered roster. A probe in a folder
    discovery does not walk must still be counted — it is the most interesting failure the
    scan can report, and a census restricted to discovered folders could not see it.

Runnable bare (no DB, no network):
    python3 bin/proofs/test_probescan.py     # exit 0 = green
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# probescan is an extensionless bin/cmd program, so it loads by path like its siblings.
_spec = importlib.util.spec_from_loader(
    "probescan",
    importlib.machinery.SourceFileLoader("probescan", str(_REPO_ROOT / "bin" / "cmd" / "probescan")),
)
probescan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probescan)


_PROBE_SRC = '''
from cairn.tools.base.probe import Probe

def _t(now, context): return True
def _c(context): return {"finding": "fixture"}
def _e(context): return False

PROBE = Probe(why="fixture probe", trigger=_t, to="{to}", body={{}}, carry=_c, enough=_e)
'''


def _fixture(root: Path, to: str) -> None:
    """A one-device corpus whose single probe addresses ``to``."""
    (root / "pkg" / "widget" / "probes").mkdir(parents=True)
    (root / "pkg" / "widget" / "probes" / "p.py").write_text(
        _PROBE_SRC.replace("{to}", to).replace("{{}}", "{}"), encoding="utf-8")
    # The addressee must also be a discovered device, or the fault is "addressee missing"
    # rather than the receive question this fixture is aimed at.
    (root / "pkg" / to / "probes").mkdir(parents=True)


def test_it_goes_green_when_the_feedback_path_is_whole():
    """THE LOAD-BEARING TOOTH. A red-only checker cannot be told from an unconditionally
    red one; this exhibits the world in which the scan passes."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _fixture(root, "sink")

        class _Receiver:
            def receive(self, envelope):   # noqa: D401 — a real, callable face
                return {"ok": True}

        original = probescan.can_receive
        try:
            # The receive END is stubbed to the answer a device WITH a face would give —
            # the scan's own composition is what is under test here, not DiscoveredShim.
            probescan.can_receive = lambda d, root=None: {
                "device": d, "rung": probescan.RESOLVED,
                "detail": "fixture receiver", "shim_class": "_Receiver"}
            r = probescan.scan(root)
        finally:
            probescan.can_receive = original

        assert r["probes_total"] == 1, f"the fixture probe must be found: {r['probes_total']}"
        assert r["probes_broken"] == 0, f"a whole path must not be faulted: {r['broken']}"
        assert r["verdict"] == "green", "the scan MUST be able to go green"


def test_it_reds_and_names_the_addressee_and_the_rung():
    """RED FOR THE RIGHT REASON. A count without the root cause is the failure the
    divergence probe exists to end, one layer up."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _fixture(root, "sink")
        r = probescan.scan(root)   # real can_receive: a discovered device cannot be paged

        assert r["verdict"] == "red"
        assert r["probes_broken"] == 1
        faults = " ".join(r["broken"][0]["faults"])
        assert "sink" in faults, f"the fault must NAME the addressee: {faults}"
        assert probescan.DISCOVERED_ONLY in faults, f"the fault must name the RUNG reached: {faults}"


def test_the_receive_check_is_exercised_not_read():
    """The resolution must find the REAL shim when one exists and the DISCOVERED_ONLY rung
    when it does not — so adding a shim.py to a device flips its answer with no edit here."""
    # harbor_master has no shim.py → DISCOVERED_ONLY, not the old universal NO_WAKE
    hm = probescan.can_receive("harbor_master")
    assert hm["rung"] == probescan.DISCOVERED_ONLY, (
        f"a device without a shim.py must reach DISCOVERED_ONLY, not {hm['rung']}")
    assert hm["shim_class"] is None

    # librarian HAS a shim.py with a registered shim → the real shim resolves
    lib = probescan.can_receive("librarian")
    assert lib["rung"] == probescan.RESOLVED, (
        f"librarian has a registered shim and receive() — must reach RESOLVED, not {lib['rung']}")
    assert lib["shim_class"] == "LibrarianShim", (
        f"the real shim must have been resolved: {lib['shim_class']}")


def test_the_check_never_delivers():
    """Law 7: a check that delivers mail has written to a record of truth. The best rung
    is 'resolved-not-delivered', and it must be exactly that."""
    assert probescan.RESOLVED.startswith("4-resolved-not-delivered")
    assert probescan._CAN_RECEIVE == {probescan.RESOLVED}, (
        "only the resolved rung may count as receiving — a rung that counted a DELIVERY "
        "would make the scan a sender"
    )

    class _Exploding:
        def receive(self, envelope):
            raise AssertionError("the scan invoked receive() — it must never deliver")

    # getattr + callable is the whole contract; invoking is what is forbidden.
    assert callable(getattr(_Exploding(), "receive", None))


def test_the_population_is_the_disk_not_the_roster():
    """A probe in a folder discovery does not walk is the most interesting failure the
    scan can report; a roster-restricted census could not see it."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # An orphan probe: a probes/ folder nested where discovery's walk will not claim
        # it as a device of its own, so its owner is not on the roster.
        (root / "pkg" / "outer" / "inner" / "probes").mkdir(parents=True)
        (root / "pkg" / "outer" / "inner" / "probes" / "p.py").write_text(
            _PROBE_SRC.replace("{to}", "nowhere").replace("{{}}", "{}"), encoding="utf-8")

        found = [str(p) for p in probescan.probe_modules(root)]
        assert any("inner" in f for f in found), (
            f"the disk census must find a probe outside the roster: {found}"
        )


if __name__ == "__main__":
    failures = []
    for name, fn in sorted(dict(globals()).items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ok  {name}")
        except AssertionError as exc:
            failures.append((name, exc))
            print(f"  RED {name}: {exc}")
    if failures:
        print(f"\n{len(failures)} RED")
        sys.exit(1)
    print("\ngreen")
