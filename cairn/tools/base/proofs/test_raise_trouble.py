"""Proof: ANY component can raise a trouble WITHOUT holding the trouble device.

Ticket 9579a6f9cec6 — a-device-reaches-trouble-over-the-bus-never-by-import.

THE SHAPE BEING PROVED, in Akien's words on the day it was ratified: SENDING IS A TOOL,
HOLDING IS OWNED. Raising is append-only, needs no addressee and no running recipient, so
it lives on the mixin every device already composes — a breadcrumb under the raiser's own
log home, exactly the ``BreadcrumbLog`` shape everything else emits into. Holding is a
read-modify-write over a shared store, so it stays behind one owner's gate (Law 6).

WHAT A HOLLOW BUILD PASSES THAT THIS FILE DOES NOT LET IT. The obvious hollow version of
this ticket is a ``raise_trouble`` that imports the trouble device lazily inside the
function body: every caller looks clean, ``grep`` goes quiet, and the isolation sieve goes
green while nothing whatsoever has changed about who holds the store. So the central tooth
here does not read the source for an import statement — it raises from a fixture class
defined in THIS file, in a process where ``cairn.devices`` has never been imported, and
asserts on ``sys.modules`` that raising did not drag the device in. A lazy import would
red it.

The second thing a hollow build gets away with is a raise that carries nothing: an empty
identity means two occurrences of one defect cannot be recognised as one, and an empty why
means the ticket that lands is a shrug (CP3). Both are refused AT THE FLOOR here, by the
raiser, rather than draining into a store where nobody can act on them.

    python3 -m pytest cairn/tools/base/proofs/test_raise_trouble.py -q   # exit 0 = green
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# WHICH TICKET CLAUSES THESE TEETH COVER (read by cairn/tools/proof_coverage, ticket
# feeb4c786b14). Clause (3) of 9579a6f9cec6 asks for exactly what this file is: a tools/base
# proof that raises from a fixture device holding nothing of cairn.devices, and watches the
# emission land in the raiser's OWN log home. The ticket's other clauses are served in
# trouble's own proof — a seam has ends in more than one component, and the crossing names
# every proof it is proved by.
PROVES = {
    "9579a6f9cec6": {"3": "test_the_emission_lands_in_the_RAISERS_OWN_log_home"},
}

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.address import log_path
from cairn.tools.base.diagnostic import DiagnosticBase, ModuleRaiser, TroubleRaiseRefused


def _roots(tmp) -> dict:
    return {k: Path(tmp) for k in ("repo", "commons", "instance")}


class _FixtureDevice(DiagnosticBase):
    """A component that composes the mixin and imports NOTHING from ``cairn.devices``.

    Its ``diagnostic_device`` is given rather than derived because a class defined inside a
    proof sits under no rung, and the base is deliberately honest about that: an underived
    name means the record HOLDS rather than being filed under an invented owner. That
    honesty is right and it is also not what this proof is measuring, so the fixture says
    who it is."""

    @property
    def diagnostic_device(self) -> str:
        return "a_fixture_component"


def _raises_in(tmp, device="a_fixture_component") -> list[dict]:
    home = Path(log_path(device, 0, _roots(tmp)))
    if not home.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(home.glob("*.raise_trouble.json"))]


# ── the central tooth ───────────────────────────────────────────────────────────

def test_raising_does_not_pull_the_trouble_DEVICE_into_the_process():
    """THE TOOTH THE HOLLOW BUILD FAILS. A lazy import inside ``raise_trouble`` would
    satisfy every grep in the ticket's falsifier and change nothing about who holds the
    store. So this asserts the RUNTIME fact instead of the source fact: raise, then look
    at what is loaded.

    Run in a subprocess because this test session has already imported half the corpus —
    the assertion is only meaningful in a process that had no reason to load the device."""
    with tempfile.TemporaryDirectory() as tmp:
        script = f'''
import json, sys
sys.path.insert(0, {str(_REPO_ROOT)!r})
from pathlib import Path
from cairn.tools.base.diagnostic import DiagnosticBase

class D(DiagnosticBase):
    @property
    def diagnostic_device(self): return "a_fixture_component"

d = D()
d.set_diagnostic_roots({{k: Path({tmp!r}) for k in ("repo", "commons", "instance")}})
d.raise_trouble("a-fixture-defect", why="the raise must need no device")
leaked = sorted(m for m in sys.modules if m.startswith("cairn.devices"))
print(json.dumps(leaked))
'''
        out = subprocess.run([sys.executable, "-c", script], capture_output=True,
                             text=True, timeout=120)
        assert out.returncode == 0, out.stderr
        leaked = json.loads(out.stdout.strip().splitlines()[-1])
        assert leaked == [], (
            f"raising loaded device modules: {leaked} — a lazy import is the hollow build "
            f"this ticket exists to refuse, and it passes every grep in the falsifier")

        # ...and the raise still LANDED. Without this half the tooth above is satisfied by
        # a raise_trouble that does nothing at all.
        landed = _raises_in(tmp)
        assert len(landed) == 1, landed
        assert landed[0]["pointer"] == "a-fixture-defect"
        assert landed[0]["values"]["why"] == "the raise must need no device"


# ── the emission lands in the raiser's OWN home ─────────────────────────────────

def test_the_emission_lands_in_the_RAISERS_OWN_log_home():
    """Not trouble's home, and not a shared spool. The raiser's own address is what lets
    the drain say WHO raised each fold, and it is the same address every other breadcrumb
    that component writes already uses — one trail per component, not one per lane."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _FixtureDevice()
        d.set_diagnostic_roots(_roots(tmp))
        d.raise_trouble("some-defect", why="a why", detail={"n": 1})

        landed = _raises_in(tmp)
        assert len(landed) == 1, landed
        rec = landed[0]
        assert rec["values"]["detail"] == {"n": 1}
        assert not (Path(tmp) / "logs" / "trouble").exists(), (
            "the raise wrote into trouble's log home — the raiser writes its own")


