"""Proof: code outside codemother asks build_inspector's judges through inspect_wire, and the
CodeMother that answers is a separate process launched with her roots (tickets 7ea59855b1f4,
0c2c3f53c2be).

Code outside codemother may not import the inspector (RULE 1), and outline 9.4.3.3.4 (Q#88)
puts the answer on the bus. 7ea59855b1f4 gave outside proofs ``ask`` and a fixture world, but
ask held CodeMother's shim in the asking process and the fixture wrote her inspector's globals.
0c2c3f53c2be makes inspect_wire a plain tool: ask reaches a CodeMother held by a bus process
under a scratch HOME (the cairn device's scratch_bus.launch), and ``launch`` names her roots by
her environment at launch.

Teeth that ride a bus need Postgres on 5432; on a box without it they read red here and the
Linux sealer's run is the seal (outline 9.4.8.1). Every answer is compared in JSON-normal form,
json.loads(json.dumps(x, default=str)), on BOTH sides: the bus is JSON, and the codec is not
taught to rebuild a judge's returned tuple (0c2c3f53c2be D7; measured on akiendelllinux at
44e86aa7c: the_nest answered [(1, [...])] directly and [[1, [...]]] over ask).

7ea59855b1f4:
  1. ask answers equal to the direct call for an allow-listed judge on a fixture charter.
  2. A judge off the allow-list raises InspectRefused naming it; a judge that raised over the
     bus raises again carrying its type name.
  3. Two asks in one process mint one scratch bus.
  4. Every name the ticket adds is answered over ask, never refused as off the list, and the
     ones that take no fixture answer equal to the direct call.
  5. Inside ``launch``, a chart judge asked over the bus reads the berths named; after the
     block its bus answers nothing and an ask reads the default world again.
0c2c3f53c2be:
  1. inspect_wire carries the codec, InspectRefused, ask and launch, and imports nothing under
     cairn.devices.codemother; the old address is gone and nothing imports it.
  2. ask answers from a CodeMother held by a bus process that is not the asking one, and the
     asking process never imports codemother's shim.
  3. launch names all three roots in the launch environment, and fixture is gone.

    python3 cairn/tools/inspect_wire/proofs/test_ask_reaches_a_launched_codemother.py
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "7ea59855b1f4": {
        "1": "test_ask_answers_as_the_direct_call",
        "2": "test_a_refusal_raises_naming_the_judge",
        "3": "test_two_asks_mint_one_scratch_bus",
        "4": "test_every_added_name_is_answered",
        "5": "test_a_launch_world_stands_behind_her_inspector_and_goes",
    },
    "0c2c3f53c2be": {
        "1": "test_inspect_wire_is_a_plain_tool_and_the_old_address_is_gone",
        "2": "test_ask_answers_from_another_process_and_never_imports_her_shim",
        "3": "test_launch_names_every_root_by_environment_and_fixture_is_gone",
    },
}

_TID = "fa1e7ea5a5c0"   # a fixture ticket id; no live ticket carries it
ADDED = ("claim_provenance", "proofs_exist", "constraint_enforcement_holds",
         "crossing_fingerprints_verified", "the_nest", "declared_runners", "_workflow_cursor",
         "proof_covers_the_ticket", "buildme_rides_the_rehearsal", "build_started",
         "_source_fingerprint", "sieve_names", "run_sieve", "proven_space")


def _jn(x):
    """JSON-normal form: what a JSON wire can carry (D7)."""
    return json.loads(json.dumps(x, default=str))


def _wire():
    from cairn.tools.inspect_wire import inspect_wire
    return inspect_wire


def _insp():
    return importlib.import_module("cairn.machines.build_inspector.inspector")


def _charter_dir() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    d = scratch_dir("inspect_ask_charter_")
    (d / "intention+why.json").write_text(json.dumps(
        {"component": "fixture", "claim_provenance": {}}), encoding="utf-8")
    return d


def test_ask_answers_as_the_direct_call():
    d = _charter_dir()
    row = {"component": "fixture"}
    direct = _insp().claim_provenance(row, d)
    assert direct, "the fixture charter has an empty claim_provenance, so the sieve must red it"
    got = _wire().ask("claim_provenance", row, d)
    assert _jn(got) == _jn(direct), (got, direct)


def test_a_refusal_raises_naming_the_judge():
    w = _wire()
    try:
        w.ask("not_a_judge_anyone_listed")
    except w.InspectRefused as exc:
        assert exc.judge == "not_a_judge_anyone_listed" and exc.raised is None, vars(exc)
        assert "not_a_judge_anyone_listed" in str(exc), str(exc)
    else:
        raise AssertionError("an unlisted judge was answered")
    try:
        w.ask("run_sieve", "no_sieve_has_this_name")
    except w.InspectRefused as exc:
        assert exc.raised == "KeyError", vars(exc)
        assert "no_sieve_has_this_name" in exc.reason, exc.reason
    else:
        raise AssertionError("run_sieve on an unregistered name answered instead of raising")


def test_two_asks_mint_one_scratch_bus():
    w = _wire()
    w.ask("sieve_names")
    first = w._HELD["bus"]
    w.ask("proven_space")
    assert w._HELD["bus"] is first and w._HELD["minted"] == 1, w._HELD


def test_every_added_name_is_answered():
    # Asked with no arguments, a listed judge either answers or raises its own TypeError over
    # the bus (``raised`` names it); only a name off the list is refused with raised None.
    insp, w = _insp(), _wire()
    off = []
    for name in ADDED:
        try:
            w.ask(name)
        except w.InspectRefused as exc:
            if exc.raised is None:
                off.append((name, exc.reason))
    assert not off, f"refused as unlisted over ask: {off}"
    wf = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
    for judge, args in (("sieve_names", ()), ("proven_space", ()), ("the_nest", ()),
                        ("declared_runners", ()), ("_workflow_cursor", (wf,))):
        assert _jn(w.ask(judge, *args)) == _jn(getattr(insp, judge)(*args)), judge
    assert "PROVED" in w.ask("proven_space") and "BUILDME" not in w.ask("proven_space")


def test_a_launch_world_stands_behind_her_inspector_and_goes():
    from cairn.tools.bus_client.remote import exchange
    from cairn.tools.scratch.scratch import scratch_dir
    w = _wire()
    berths, tickets = scratch_dir("inspect_ask_berths_"), scratch_dir("inspect_ask_tickets_")
    roots = {"repo": str(tickets), "commons": str(tickets)}
    with w.launch(berths=berths, tickets_root=tickets, crossing_roots=roots) as bus:
        home = bus._home
        findings = w.ask("buildme_rides_the_chart", _TID)
        assert findings and findings[0]["values"]["searched"] == str(berths), findings
        assert w._HELD["bus"] is bus, "an ask inside the block rode another world"
    try:
        exchange({"op": "stats"}, home, timeout=5)
    except OSError:
        pass
    else:
        raise AssertionError(f"the launch world's bus at {home} still answers after its block")
    plain = w.ask("buildme_rides_the_chart", _TID)
    assert plain and plain[0]["values"]["searched"] != str(berths), plain


def test_inspect_wire_is_a_plain_tool_and_the_old_address_is_gone():
    import ast
    import subprocess
    w = _wire()
    for name in ("wire_encode", "wire_decode", "InspectRefused", "ask", "launch"):
        assert hasattr(w, name), name
    tree = ast.parse(Path(w.__file__).read_text(encoding="utf-8"))
    reach = [n for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
             for n in ([a.name for a in node.names] if isinstance(node, ast.Import)
                       else [node.module or ""])
             if n.startswith("cairn.devices.codemother")]
    assert not reach, f"inspect_wire imports codemother: {reach}"
    assert not (_REPO_ROOT / "cairn/devices/codemother/tools/inspect_wire").exists()
    hits = subprocess.run(["git", "-C", str(_REPO_ROOT), "grep", "-l", "-E", "-e",
                           r"(from|import) cairn[.]devices[.]codemother[.]tools[.]inspect_wire",
                           "--", "*.py"],
                          capture_output=True, text=True).stdout.split()
    assert not hits, f"still importing the old address: {hits}"


def test_ask_answers_from_another_process_and_never_imports_her_shim():
    import subprocess
    child = ("import json, os, sys\n"
             "from cairn.tools.inspect_wire import inspect_wire as w\n"
             "names = w.ask('sieve_names')\n"
             "st = w._HELD['bus'].stats()\n"
             "print(json.dumps({'pid': os.getpid(), 'bus_pid': st['pid'], 'held': st['held'],\n"
             "                  'shim': 'cairn.devices.codemother.shim' in sys.modules,\n"
             "                  'names': bool(names)}))\n")
    from cairn.tools.scratch.scratch import home_env, scratch_dir
    env = home_env(scratch_dir("inspect_ask_child_"), PYTHONPATH=str(_REPO_ROOT))
    done = subprocess.run([sys.executable, "-c", child], env=env, capture_output=True,
                          text=True, timeout=600, cwd=str(_REPO_ROOT))
    assert done.returncode == 0, done.stderr[-1500:]
    got = json.loads(done.stdout.strip().splitlines()[-1])
    assert got["names"], got
    assert got["bus_pid"] != got["pid"], ("CodeMother answered in the asking process", got)
    assert "codemother" in got["held"], got
    assert got["shim"] is False, ("the asking process imported codemother's shim", got)


def test_launch_names_every_root_by_environment_and_fixture_is_gone():
    w = _wire()
    env = w._launch_env("/b", "/t", lambda: {"repo": "/r", "commons": "/c"})
    assert env == {"CAIRN_BUILD_INSPECTOR_CHART_BERTHS": str(Path("/b")),
                   "CAIRN_BUILD_INSPECTOR_TICKETS_ROOT": str(Path("/t")),
                   "CAIRN_BUILD_INSPECTOR_CROSSING_ROOTS": json.dumps({"repo": "/r", "commons": "/c"})}, env
    assert w._launch_env(None, None, None) == {}
    assert set(w.ROOT_ENV.values()) == set(_insp().ROOT_ENV.values()), \
        "the tool and the inspector name the roots differently"
    assert not hasattr(w, "fixture"), "fixture still stands"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
