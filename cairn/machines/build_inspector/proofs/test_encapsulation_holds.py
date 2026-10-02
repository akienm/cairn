"""Proof of the encapsulation_holds sieve (ticket 56d1aff4455e, RULE 1): every component talks to
every other only through that component's declared public interface.

RULE 1 (Akien, agreed 2026-10-01): "Every component talks to every other component only through
that component's public interface." A device's interface is the bus plus any client tool it
publishes; a machine's or tool's is what its charter declares in ``public_interface``. So one
predicate replaces two: a site in component S landing on module M in component T (S != T) holds
iff M is in T's public_interface AND, when T sits inside device D and S does not, T is a tool
nested in D whose charter says ``published_by_device: true``.

What the old sieves forgave, this one does not: proofs and probes are inside their component and
are NOT skipped (an instrument reaching into another device's code is the same reach), and the
db_domain enumeration is gone (its client is a published tool now, or the reach is red).

Named teeth, one per RED clause of the ticket's falsifier, so a hollow revert of inspector.py
reads red tooth by tooth rather than dying at import (the _Late pattern below).

    python3 cairn/machines/build_inspector/proofs/test_encapsulation_holds.py   # exit 0 = green
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))


class _Late:
    """The build's names are resolved AT CALL TIME, never bound at import. `cairn test
    --hollow` reverts the subject file by file and re-runs this proof; a proof that dies at
    import prints no teeth and the reading is UNRAN, not red (hollow.py: "THE FIX BELONGS TO
    THE PROOF: it must survive its subject being taken away"). Resolving late turns a missing
    subject into a red tooth, which is the evidence the crossing needs."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)

_inspector = _Late("cairn.machines.build_inspector.inspector")

# Coverage declaration read by cairn.tools.proof_coverage. 76639374d9f9's clause (a) leaned on
# the retired machine_imports_no_device sieve; its tooth moves here under the same name, so the
# coverage the PROVED ticket rests on moves with the rule rather than vanishing.
PROVES = {
    "56d1aff4455e": {"1": "a_tool_reaching_into_a_device_is_into_device",
                     "2": "a_skill_importing_an_undeclared_module_reds_until_declared",
                     "3": "a_proof_reaching_into_a_device_reds",
                     "4": "a_published_device_client_is_reachable_through_its_declared_module",
                     "5": "a_component_with_no_public_interface_reds",
                     "6": "the_old_sieves_are_retired_and_encapsulation_holds_stands",
                     "7": "the_live_into_device_findings_equal_an_independent_census"},
    "76639374d9f9": {"a": "a_machine_importing_a_device_reds_by_file_and_module"},
}

PASS = 0
FAIL = 0
_TMP: list[str] = []


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _charter(public_interface=(), **extra):
    doc = {"what": "a fixture component", "why": "a fixture component"}
    if public_interface is not None:
        doc["public_interface"] = list(public_interface)
    doc.update(extra)
    return json.dumps(doc)


def _repo(files: dict[str, str]) -> str:
    root = tempfile.mkdtemp(prefix="encapsulation_fixture_holds_")
    _TMP.append(root)
    for rel, text in files.items():
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def _breaches(files):
    return _inspector.encapsulation_breaches(_repo(files))


def _cross(found):
    """The breaches that cross a boundary (missing_field rows are about a charter, not a reach)."""
    return [b for b in found if b["reason"] != "missing_field"]


_DEVICE_D = {"cairn/devices/d/intention+why.json": _charter([]),
             "cairn/devices/d/internal.py": "X = 1\n"}


def a_tool_reaching_into_a_device_is_into_device():
    got = _cross(_breaches({**_DEVICE_D,
                            "cairn/tools/t/intention+why.json": _charter([]),
                            "cairn/tools/t/t.py": "from cairn.devices.d import internal\n"}))
    assert [(b["source"], b["target"], b["reason"]) for b in got] == \
        [("cairn/tools/t", "cairn/devices/d", "into_device")], got
    assert got[0]["file"] == "cairn/tools/t/t.py" and got[0]["line"] == 1, got


def a_skill_importing_an_undeclared_module_reds_until_declared():
    files = {"cairn/tools/t/intention+why.json": _charter(["cairn.tools.t.pub"]),
             "cairn/tools/t/pub.py": "X = 1\n", "cairn/tools/t/priv.py": "Y = 1\n",
             "skills/s/intention+why.json": _charter([]),
             "skills/s/door.py": "from cairn.tools.t import priv\n"}
    got = _cross(_breaches(files))
    assert [(b["source"], b["module"], b["reason"]) for b in got] == \
        [("skills/s", "cairn.tools.t.priv", "undeclared")], got
    files["cairn/tools/t/intention+why.json"] = _charter(["cairn.tools.t.pub", "cairn.tools.t.priv"])
    assert _cross(_breaches(files)) == [], "declaring the module did not clear the breach"


def a_proof_reaching_into_a_device_reds():
    got = _cross(_breaches({**_DEVICE_D,
                            "cairn/tools/t/intention+why.json": _charter([]),
                            "cairn/tools/t/proofs/test_x.py": "import cairn.devices.d.internal\n"}))
    assert [(b["file"], b["reason"]) for b in got] == \
        [("cairn/tools/t/proofs/test_x.py", "into_device")], got


def a_published_device_client_is_reachable_through_its_declared_module():
    files = {**_DEVICE_D,
             "cairn/devices/d/tools/client/intention+why.json": _charter(
                 ["cairn.devices.d.tools.client.client"], published_by_device=True),
             "cairn/devices/d/tools/client/client.py": "X = 1\n",
             "cairn/devices/d/tools/client/other.py": "Y = 1\n",
             "cairn/tools/t/intention+why.json": _charter([]),
             "cairn/tools/t/t.py": "from cairn.devices.d.tools.client import client\n"}
    assert _cross(_breaches(files)) == [], "a declared module of a published client tool read red"
    files["cairn/tools/t/t.py"] = "from cairn.devices.d.tools.client import other\n"
    got = _cross(_breaches(files))
    assert [(b["module"], b["reason"]) for b in got] == \
        [("cairn.devices.d.tools.client.other", "undeclared")], got


def a_component_with_no_public_interface_reds():
    got = _breaches({"cairn/tools/t/intention+why.json": _charter(None),
                     "cairn/tools/t/t.py": "import json\n"})
    assert [(b["source"], b["reason"]) for b in got] == [("cairn/tools/t", "missing_field")], got
    # The live horizon (step 4): every charter in the repo declares the field.
    live = [b["source"] for b in _inspector.encapsulation_breaches(str(_REPO_ROOT))
            if b["reason"] == "missing_field"]
    assert not live, f"{len(live)} live charter(s) declare no public_interface: {sorted(set(live))}"


def the_old_sieves_are_retired_and_encapsulation_holds_stands():
    sieves = _inspector.SIEVES
    assert "device_isolation_holds" not in sieves and "machine_imports_no_device" not in sieves, \
        sorted(k for k in sieves if k in ("device_isolation_holds", "machine_imports_no_device"))
    assert sieves.get("encapsulation_holds") is _inspector.encapsulation_holds
    # A sieve the nest would refuse does not stand: every member carries the provenance of
    # the failure that taught it (the learning-device shape, test_inspector tooth 10).
    assert "Provenance:" in (_inspector.encapsulation_holds.__doc__ or ""), \
        "encapsulation_holds carries no provenance — a check nobody was taught by"
    retired = ("device_isolation_holds", "machine_imports_no_device")
    seeds = _REPO_ROOT / "cairn/machines/build_inspector/sieves"
    assert (seeds / "encapsulation_holds.json").is_file(), "encapsulation_holds has no sieve seed"
    assert not [n for n in retired if (seeds / f"{n}.json").exists()], "a retired sieve keeps its seed"
    # A baseline entry naming a retired method forgives a finding nothing can raise any more.
    known = json.loads((_REPO_ROOT / "cairn/machines/build_inspector/finding_baseline.json")
                       .read_text())["known"]
    assert not [k for k in known if k.get("method") in retired], known
    # A charter's contract (its gates and falsifier) never leans on a retired sieve.
    leaning = [str(c.relative_to(_REPO_ROOT)) for c in _REPO_ROOT.rglob("intention+why.json")
               if ".git" not in c.parts and any(n in json.dumps(
                   {k: v for k, v in json.loads(c.read_text()).items() if k in ("gates", "falsifier")})
                   for n in retired)]
    assert not leaning, f"charter contracts still name a retired sieve: {leaning}"


def a_device_importing_another_device_is_into_device():
    got = _cross(_breaches({"cairn/devices/a/intention+why.json": _charter([]),
                            "cairn/devices/a/a.py": "from cairn.devices.b import x\n",
                            "cairn/devices/b/intention+why.json": _charter([]),
                            "cairn/devices/b/x.py": "X = 1\n"}))
    assert [(b["source"], b["target"], b["reason"]) for b in got] == \
        [("cairn/devices/a", "cairn/devices/b", "into_device")], got


def a_machine_importing_a_device_reds_by_file_and_module():
    got = _cross(_breaches({"cairn/machines/m/intention+why.json": _charter([]),
                            "cairn/machines/m/m.py": "from cairn.devices.db_domain import store\n",
                            "cairn/devices/db_domain/intention+why.json": _charter([]),
                            "cairn/devices/db_domain/store.py": "X = 1\n"}))
    assert [(b["file"], b["module"], b["reason"]) for b in got] == \
        [("cairn/machines/m/m.py", "cairn.devices.db_domain.store", "into_device")], got


def the_live_into_device_findings_equal_an_independent_census():
    """Clause 7, kept as an invariant: the live into-device findings are exactly the edges an
    independent census reads straight off import_sieve's sites, site for site. Both move together
    as RULE 1's children close breaches, so equality holds at every commit, not just the first."""
    import os
    import re
    from cairn.tools.import_sieve.sieve import SKIP_DIRS, import_sites
    root = str(_REPO_ROOT)
    comps = set()
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        if "intention+why.json" in files:
            comps.add(Path(d).relative_to(root).as_posix())

    def comp_of(rel):
        parts = Path(rel).parts
        return next(("/".join(parts[:i]) for i in range(len(parts), 0, -1)
                     if "/".join(parts[:i]) in comps), None)

    def rel(p):
        return Path(p).relative_to(root).as_posix() if os.path.isabs(str(p)) else str(p)

    census = set()
    for site in import_sites(root):
        if not site.get("target"):
            continue
        f = rel(site["file"])
        src, tgt = comp_of(f), comp_of(rel(site["target"]))
        if src is None or tgt is None or src == tgt:
            continue
        dev = re.match(r"cairn/devices/[^/]+", tgt)
        if dev and not (src == dev.group(0) or src.startswith(dev.group(0) + "/")):
            # A tool the device publishes (RULE 1: bus + published client tools) is not an
            # into-device reach; whether the module is declared is the 'undeclared' question.
            if tgt != dev.group(0) and json.loads((Path(root) / tgt / "intention+why.json")
                                                  .read_text()).get("published_by_device") is True:
                continue
            census.add((f, site["line"], tgt))
    found = {(b["file"], b["line"], b["target"]) for b in _inspector.encapsulation_breaches(root)
             if b["reason"] == "into_device"}
    assert census, "the census read no into-device edge at all — an empty census proves nothing"
    assert found == census, (f"inspector {len(found)} vs census {len(census)}; "
                             f"census-only {sorted(census - found)[:5]}; "
                             f"inspector-only {sorted(found - census)[:5]}")


TEETH = [
    a_tool_reaching_into_a_device_is_into_device,
    a_skill_importing_an_undeclared_module_reds_until_declared,
    a_proof_reaching_into_a_device_reds,
    a_published_device_client_is_reachable_through_its_declared_module,
    a_component_with_no_public_interface_reds,
    the_old_sieves_are_retired_and_encapsulation_holds_stands,
    a_device_importing_another_device_is_into_device,
    a_machine_importing_a_device_reds_by_file_and_module,
    the_live_into_device_findings_equal_an_independent_census,
]

if __name__ == "__main__":
    try:
        for fn in TEETH:
            _tooth(fn.__name__, fn)
    finally:
        for d in _TMP:
            shutil.rmtree(d, ignore_errors=True)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
