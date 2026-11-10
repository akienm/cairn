"""Proof of the encapsulation_holds sieve: RULE 1, enforced as a device-path check.

RULE 1 (Akien, agreed 2026-10-01): "Every component talks to every other component only through
that component's public interface." Its physics, as outline 17.13.1 settles it (Akien, Q#77,
2026-11-09): "The RULE 1 check is a path check: code inside device bar may not import
cairn.devices.foo (anything not under cairn.devices.bar), except a tool foo publishes
(cairn.devices.foo.tools.<x>, its charter saying published_by_device). Inside one device there is
one owner, so nothing is checked there. A charter's public_interface describes what the component
offers ...; the check does not read it." Code outside every device (tools/, machines/, skills/,
bin/) reaching a module under a device that is not a published tool is red too (ticket
124c0312c2d8's reading; RULE 1's verbatim "NO DEVICE MAY IMPORT ANOTHERS DEVICE").

What changed, by ticket: 56d1aff4455e built one sieve over every component boundary that read
each charter's ``public_interface``; 124c0312c2d8 narrows it to the device path. 56d1aff4455e's
clauses (2) (an undeclared module reds) and (5) (a charter without public_interface reds) are
overturned by the outline answer, so their PROVES keys sit on the tooth that measures the claim
that replaced them: ``an_undeclared_module_and_a_missing_public_interface_hold``.

Named teeth, one per clause, so a hollow revert of inspector.py reads red tooth by tooth rather
than dying at import (the _Late pattern below).

    python3 cairn/machines/build_inspector/proofs/test_encapsulation_holds.py   # exit 0 = green
"""
import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402  the fixture door; swept at exit


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

