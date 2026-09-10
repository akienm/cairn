"""THE THREE FACES RESOLVE A SHIM FROM DISK — ticket ``dd8ad9702b49`` (2026-09-09).

This is the PROVED gate the ticket bound at cast, in its own words: *"a proof beside
cairn/tools/bus_client that its three faces resolve a shim from disk and that every
importer in class-space imports at the new address (run, not grepped)."* Both halves
are here, and the parenthesis is the design of the second one: a grep says a file
contains a string, and the thing being claimed is that nineteen call sites across
thirteen files still WORK at the new address. Only running them says that.

WHY A PROOF AND NOT A NOTE THAT THE MOVE WAS A ``git mv``. The module's bytes did not
change, so the tempting argument is that nothing can have broken. That argument is
exactly wrong here, and the voyage measured why twice: the moved proof carried SIX
load-bearing path strings where the survey counted five, and four live import sites
lived in extensionless bash shims that no ``--include=*.py`` sweep could see. A move
is not a no-op when the address is data.

WHAT "FROM DISK" MEANS, and it is the property the whole tool rests on: a device's
bus presence IS ``<device folder>/shim.py``. No registry, no flag, no roster to keep
in sync — the file is the declaration. So tooth i plants a device that did not exist,
watches the loader find it, deletes the file, and watches the loader lose it. If the
loader ever consulted anything but disk, one of those two halves would not move.

TOOTH iii IS A REGRESSION TOOTH AND IS NOT DECORATIVE. Ticket ``8754ae677af6`` (the
voyage immediately before this one) measured ``reach("harbor_master")`` raising
LookupError because this loader spelled the address ``cairn.devices.<name>.shim``
while discovery derives a device from the parent of ANY ``probes/`` folder at any
depth. The harbor is a machine held by the cairn device; the two disagreed about
exactly one device and it was that one. Nothing else in the corpus is nested that
way, so the case has one member and it is the case that broke.

Run:  python3 cairn/tools/bus_client/proofs/test_the_three_faces_resolve_a_shim_from_disk.py
Seal: cairn test --seal cairn/tools/bus_client
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

# cairn/tools/bus_client/proofs/<this file> -> proofs -> bus_client -> tools -> cairn -> root
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# THE MODULE, NOT THE PACKAGE, AND THAT IS NOT A STYLE CHOICE. ``cairn.tools.bus_client``
# re-exports the public faces, but ``_wire`` calls ``_load_device_shim`` through its OWN
# module global — so a recording wrapper installed on the package would be invisible to the
# code under test, and tooth ii would pass while measuring nothing. ``_CLASS_ROOT`` lives
# here too. The faces reached this way are the same objects the package hands out.
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402


class _LazyModule:
    """``cairn.tools.bus_client.bus_client`` resolved at CALL time, never at import time.

    MEASURED NECESSARY 2026-09-09 BY THE HOLLOW READING OF THIS BUILD. Bound at import, the
    module under test is a load-bearing name in the proof's own header — so when `cairn test
    --hollow` reverted ``bus_client.py`` (absent before the build) this file raised
    ModuleNotFoundError before its first tooth and printed NO teeth at all. The clearance gate
    reads that as ``hollow_unreadable``, and it is right to: "the proof crashed" and "no tooth
    checks this file" are different answers, and a run that cannot reach a check has measured
    nothing. A proof has to survive its subject being taken away in order to say anything about
    whether that subject is load-bearing.

    __setattr__ forwards too, because the teeth monkeypatch ``_CLASS_ROOT`` and
    ``_load_device_shim`` on the module object itself — a proxy that only read would leave those
    writes on the proxy, where ``_wire``'s own module global would never see them, and tooth ii
    would pass while measuring nothing.
    """

    def __getattr__(self, name):
        return getattr(importlib.import_module("cairn.tools.bus_client.bus_client"), name)

    def __setattr__(self, name, value):
        setattr(importlib.import_module("cairn.tools.bus_client.bus_client"), name, value)


bus_client = _LazyModule()

# The live device the faces are exercised against. `cc` is chosen for one measured
# reason: `reach("cc")` costs 0.03s on this machine (2026-09-09), against 0.96s for
# `trouble` and ~23.5s for a face that beats. A proof that cost a heartbeat would be
# a proof nobody runs, and the thing under test here is shim RESOLUTION, which every
# device pays identically.
LIVE_DEVICE = "cc"

# WHICH CLAUSE OF THE TICKET'S FALSIFIER EACH TOOTH PROVES — read by proof_coverage and by
# the hollow check. The falsifier carries no ``(N)`` markers, so it is ONE clause covering
# the whole DONE-when, and it is served from TWO ends: the determinism proof answers "test_q
# passes and base shows no llm edge", this one answers "the importers resolve". Both declare
# ``all``; the coverage reader takes a clause as covered when ANY declarer is green, so the
# two are more evidence rather than a conflict to adjudicate.
PROVES = {
    "dd8ad9702b49": {
        "all": "test_v_every_importer_in_class_space_imports_at_the_new_address",
    }
}

OLD_DOTTED = "cairn.tools.base.bus_client"
OLD_PATH = "cairn/tools/base/bus_client"
NEW_DOTTED = "cairn.tools.bus_client"


def _plant(root: Path, device_id: str) -> Path:
    """Write a minimal device on disk: a probes/ folder (what discovery reads) and a
    shim.py declaring one BaseShim subclass (what the loader reads).

    The planted tree mirrors class-space exactly — ``<root>/cairn/devices/<id>/`` — because
    the loader builds a DOTTED path from the layout and then imports it. A flatter fixture
    would resolve to a name the real ``cairn.devices`` package could not host, and the tooth
    would be measuring an import error instead of a lookup."""
    folder = root / "cairn" / "devices" / device_id
    (folder / "probes").mkdir(parents=True)
    (folder / "probes" / "__init__.py").write_text("")
    (folder / "__init__.py").write_text("")
    shim = folder / "shim.py"
    shim.write_text(
        "from cairn.tools.base.shim import BaseShim\n"
        "\n"
        "\n"
        "class PlantedShim(BaseShim):\n"
        "    device_id = %r\n" % device_id)
    return shim


def test_i_a_shim_planted_on_disk_is_found_and_a_deleted_one_is_lost():
    """The file IS the declaration: plant it and the loader finds it; delete it and the
    loader loses it. Nothing else changes between the two halves."""
    # THROUGH THE DOOR, NOT THROUGH tempfile — a proof reaches the system temp directory only
    # via scratch_dir, which registers its own removal (ticket nothing-observes-the-host; 3581
    # leaked entries measured 2026-08-03). Caught here by test_scratch's corpus tooth on the
    # first run of this file, which is the tooth doing exactly its job.
    tmp = scratch_dir("cairn-busclient-plant-")
    device_id = "a_planted_device_that_only_this_proof_creates"
    shim_file = _plant(tmp, device_id)
    real_root = bus_client._CLASS_ROOT
    bus_client._CLASS_ROOT = tmp
    # THE PLANTED DEVICE HAS TO BE IMPORTABLE AS ``cairn.devices.<id>``, and ``cairn.devices``
    # is already imported from the repo — so a bare sys.path entry would never be consulted
    # for that name. Lending the real package a second search path is how a namespace gets a
    # tenant without moving anybody: the loader's own import is unmodified and does the work.
    import cairn.devices as _devices_pkg
    _devices_pkg.__path__.append(str(tmp / "cairn" / "devices"))
    try:
        dotted = bus_client._device_shim_module(device_id)
        assert dotted == "cairn.devices.%s.shim" % device_id, \
            "the loader did not resolve a planted device from disk: %r" % (dotted,)

        loaded = bus_client._load_device_shim(device_id, bus=None)
        assert loaded is not None, "a planted shim.py declaring a BaseShim yielded no shim"
        assert type(loaded).__name__ == "PlantedShim", \
            "the loader instantiated %r, not the class the planted file declares" % (
                type(loaded).__name__,)
        origin = Path(sys.modules[type(loaded).__module__].__file__).resolve()
        assert origin == shim_file.resolve(), \
            "the class came from %s, not from the file on disk at %s" % (origin, shim_file)

        # Now take the file away. Same name, same root, same everything else.
        shim_file.unlink()
        for mod in [m for m in sys.modules if m.startswith("cairn.devices.%s" % device_id)]:
            del sys.modules[mod]
        assert bus_client._device_shim_module(device_id) is None, \
            "the loader still resolved a device whose shim.py is gone — it is reading " \
            "something other than disk"
        assert bus_client._load_device_shim(device_id, bus=None) is None, \
            "the loader still built a shim for a device whose shim.py is gone"
    finally:
        bus_client._CLASS_ROOT = real_root
        _devices_pkg.__path__.remove(str(tmp / "cairn" / "devices"))
        for mod in [m for m in sys.modules if m.startswith("cairn.devices.%s" % device_id)]:
            del sys.modules[mod]
    print("  PASS  test_i_a_shim_planted_on_disk_is_found_and_a_deleted_one_is_lost")


def test_ii_all_three_faces_go_to_disk_for_the_named_device():
    """connect_bus, reach and connect_system each resolve the named device through the one
    loader, and the object they register is the class declared in that device's shim.py.

    RECORDED, not smoothed: connect_bus and connect_system are called with ``beat=False``.
    They are the RUNNER's faces and a beat costs ~23.5s here; what is under test is shim
    resolution, which happens in ``_wire`` before any pulse. ``reach`` takes no beat flag
    because it never beats — that is its whole contract (ticket fc93d8cd5961), and the
    probe beside this one reds any client that calls the other two."""
    seen = []
    real_loader = bus_client._load_device_shim

    def recording(device_name, bus):
        got = real_loader(device_name, bus)
        seen.append((device_name, got))
        return got

    bus_client._load_device_shim = recording
    try:
        for face, call in (
                ("connect_bus", lambda: bus_client.connect_bus(devices=[LIVE_DEVICE], beat=False)),
                ("reach", lambda: bus_client.reach(LIVE_DEVICE)),
                ("connect_system", lambda: bus_client.connect_system(devices=[LIVE_DEVICE], beat=False)),
        ):
            before = len(seen)
            result = call()
            assert result is not None, "%s handed back nothing" % face
            new = seen[before:]
            assert [n for n, _ in new] == [LIVE_DEVICE], \
                "%s resolved %r, not the one device it was given" % (face, [n for n, _ in new])
            shim = new[0][1]
            assert shim is not None, "%s resolved no shim for %r" % (face, LIVE_DEVICE)
            origin = Path(sys.modules[type(shim).__module__].__file__).resolve()
            expected = (_REPO_ROOT / "cairn" / "devices" / LIVE_DEVICE / "shim.py").resolve()
            assert origin == expected, \
                "%s built its shim from %s, not from %s" % (face, origin, expected)
    finally:
        bus_client._load_device_shim = real_loader
    print("  PASS  test_ii_all_three_faces_go_to_disk_for_the_named_device")


def test_iii_a_device_nested_under_a_machine_resolves_where_discovery_says():
    """The harbor_master regression (ticket 8754ae677af6): a device whose folder is not
    ``cairn/devices/<name>/`` must still resolve, because discovery derives device-ness from
    the parent of a probes/ folder at ANY depth."""
    dotted = bus_client._device_shim_module("harbor_master")
    assert dotted == "cairn.devices.cairn.machines.harbor_master.shim", \
        "the loader resolved harbor_master to %r — the assumed shape is back and the " \
        "concrete HarborMasterShim has zero callers again" % (dotted,)
    expected = (_REPO_ROOT / "cairn" / "devices" / "cairn" / "machines"
                / "harbor_master" / "shim.py")
    assert expected.is_file(), "the address this tooth pins does not exist on disk: %s" % expected
    print("  PASS  test_iii_a_device_nested_under_a_machine_resolves_where_discovery_says")


def test_iv_reach_refuses_a_name_no_shim_answers_to():
    """The loud half of "the file is the declaration": no file, no shim, and reach says so
    with the address it looked at rather than timing out into silence."""
    ghost = "a_device_name_that_no_shim_on_this_disk_answers_to"
    try:
        bus_client.reach(ghost)
    except LookupError as e:
        assert ghost in str(e), "the refusal did not name the device asked for: %s" % e
        assert "shim.py" in str(e), \
            "the refusal did not name the address it looked at, so it teaches nothing: %s" % e
    else:
        raise AssertionError("reach(%r) returned a bus for a device that does not exist" % ghost)
    print("  PASS  test_iv_reach_refuses_a_name_no_shim_answers_to")


def _docstring_nodes(tree):
    """Every Constant node that is a docstring — the first statement of a module, class or
    function. Prose recording where a module CAME FROM is not a call site, and a tooth that
    could not tell the two apart would force the corpus to forget its own history in order to
    stay green."""
    out = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            out.add(id(body[0].value))
    return out


def _names_the_old_address(text: str) -> bool:
    """True when python source names the departed address in a way that RUNS: an import of the
    old module, or a string literal outside a docstring carrying the old dotted or file path.

    A plain text search cannot make this cut, and the cut is the whole point — the moved probe
    carries its roster as string literals (live, and they were rewritten) while three modules
    carry the old address in prose (historical, and they must not be). Parsing is what tells a
    path the interpreter will follow from a sentence about the past."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return OLD_DOTTED in text or OLD_PATH in text
    docstrings = _docstring_nodes(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(OLD_DOTTED):
            return True
        if isinstance(node, ast.Import) and any(a.name.startswith(OLD_DOTTED) for a in node.names):
            return True
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docstrings \
                and (OLD_DOTTED in node.value or OLD_PATH in node.value):
            return True
    return False


def _import_targets():
    """Every file under class-space, bin/ and skills/ that names bus_client, paired with the
    dotted module paths it imports. Records are excluded by kind, not by guesswork:
    history.json and state.json are journals of what happened, validations/ are seals, and
    __pycache__ is derived — none of them is a call site."""
    roots = [_REPO_ROOT / "cairn", _REPO_ROOT / "bin", _REPO_ROOT / "skills"]
    hits = []
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            parts = path.parts
            if "__pycache__" in parts or "validations" in parts:
                continue
            # RECORDS ARE EXCLUDED BY KIND, NOT BY GUESSWORK. history.json and state.json are
            # journals of what happened; intention+why.json is a charter, and this tool's own
            # charter names the old address ON PURPOSE — the move IS its provenance. None of
            # the three is a call site, and rewriting a record to make an instrument green
            # would be the record lying about the past to flatter the present (Law 7).
            if path.name in ("history.json", "state.json", "intention+why.json"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "bus_client" not in text:
                continue
            hits.append((path, text))
    return hits


def test_v_every_importer_in_class_space_imports_at_the_new_address():
    """RUN, NOT GREPPED — the gate's own parenthesis. Every module that reaches for the bus
    client is imported for real, and the old dotted path may not appear as a live import
    anywhere.

    The two extensionless bash shims are the reason this walks all file kinds rather than
    ``*.py``: cairn/devices/codemother/0/bin/codemother and cairn/devices/trouble/0/bin/trouble
    carry embedded python imports, and the sweep that authored this ticket's survey could not
    see them. What is checked for a non-python file is that the dotted path it names IMPORTS —
    the same standard, reached the only way a heredoc allows."""
    hits = _import_targets()
    assert hits, "no file in class-space names bus_client at all — this tooth has gone blind"

    stale, imported, checked_paths = [], [], []
    this_file = Path(__file__).resolve()
    for path, text in hits:
        rel = path.relative_to(_REPO_ROOT).as_posix()
        if path.resolve() == this_file:
            # THE INSTRUMENT NAMES THE STRING IT HUNTS FOR — it has to, or it has nothing to
            # compare against. Stated out loud rather than dressed up: the alternative is
            # assembling the address at runtime from fragments so the literal never appears,
            # which would hide the one thing a reader of this tooth most needs to see.
            continue
        if path.suffix == ".py":
            if _names_the_old_address(text):
                stale.append(rel)
        elif OLD_DOTTED in text or OLD_PATH in text:
            stale.append(rel)
        if path.suffix == ".py":
            # Anything under proofs/ RUNS on import (they are scripts with a __main__ tail
            # and module-level teeth); importing them here would run the corpus inside one
            # tooth. Their import lines are checked by parsing instead, which is why the
            # stale check above is the load-bearing half for them.
            if "proofs" in path.parts or "probes" in path.parts:
                try:
                    ast.parse(text)
                except SyntaxError as e:
                    raise AssertionError("%s does not parse: %s" % (rel, e))
                checked_paths.append(rel)
                continue
            rel_mod = path.relative_to(_REPO_ROOT).with_suffix("")
            dotted = ".".join(rel_mod.parts)
            if dotted.endswith(".__init__"):
                dotted = dotted[: -len(".__init__")]
            importlib.import_module(dotted)
            imported.append(dotted)
        else:
            for line in text.splitlines():
                if NEW_DOTTED in line:
                    for token in line.replace(",", " ").replace("(", " ").split():
                        if token.startswith(NEW_DOTTED):
                            importlib.import_module(token.rstrip(".;"))
                            imported.append(token.rstrip(".;"))
                            break
            checked_paths.append(rel)

    assert not stale, \
        "these still name the old address, which no longer exists: %s" % ", ".join(sorted(stale))
    assert NEW_DOTTED in sys.modules, "the new address was never actually imported"
    assert len(imported) >= 10, \
        "only %d module(s) imported — the walk found %d file(s) naming bus_client, so it is " \
        "not reaching the importers" % (len(imported), len(hits))
    print("  PASS  test_v_every_importer_in_class_space_imports_at_the_new_address "
          "(%d file(s) named it · %d module(s) imported for real · %d parsed)"
          % (len(hits), len(imported), len(checked_paths)))


def check():
    """Every tooth runs, whatever the one before it did — and that is the hollow reading's
    requirement, not tidiness.

    A tooth that raises used to take the whole run with it, so the teeth AFTER it printed
    nothing and the reading could not tell "no tooth checks this file" from "the run stopped
    before the tooth that does". The declared tooth for ticket dd8ad9702b49 is test_v, the LAST
    one — under a sequential runner every reversion that upset an earlier tooth would have
    hidden test_v's verdict behind it.
    """
    failures = []
    for tooth in (test_i_a_shim_planted_on_disk_is_found_and_a_deleted_one_is_lost,
                  test_ii_all_three_faces_go_to_disk_for_the_named_device,
                  test_iii_a_device_nested_under_a_machine_resolves_where_discovery_says,
                  test_iv_reach_refuses_a_name_no_shim_answers_to,
                  test_v_every_importer_in_class_space_imports_at_the_new_address):
        try:
            tooth()
        except BaseException as exc:               # noqa: BLE001 — a red is a reading, not a crash
            failures.append(tooth.__name__)
            print("  RED  %s: %s: %s" % (tooth.__name__, type(exc).__name__, exc))
    if failures:
        print("RED: %d failing" % len(failures))
        return 1
    print("green — the three faces resolve a shim from the file on disk, a device that is "
          "not there refuses loudly, the nested device still resolves, and every importer "
          "in class-space was RUN at the new address")
    return 0


if __name__ == "__main__":
    raise SystemExit(check())