def test_the_gate_is_in_the_FILENAME_so_the_drain_reads_only_raises():
    """The drain globs ``*.raise_trouble.json`` rather than opening every breadcrumb a
    device ever wrote. That is only affordable because the gate is in the name, so it is
    asserted here rather than assumed there."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _FixtureDevice()
        d.set_diagnostic_roots(_roots(tmp))
        d.emit("some_other_gate", pointer="not-a-raise")
        d.raise_trouble("a-defect", why="a why")

        home = Path(log_path("a_fixture_component", 0, _roots(tmp)))
        assert len(list(home.glob("*.json"))) == 2, sorted(p.name for p in home.glob("*.json"))
        assert len(list(home.glob("*.raise_trouble.json"))) == 1, (
            "the glob the drain uses does not separate raises from other breadcrumbs")


def test_filename_order_IS_write_order():
    """THE WATERMARK DEPENDS ON THIS. The drain remembers how far it got as the highest
    filename it folded, and skips names ``<=`` it — which is a correct resume only if
    sorting names sorts by time. The stamp is UTC to the microsecond and leads the name,
    so it does; asserted here because the drain's correctness rests on it and nothing else
    in the corpus states it."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _FixtureDevice()
        d.set_diagnostic_roots(_roots(tmp))
        for i in range(8):
            d.raise_trouble(f"defect-{i}", why=f"why {i}")

        home = Path(log_path("a_fixture_component", 0, _roots(tmp)))
        by_name = [json.loads(p.read_text(encoding="utf-8"))["pointer"]
                   for p in sorted(home.glob("*.raise_trouble.json"))]
        assert by_name == [f"defect-{i}" for i in range(8)], by_name


# ── refusals at the floor ───────────────────────────────────────────────────────

