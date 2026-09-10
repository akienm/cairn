"""THE TOOL STANDS AT ITS OWN ADDRESS — ticket ``dd8ad9702b49`` (2026-09-09).

WHY THIS PROOF EXISTS, and it is a hollow reading's finding rather than a design idea.
``test_the_three_faces_resolve_a_shim_from_disk`` proves the CODE moved and still works, and
``cairn/tools/determinism/proofs/test_determinism`` proves the gate's directory came out pure.
Between them they left six of this build's own files with no declared tooth watching them:
``cairn test --hollow dd8ad9702b49`` reverted each and NOTHING went red —

    cairn/tools/bus_client/intention+why.json
    cairn/tools/bus_client/probes/a_client_reaches_and_never_beats.py
    cairn/tools/bus_client/history.json   cairn/tools/bus_client/state.json
    cairn/tools/base/history.json         cairn/tools/base/state.json

which is the exact shape Law 8 calls a hollow green: the two proofs are green whether those
files are there or not, so they are not evidence about them. The clearance gate refuses on it
by name (``hollow_file``), and that refusal is correct — "bus_client is its own tool, not a
lodger" is a claim about a CHARTER, a PROBE and a JOURNAL berthing at the new address, not only
about a module doing so. Those three are what this proof watches.

ONE DECLARED TOOTH, DELIBERATELY. A ticket's ``PROVES`` map is clause -> one tooth, and this
ticket's falsifier carries no ``(N)`` markers, so it is a single ``all`` clause and a proof can
declare exactly one tooth against it. Tooth i therefore asserts all three properties in one
run: any one of the six files reverted takes it red. The finer teeth below it are undeclared
and exist for the diagnostic surface (Law 7) — they say WHICH of the three failed without the
reader having to read a traceback.

WHAT IT DOES NOT DO: it never asserts a particular cursor VALUE. A proof over live records that
pinned "the standing is PROVEME" would go red at this ticket's own next crossing and at every
crossing after it. The invariant is that a component's ``state.json`` cursor IS the last entry
of its ``history.json`` — the projection agreeing with the record it is projected from — which
is true at every standing and false the moment either file is reverted alone.

Run:  python3 cairn/tools/bus_client/proofs/test_the_tool_stands_at_its_own_address.py
Seal: cairn test --seal cairn/tools/bus_client
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

# cairn/tools/bus_client/proofs/<this file> -> proofs -> bus_client -> tools -> cairn -> root
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# WHICH CLAUSE OF THE TICKET'S FALSIFIER EACH TOOTH PROVES — read by proof_coverage and by the
# hollow check. See the header: one clause, one declarable tooth, and tooth i is it.
PROVES = {
    "dd8ad9702b49": {
        "all": "test_i_every_address_this_build_wrote_is_load_bearing",
    }
}

TOOL = "cairn/tools/bus_client"
GATE = "cairn/tools/base"
CHARTER = TOOL + "/intention+why.json"
PROBE_PATH = TOOL + "/probes/a_client_reaches_and_never_beats.py"
PROBE_DOTTED = "cairn.tools.bus_client.probes.a_client_reaches_and_never_beats"

# The keys the cursor and the last journal entry must agree on. Not the whole record: the
# journal entry carries a `proved` list the projector does not copy, and demanding byte
# equality would red on a shape difference that means nothing.
MIRRORED = ("workflow", "standing", "from", "to", "direction", "at", "fingerprint")


def _charter_stands() -> str:
    path = _REPO_ROOT / CHARTER
    assert path.is_file(), (
        "the tool has no charter at its own address (%s) — a component without an intention "
        "does not run, and a tool that borrows its holder's charter is the lodger this ticket "
        "moved out" % CHARTER)
    try:
        charter = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise AssertionError("%s does not parse: %s" % (CHARTER, exc)) from exc
    assert charter.get("component") == "bus_client", (
        "the charter at %s names component %r — it must declare THIS tool, or it is somebody "
        "else's charter sitting at this address" % (CHARTER, charter.get("component")))
    for field in ("what", "why", "falsifier", "owner"):
        assert str(charter.get(field) or "").strip(), (
            "the charter at %s leaves %r empty — the filename forces the why, and an empty one "
            "is the blank field that forcing exists to stop" % (CHARTER, field))
    return "charter: %s declares component 'bus_client' with what/why/falsifier/owner filled" % CHARTER


def _probe_berths_with_what_it_watches() -> str:
    path = _REPO_ROOT / PROBE_PATH
    assert path.is_file(), (
        "the WATCHME probe is not at %s — a probe berths WITH what it watches, and this one "
        "watches the bus client, so leaving it in the gate's directory would be the lodging "
        "this ticket ended" % PROBE_PATH)
    try:
        module = importlib.import_module(PROBE_DOTTED)
    except BaseException as exc:                   # noqa: BLE001 — a broken probe is a red, not a crash
        raise AssertionError(
            "%s is on disk but does not import: %s: %s" % (PROBE_PATH, type(exc).__name__, exc)) from exc
    probe = getattr(module, "PROBE", None)
    assert probe is not None, "%s declares no module-level PROBE" % PROBE_PATH
    for face in ("carry", "enough"):
        assert callable(getattr(probe, face, None)), (
            "%s's PROBE carries no %s — the emission gate reads ARMED from both" % (PROBE_PATH, face))
    return "probe: %s imports and carries a PROBE with carry and enough" % PROBE_PATH


def _journal_mirrors_the_cursor(component: str) -> str:
    state_path = _REPO_ROOT / component / "state.json"
    hist_path = _REPO_ROOT / component / "history.json"
    for path in (state_path, hist_path):
        assert path.is_file(), (
            "%s has no %s — intent, state and proofs share an address (Law 5), and a component "
            "with no journal at its own address cannot say what is going on without leaving"
            % (component, path.name))
    try:
        cursor = (json.loads(state_path.read_text(encoding="utf-8")) or {}).get("cursor") or {}
        entries = json.loads(hist_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise AssertionError("%s's state or history does not parse: %s" % (component, exc)) from exc
    assert isinstance(entries, list) and entries, "%s/history.json holds no entries" % component
    last = entries[-1]
    disagree = [k for k in MIRRORED if cursor.get(k) != last.get(k)]
    assert not disagree, (
        "%s's cursor is not its journal's last entry — they disagree on %s. The cursor is a "
        "PROJECTION of the record; when the two differ, one of them was written by something "
        "other than the crossing door (cursor %r vs journal %r)"
        % (component, ", ".join(disagree),
           {k: cursor.get(k) for k in disagree}, {k: last.get(k) for k in disagree}))
    return "journal: %s's cursor mirrors its last history entry on %d field(s) (standing %r)" % (
        component, len(MIRRORED), last.get("standing"))


def test_i_every_address_this_build_wrote_is_load_bearing():
    """THE DECLARED TOOTH. Charter, probe and both ends' journals, in one run — see the header
    for why they are not three declared teeth."""
    lines = [_charter_stands(),
             _probe_berths_with_what_it_watches(),
             _journal_mirrors_the_cursor(TOOL),
             _journal_mirrors_the_cursor(GATE)]
    print("  PASS  test_i_every_address_this_build_wrote_is_load_bearing")
    for line in lines:
        print("          %s" % line)


def test_ii_the_charter_berths_at_the_tools_own_address():
    print("  PASS  test_ii_the_charter_berths_at_the_tools_own_address (%s)" % _charter_stands())


def test_iii_the_watchme_probe_moved_with_what_it_watches():
    print("  PASS  test_iii_the_watchme_probe_moved_with_what_it_watches (%s)"
          % _probe_berths_with_what_it_watches())


def test_iv_each_end_of_the_seam_carries_a_journal_that_mirrors_its_cursor():
    for component in (TOOL, GATE):
        print("  PASS  test_iv_each_end_of_the_seam_carries_a_journal_that_mirrors_its_cursor "
              "(%s)" % _journal_mirrors_the_cursor(component))


def check():
    """Every tooth runs whatever the one before it did — the declared tooth may not be hidden
    behind an earlier failure, or the hollow reading cannot tell "nothing checks this file"
    from "the run stopped before the tooth that does"."""
    failures = []
    for tooth in (test_i_every_address_this_build_wrote_is_load_bearing,
                  test_ii_the_charter_berths_at_the_tools_own_address,
                  test_iii_the_watchme_probe_moved_with_what_it_watches,
                  test_iv_each_end_of_the_seam_carries_a_journal_that_mirrors_its_cursor):
        try:
            tooth()
        except BaseException as exc:               # noqa: BLE001 — a red is a reading, not a crash
            failures.append(tooth.__name__)
            print("  RED  %s: %s: %s" % (tooth.__name__, type(exc).__name__, exc))
    if failures:
        print("RED: %d failing" % len(failures))
        return 1
    print("green — bus_client stands at its own address: its own charter, the WATCHME probe "
          "berthed with what it watches, and a journal at each end of the seam whose cursor is "
          "its own last entry")
    return 0


if __name__ == "__main__":
    raise SystemExit(check())