# Coverage declaration read by cairn.tools.proof_coverage.
PROVES = {
    "124c0312c2d8": {"1": "every_source_reaching_another_device_reads_one_row",
                     "2": "a_reach_inside_one_device_reads_no_row",
                     "3": "a_published_tool_is_reachable_by_any_module_under_it",
                     "4": "an_undeclared_module_and_a_missing_public_interface_hold",
                     "5": "the_live_rows_equal_an_independent_path_census",
                     "6": "the_build_inspector_reaches_no_device_and_the_old_sieves_stay_retired"},
    "56d1aff4455e": {"1": "every_source_reaching_another_device_reads_one_row",
                     "2": "an_undeclared_module_and_a_missing_public_interface_hold",
                     "3": "every_source_reaching_another_device_reads_one_row",
                     "4": "a_published_tool_is_reachable_by_any_module_under_it",
                     "5": "an_undeclared_module_and_a_missing_public_interface_hold",
                     "6": "the_build_inspector_reaches_no_device_and_the_old_sieves_stay_retired",
                     "7": "the_live_rows_equal_an_independent_path_census"},
    "76639374d9f9": {"a": "every_source_reaching_another_device_reads_one_row"},
    "135a905eac3c": {"all": "the_build_inspector_reaches_no_device_and_the_old_sieves_stay_retired"},
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
    root = str(scratch_dir("encapsulation_fixture_holds_"))
    _TMP.append(root)
    for rel, text in files.items():
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def _rows(files):
    return _inspector.encapsulation_breaches(_repo(files))


_DEVICE_D = {"cairn/devices/d/intention+why.json": _charter([]),
             "cairn/devices/d/internal.py": "X = 1\n"}


def every_source_reaching_another_device_reads_one_row():
    sources = {"cairn/tools/t/t.py": "cairn/tools/t",
               "cairn/machines/m/m.py": "cairn/machines/m",
               "skills/s/door.py": "skills/s",
               "cairn/tools/p/proofs/test_x.py": "cairn/tools/p",
               "cairn/devices/a/a.py": "cairn/devices/a"}
    for i, (src, comp) in enumerate(sources.items(), 1):
        files = {**_DEVICE_D, comp + "/intention+why.json": _charter([]),
                 src: "import json\n" * (i - 1) + "from cairn.devices.d import internal\n"}
        got = _rows(files)
        assert [(b["file"], b["line"], b["module"], b["source"], b["target"], b["reason"])
                for b in got] == \
            [(src, i, "cairn.devices.d.internal", comp, "cairn/devices/d", "into_device")], (src, got)


def a_reach_inside_one_device_reads_no_row():
    files = {"cairn/devices/d/intention+why.json": _charter([]),
             "cairn/devices/d/machines/m1/intention+why.json": _charter([]),
             "cairn/devices/d/machines/m1/m1.py": "from cairn.devices.d.machines.m2 import private\n",
             "cairn/devices/d/machines/m2/intention+why.json": _charter(["cairn.devices.d.machines.m2.pub"]),
             "cairn/devices/d/machines/m2/pub.py": "X = 1\n",
             "cairn/devices/d/machines/m2/private.py": "Y = 1\n",
             "cairn/devices/d/proofs/test_d.py": "import cairn.devices.d.machines.m2.private\n"}
    got = _rows(files)
    assert got == [], got


def a_published_tool_is_reachable_by_any_module_under_it():
    files = {**_DEVICE_D,
             "cairn/devices/d/tools/client/intention+why.json": _charter(
                 ["cairn.devices.d.tools.client.client"], published_by_device=True),
             "cairn/devices/d/tools/client/client.py": "X = 1\n",
             "cairn/devices/d/tools/client/other.py": "Y = 1\n",
             "cairn/tools/t/intention+why.json": _charter([]),
             "cairn/tools/t/t.py": "from cairn.devices.d.tools.client import client\n"
                                  "from cairn.devices.d.tools.client import other\n"}
    got = _rows(files)
    assert got == [], f"a published tool's module read red: {got}"
    files["cairn/devices/d/tools/client/intention+why.json"] = _charter(
        ["cairn.devices.d.tools.client.client"])
    got = _rows(files)
    assert [(b["line"], b["target"], b["reason"]) for b in got] == \
        [(1, "cairn/devices/d/tools/client", "into_device"),
         (2, "cairn/devices/d/tools/client", "into_device")], got


def an_undeclared_module_and_a_missing_public_interface_hold():
    files = {"cairn/tools/t/intention+why.json": _charter(["cairn.tools.t.pub"]),
             "cairn/tools/t/pub.py": "X = 1\n", "cairn/tools/t/priv.py": "Y = 1\n",
             "cairn/tools/u/intention+why.json": _charter(None),
             "cairn/tools/u/u.py": "import json\n",
             "skills/s/intention+why.json": _charter([]),
             "skills/s/door.py": "from cairn.tools.t import priv\nfrom cairn.tools.u import u\n"}
    got = _rows(files)
    assert got == [], f"the check read a public_interface: {got}"
    src = (_REPO_ROOT / "cairn/machines/build_inspector/inspector.py").read_text()
    for word in ("'undeclared'", '"undeclared"', "'missing_field'", '"missing_field"'):
        assert word not in src, f"inspector.py still carries the retired reason {word}"


def the_live_rows_equal_an_independent_path_census():
    """Read straight off import_sieve's sites by path alone, with no component walk: a site counts
    iff its target sits under cairn/devices/<y>/ (a file, not the package's own __init__), its
    file does not, and its target is not under a tools/<t>/ of y whose charter says
    published_by_device. Both move together as RULE 1's children close reaches."""
    import os
    from cairn.tools.import_sieve.sieve import import_sites
    root = str(_REPO_ROOT)

    def rel(p):
        p = str(p)
        return Path(p).relative_to(root).as_posix() if os.path.isabs(p) else p.replace(os.sep, "/")

    census = set()
    for site in import_sites(root):
        if not site.get("target"):
            continue
        f, t = rel(site["file"]), rel(site["target"])
        parts = t.split("/")
        if len(parts) < 4 or parts[:2] != ["cairn", "devices"]:
            continue
        dev = "/".join(parts[:3]) + "/"
        if f.startswith(dev):
            continue
        if len(parts) > 5 and parts[3] == "tools":
            charter = Path(root, *parts[:5], "intention+why.json")
            if charter.is_file() and json.loads(charter.read_text()).get("published_by_device") is True:
                continue
        mod = t[:-len(".py")].replace("/", ".")
        census.add((f, site["line"], mod[:-len(".__init__")] if mod.endswith(".__init__") else mod))
    found = {(rel(b["file"]), b["line"], b["module"]) for b in _inspector.encapsulation_breaches(root)}
    assert census, "the census read no cross-device edge at all — an empty census proves nothing"
    assert found == census, (f"inspector {len(found)} vs census {len(census)}; "
                             f"census-only {sorted(census - found)[:5]}; "
                             f"inspector-only {sorted(found - census)[:5]}")


def the_build_inspector_reaches_no_device_and_the_old_sieves_stay_retired():
    """Ticket 135a905eac3c: the inspector's verdict gate once imported codemother's verdict
    machine. Over the LIVE tree, RULE 1's predicate finds nothing on build_inspector's row and no
    import line in inspector.py names cairn.devices. And the two sieves 56d1aff4455e retired stay
    retired: not in SIEVES, no seed, no baseline entry, no charter contract leaning on them."""
    row = {"dir": "machines/build_inspector", "component": "build_inspector"}
    found = _inspector.encapsulation_holds(row, _REPO_ROOT / "cairn/machines/build_inspector")
    assert found == [], found
    src = (_REPO_ROOT / "cairn/machines/build_inspector/inspector.py").read_text()
    reach = [ln.strip() for ln in src.splitlines()
             if ln.lstrip().startswith(("from cairn.devices", "import cairn.devices"))]
    assert reach == [], reach
    sieves = _inspector.SIEVES
    retired = ("device_isolation_holds", "machine_imports_no_device")
    assert not [n for n in retired if n in sieves], sorted(k for k in sieves if k in retired)
    assert sieves.get("encapsulation_holds") is _inspector.encapsulation_holds
    doc = _inspector.encapsulation_holds.__doc__ or ""
    assert "Provenance:" in doc and "17.13.1" in doc, \
        "encapsulation_holds carries no provenance naming outline 17.13.1"
    seeds = _REPO_ROOT / "cairn/machines/build_inspector/sieves"
    assert (seeds / "encapsulation_holds.json").is_file(), "encapsulation_holds has no sieve seed"
    assert not [n for n in retired if (seeds / f"{n}.json").exists()], "a retired sieve keeps its seed"
    known = json.loads((_REPO_ROOT / "cairn/machines/build_inspector/finding_baseline.json")
                       .read_text())["known"]
    assert not [k for k in known if k.get("method") in retired], known
    leaning = [str(c.relative_to(_REPO_ROOT)) for c in _REPO_ROOT.rglob("intention+why.json")
               if ".git" not in c.parts and any(n in json.dumps(
                   {k: v for k, v in json.loads(c.read_text()).items() if k in ("gates", "falsifier")})
                   for n in retired)]
    assert not leaning, f"charter contracts still name a retired sieve: {leaning}"


TEETH = [
    every_source_reaching_another_device_reads_one_row,
    a_reach_inside_one_device_reads_no_row,
    a_published_tool_is_reachable_by_any_module_under_it,
    an_undeclared_module_and_a_missing_public_interface_hold,
    the_live_rows_equal_an_independent_path_census,
    the_build_inspector_reaches_no_device_and_the_old_sieves_stay_retired,
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