@pytest.mark.parametrize("identity,why", [
    ("", "a real why"),
    ("   ", "a real why"),
    ("a-defect", ""),
    ("a-defect", "   "),
])
def test_a_raise_without_an_IDENTITY_or_a_WHY_is_refused_HERE(identity, why):
    """REFUSED AT THE FLOOR, not drained into a ticket nobody can act on.

    The identity names the DEFECT, which is the only thing that makes a second occurrence
    the SAME trouble as the first — an empty one turns fifty flaps into fifty tickets, the
    exact failure the damping exists to prevent. The why is CP3: a fault with no reason is
    not a report, it is a shrug. Both were already refused by ``TroubleDevice``; refusing
    them again here is not duplication, because the raiser and the holder are now different
    hands and a raise refused only at the far end is a raise that already landed on disk."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _FixtureDevice()
        d.set_diagnostic_roots(_roots(tmp))
        with pytest.raises(TroubleRaiseRefused):
            d.raise_trouble(identity, why=why)
        assert _raises_in(tmp) == [], "a refused raise still wrote an emission"


# ── the poke ────────────────────────────────────────────────────────────────────

def test_an_UNWIRED_notifier_still_lands_the_record():
    """The ordinary state, and it must cost LATENCY rather than the record. Nobody is
    wired in a bare ``python3 -m`` run of the inspector, and that is precisely when a
    finding most needs to survive."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _FixtureDevice()
        d.set_diagnostic_roots(_roots(tmp))
        rec = d.raise_trouble("a-defect", why="a why")
        assert "held for the beat" in rec["poke"], rec
        assert len(_raises_in(tmp)) == 1


def test_a_WIRED_notifier_is_poked_with_the_record():
    with tempfile.TemporaryDirectory() as tmp:
        seen = []
        d = _FixtureDevice()
        d.set_diagnostic_roots(_roots(tmp))
        d.set_trouble_notifier(seen.append)
        rec = d.raise_trouble("a-defect", why="a why")
        assert rec["poke"] == "sent", rec
        assert len(seen) == 1 and seen[0]["pointer"] == "a-defect"


def test_a_REFUSING_notifier_does_not_cost_the_RECORD():
    """The record is already on disk before the poke is attempted, and the order is the
    design: the poke is an optimisation on WHEN the lane notices, never the path by which
    it notices. A raiser that lost the fault because the recipient was down would be the
    silent failure this whole lane exists to end (Law 7) — so the failure is written INTO
    the returned record instead of being raised over the top of a landed measurement."""
    with tempfile.TemporaryDirectory() as tmp:
        def refuse(_record):
            raise OSError("the lane is down")

        d = _FixtureDevice()
        d.set_diagnostic_roots(_roots(tmp))
        d.set_trouble_notifier(refuse)
        rec = d.raise_trouble("a-defect", why="a why")
        assert rec["poke"].startswith("refused: OSError"), rec
        assert len(_raises_in(tmp)) == 1, "a refused poke cost us the record"


# ── the module raiser ───────────────────────────────────────────────────────────

def test_a_MODULE_raiser_files_under_the_component_it_NAMES():
    """``build_inspector`` and the tester's ``validation_store`` are functions, not
    objects, so they carry no class whose module address names them. A throwaway subclass
    would derive whatever module happened to define it — and a class under no rung gets no
    trail at all, which means the record HOLDS in a process about to exit."""
    with tempfile.TemporaryDirectory() as tmp:
        ModuleRaiser("build_inspector", roots=_roots(tmp)).raise_trouble(
            "a-finding", why="a why")
        landed = _raises_in(tmp, device="build_inspector")
        assert len(landed) == 1, landed
        assert landed[0]["source"] == "build_inspector", (
            f"the record says {landed[0]['source']!r} — a class name here would name this "
            f"helper rather than whoever spoke")


def test_an_UNNAMED_module_raiser_is_refused():
    with pytest.raises(ValueError):
        ModuleRaiser("")


if __name__ == "__main__":
    # NAMED, not counted. ``pytest.main([__file__, "-q"])`` — what stood here until
    # 2026-09-07 — runs every tooth honestly and prints dots, so the seal records
    # ``teeth_green: []`` and no ticket clause can ever be declared against this file.
    # Clause (3) of 9579a6f9cec6 is declared against it above.
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
