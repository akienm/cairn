"""Proofs for orient — the scans measure, refuse, and carry their provenance.

Hermetic: synthetic trees in a tempdir pin exact behavior; the real tree is asserted
by INVARIANT only (shape, membership, floors — never a snapshot value that legitimately
moves; memory: proof-over-live-data-assert-invariants).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.orient.orient import (  # noqa: E402
    SCANS, ScanRefused, call_sites, deepen, device_census, import_map, repo_truth,
)


def _refuses(fn, because):
    try:
        fn()
    except ScanRefused:
        return
    except Exception as e:  # noqa: BLE001 — the diagnostic IS the point
        raise AssertionError(
            f"THE SCAN DID NOT REFUSE — {because}. Instead the bad case got far enough in "
            f"to break something else: {type(e).__name__}: {e}."
        ) from None
    raise AssertionError(f"NO REFUSAL AT ALL — {because}. A silent guess is the hollow direction.")


def _synthetic_tree(tmp: Path) -> Path:
    """A fake repo: one component whose file CALLS emit once but MENTIONS it plenty."""
    comp = tmp / "cairn" / "fakedev"
    (comp / "proofs").mkdir(parents=True)
    (comp / "validations").mkdir()
    (comp / "intention+why.json").write_text('{"component": "fakedev"}')
    (comp / "dev.py").write_text(
        '"""Docstring MENTIONING emit and emit() and logging and emit again."""\n'
        "from base import BaseDevice\n\n\n"
        "class FakeDev(BaseDevice):\n"
        "    def work(self):\n"
        "        # a comment saying emit emit emit\n"
        "        self.emit('gate')  # the ONE real call site\n"
        "        name = 'emit'  # a string, not a call\n"
        "        return name\n"
    )
    (comp / "proofs" / "test_dev.py").write_text("self_emit = lambda: None\nself_emit()\n")
    (comp / "validations" / "test_dev.json").write_text('[{"verdict": "green"}]')
    # THE HOMONYM (measured on the real tree 2026-07-27): a module-level function that
    # happens to be NAMED emit — a genuine call site of the word, but NOT the device's
    # DiagnosticBase surface (no ``self`` receiver). sudo_relay's audit emit and
    # harbor_master's transitions.emit both wore this shape and passed silent_device on it.
    (comp / "audit.py").write_text(
        "def emit(record):\n    return record\n\n\n"
        "def run(record):\n    emit(record)\n"
    )
    return tmp / "cairn"


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="orient-proof-"))
    root = _synthetic_tree(tmp)

    # 1 — THE HEADLINE: capability, not mention. Five mentions, two call sites — the
    #     device's self.emit AND the homonym audit call. The GENERIC scan honestly reports
    #     both (a call site of the word IS a call site); which one is the device surface is
    #     the CENSUS's sharper question (tooth 4).
    r = call_sites("emit", root=root)
    outside = {(s["file"].rsplit("/", 1)[-1], s["line"])
               for s in r["measured"]["sites"] if not s["in_proofs"]}
    assert outside == {("dev.py", 8), ("audit.py", 6)}, (
        f"capability-not-mention breached: expected the two real call sites, got {outside} — "
        f"if this counts mentions, orient re-commits the 2026-07-27 'logging: 0 of 13' error "
        f"it exists to end"
    )

    # 2 — a string literal and a comment are not call sites.
    assert r["measured"]["call_sites_outside_proofs"] == 2

    # 3 — an unparseable file is a loud refusal, not a silently smaller world.
    (root / "fakedev" / "broken.py").write_text("def broken(:\n")
    _refuses(lambda: call_sites("emit", root=root),
             "a file that does not parse must red the scan, not shrink the scanned world")
    (root / "fakedev" / "broken.py").unlink()

    # 4 — census measures the world: subclass found, charter found, verdict READ.
    c = device_census(root=root)
    row = c["measured"]["components"][0]
    assert row["component"] == "fakedev" and row["charter_on_disk"] is True
    assert row["device_subclasses"] == ["dev.py:FakeDev"], row
    assert row["proofs"] == 1
    assert row["validations"] == [{"file": "test_dev.json", "verdict": "green", "records": 1}]
    # RECEIVER CHECKED: the homonym (audit.py's module-level emit, called once) does NOT
    # count toward the device's emission — only self.emit does. Two call sites of the word
    # in this tree (tooth 1); exactly one is the DiagnosticBase surface.
    assert row["self_emit_call_sites_outside_proofs"] == 1

    # 5 — a component whose charter is MISSING reads as missing (loud in the row).
    (root / "fakedev" / "intention+why.json").unlink()
    assert device_census(root=root)["measured"]["components"][0]["charter_on_disk"] is False

    # 6 — an unreadable validation is carried as UNREADABLE, never dropped (Law 7).
    (root / "fakedev" / "validations" / "test_dev.json").write_text("{not json")
    v = device_census(root=root)["measured"]["components"][0]["validations"][0]
    assert str(v["verdict"]).startswith("UNREADABLE"), v

    # 7 — census refuses an empty/wrong root rather than reporting an empty world.
    _refuses(lambda: device_census(root=tmp / "nowhere"),
             "a census of a nonexistent root must refuse, not report zero components")

    # 8 — REAL TREE, invariants only: floor honored, every row complete-shaped.
    real = device_census()
    assert real["measured"]["count"] >= 5, "the census barely saw the tree"
    for row in real["measured"]["components"]:
        assert set(row) == {"component", "charter_on_disk", "device_subclasses", "proofs",
                            "validations", "self_emit_call_sites_outside_proofs"}, row

    # 9 — real tree: the scan floor is enforced (a 3-file 'scan of cairn/' refuses).
    r = call_sites("emit")
    assert r["measured"]["modules_scanned"] >= 20

    # 10 — repo_truth reads plumbing: 40-hex HEAD, integer dirt, shape complete.
    g = repo_truth(repos=[_REPO_ROOT])
    row = g["measured"]["repos"][0]
    assert len(row["head"]) == 40 and all(ch in "0123456789abcdef" for ch in row["head"])
    assert isinstance(row["dirty_paths"], int)

    # 11 — repo_truth refuses a non-repo rather than narrating one.
    _refuses(lambda: repo_truth(repos=[tmp]),
             "a directory that is not a git repo must refuse, not report a clean fiction")

    # 12 — THE LEARNING-DEVICE SHAPE: every scan result carries scan/question/measured/
    #      provenance, and every provenance names a dated correction. A scan with no
    #      provenance is a check nobody was taught by.
    args = {"call_sites": lambda: call_sites("emit", root=root),
            "device_census": lambda: device_census(root=root),
            "repo_truth": lambda: repo_truth(repos=[_REPO_ROOT]),
            "import_map": lambda: import_map(Path(__file__))}
    assert set(args) == set(SCANS), "a scan joined the registry without joining this tooth"
    for name in SCANS:
        res = args[name]()
        assert set(res) == {"scan", "question", "measured", "provenance"}, (name, set(res))
        assert "2026-07-2" in res["provenance"], f"{name}: provenance names no dated correction"

    # 13 — deepen without an injected seam REFUSES — it never fabricates a deepening.
    _refuses(lambda: deepen("what is the bus for?", resolve=None),
             "failover with no seam must refuse; answering from nothing is the failure "
             "orient exists to end")

    # 14 — deepen's answer lands under `read`, never `measured`: inference is labeled
    #      inference by construction, and the sole-path seam is what got called.
    calls = []
    fake = lambda req: calls.append(req) or {"answer": "prose", "hit": False}  # noqa: E731
    d = deepen("what is the bus for?", resolve=fake)
    assert "measured" not in d and d["read"] == {"answer": "prose", "hit": False}
    assert calls == [{"kind": "generate", "prompt": "what is the bus for?"}]

    # 15 — orient itself never opens the host: no outbound-capable import in orient.py
    #      (deepen reaches inference only through the injected seam).
    import ast as _ast
    outbound = {"urllib", "http", "requests", "httpx", "aiohttp", "socket"}
    tree = _ast.parse((_REPO_ROOT / "cairn" / "orient" / "orient.py").read_text())
    imported = {
        n.name.split(".")[0]
        for node in _ast.walk(tree) if isinstance(node, _ast.Import) for n in node.names
    } | {
        node.module.split(".")[0]
        for node in _ast.walk(tree)
        if isinstance(node, _ast.ImportFrom) and node.module
    }
    assert not (imported & outbound), (
        f"orient.py imports {imported & outbound} — the failover must go through the "
        "injected inference_domain seam, never a direct line to the host"
    )

    # 16 — IMPORT_MAP measures the CAPABILITY, not the spelling: the loose package
    #      form, the precise form, and the from-module-import-name form of the same
    #      module all measure identically (the 2026-07-28 twice-fired red, ended);
    #      an unresolvable name honestly records its prefix; refusals stay loud.
    fixture_root = tmp / "imp"
    (fixture_root / "a").mkdir(parents=True)
    (fixture_root / "a" / "b.py").write_text("name = 1\n")
    spellings = {
        "loose.py": "from a import b\n",
        "precise.py": "import a.b\n",
        "from_name.py": "from a.b import name\n",
    }
    measured = {}
    for fname, src in spellings.items():
        (fixture_root / fname).write_text(src)
        measured[fname] = import_map(fixture_root / fname,
                                     root=fixture_root)["measured"]["imports"]
    assert measured["loose.py"] == measured["precise.py"] == measured["from_name.py"] \
        == ["a.b"], (
        f"three spellings of one module must measure as one capability: {measured}")
    (fixture_root / "stdlibish.py").write_text("from os import path\n")
    assert import_map(fixture_root / "stdlibish.py",
                      root=fixture_root)["measured"]["imports"] == ["os"], \
        "an unresolvable name records its stated prefix — measured, not guessed"
    _refuses(lambda: import_map(fixture_root / "ghost.py", root=fixture_root),
             "a scan of a missing file must refuse, not report an empty import list")
    (fixture_root / "broken.py").write_text("def (\n")
    _refuses(lambda: import_map(fixture_root / "broken.py", root=fixture_root),
             "an unparseable file has an unknowable import list — refusing beats "
             "narrating a smaller one")

    print("orient proofs: all teeth green")


if __name__ == "__main__":
    main()
