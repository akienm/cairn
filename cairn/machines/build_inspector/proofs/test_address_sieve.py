"""Proofs for the address sieve — the instance address has one owner, and the gate says so.

Ticket ``one-owner-for-the-instance-address``. The sieve under test
(``address_is_resolved_never_spelled``) is the inspection-time seat of the rule that lives
at ``cairn/tools/base/address_rule.py``; the pulse-time seat is
``cairn/tools/base/probes/hand_spelled_instance_paths.py``. This file proves the SEAT, not
the rule — the rule's own teeth are at ``cairn/tools/base/proofs/test_address_rule.py``,
and duplicating them here would be a second spelling of a proof about second spellings.

DEFECT-FIRST, because the sieve was born green. The corpus was converted in the same
voyage, so on the day this seat shipped it drew nothing from the real tree — which is
exactly the shape of a sieve made of solid sheet metal. Every tooth below plants the
defect first and demands the catch, and the quiet cases are asserted against a tree that
was proved to bite.

Hermetic: a synthetic component tree under scratch. The live corpus is asserted by
INVARIANT only — that the sieve RAN against every component, and that anything it caught
names a file that exists — never by today's count, which this voyage drove to zero and
which the next hand-spelled path is supposed to change.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector.inspector import SIEVES, inspect  # noqa: E402
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

_SIEVE = "address_is_resolved_never_spelled"

# Assembled from pieces so that THIS FILE does not itself contain the spellings it plants.
# It sits under proofs/, so the rule would exempt it either way — but the exemption is a
# safety net, and leaning on it here would hide the day somebody moves this tooth.
_SPELL_A = 'Path.home() / ' + '".cairn"' + ' / "devices" / "thing" / "0"'
_SPELL_B = 'Path(' + '"~/.cairn/devices/thing/0"' + ').expanduser()'
_LEGIT = 'Path.home() / "dev" / "src" / "aider"'


def _component(root: Path, rel: str) -> Path:
    """The smallest thing the census will call a component: a dir with a charter and a .py."""
    d = root / rel
    (d / "proofs").mkdir(parents=True)
    (d / "intention+why.json").write_text('{"component": "%s"}' % Path(rel).name)
    (d / "proofs" / "test_x.py").write_text("assert True\n")
    (d / "code.py").write_text("def helper():\n    return 1\n")
    return d


def _sieved(root: Path, component: str) -> list[dict]:
    return [f for f in inspect(root=root, component=component)["findings"]
            if f["method"] == _SIEVE]


def main() -> None:
    tmp = scratch_dir("address-sieve-proof-")
    root = tmp / "cairn"

    clean = _component(root, "tools/clean")
    spelled = _component(root, "tools/spelled")
    mentions = _component(root, "tools/mentions")
    legit = _component(root, "tools/legit")
    proofy = _component(root, "tools/proofy")
    holder = _component(root, "devices/holder")
    nested = _component(root, "devices/holder/machines/nested")

    # 1 — THE CATCH. A component that builds the instance address by hand reds, and the
    #     finding names the site and the shape. Without this tooth every other assertion
    #     here is compatible with a sieve that never fires.
    (spelled / "berth.py").write_text(f"from pathlib import Path\n\nWHERE = {_SPELL_A}\n")
    f = _sieved(root, "spelled")
    assert len(f) == 1, f"the planted spelling must be caught exactly once: {f}"
    assert "berth.py:3" in f[0]["about"], f[0]
    assert f[0]["values"]["shape"], f[0]

    # 2 — the OTHER shape, so the seat is not proved on one dialect. Both are the corpus's.
    (spelled / "berth.py").write_text(f"from pathlib import Path\n\nWHERE = {_SPELL_B}\n")
    f = _sieved(root, "spelled")
    assert len(f) == 1 and "berth.py:3" in f[0]["about"], f

    # 3 — A MENTION IS NOT A CATCH, and this is the whole reason the rule stopped being a
    #     text scan. The regex the probe used to own caught prose — including a sentence in
    #     its OWN docstring — and the fix was to exclude that file by name, which does not
    #     generalise to the next file that talks about the address.
    (mentions / "talk.py").write_text(
        f'"""A module that discusses {_SPELL_A} without building it."""\n\n'
        f"NOTE = 'somebody might write {_SPELL_B} here, and that would be a defect'\n")
    assert _sieved(root, "mentions") == [], \
        "a mention in prose is not a spelling — that distinction is the rule's whole shape"

    # 4 — a home-rooted path that is NOT instance space is left alone. venv.py's AIDER_SRC
    #     is the live case, and a sieve that redded it would be asking the corpus to route
    #     ~/dev through an instance-space resolver.
    (legit / "src.py").write_text(f"from pathlib import Path\n\nAIDER = {_LEGIT}\n")
    assert _sieved(root, "legit") == [], "Path.home() is not the defect; .cairn is"

    # 5 — THE EXEMPTION RIDES THROUGH THE SEAT. A proof asserting the rule has to construct
    #     what the rule forbids; counting it would make every proving component permanently
    #     dirty by its own teeth.
    (proofy / "proofs" / "test_thing.py").write_text(
        f"from pathlib import Path\n\nFIXTURE = {_SPELL_A}\n")
    assert _sieved(root, "proofy") == [], "a proofs/ file is the rule's second exemption"

    # 6 — ATTRIBUTION IS BY DEEPEST OWNER. A device holds its machines in its own tree, so a
    #     containment-based scan would red the holder for its machine's line AND red the
    #     same site twice under two names. The finding belongs to the component that owns
    #     the file, and only to it.
    (nested / "berth.py").write_text(f"from pathlib import Path\n\nWHERE = {_SPELL_A}\n")
    fh, fn = _sieved(root, "holder"), _sieved(root, "nested")
    assert fh == [], f"the holder must not wear its machine's finding: {fh}"
    assert len(fn) == 1 and "berth.py:3" in fn[0]["about"], fn

    # 7 — a clean component stays clean while the tree above is dirty. Another component's
    #     hand-spelled path must never red an innocent row.
    assert _sieved(root, "clean") == [], "a neighbour's defect is not this component's"
    assert inspect(root=root, component="clean")["clean"], \
        "the clean fixture must draw nothing from ANY sieve — else tooth 7 proves nothing"

    # 8 — THE SEAT IS IN THE NEST. A sieve that exists and is not registered judges nothing,
    #     which is the armed-by-hand failure in its build-gate costume.
    assert _SIEVE in SIEVES, "the sieve must be registered or it never runs"
    r = inspect(root=root, component="clean")
    assert _SIEVE in r["sieves_run"], r["sieves_run"]

    # 9 — THE LIVE CORPUS, BY INVARIANT AND NEVER BY COUNT. Today it is zero; the point of
    #     the seat is that it stops being zero the moment somebody spells one. So what is
    #     asserted is that the sieve RAN against every real component, and that anything it
    #     caught names a file that exists on disk.
    live = inspect()
    for comp, scores in live["gradation"].items():
        assert _SIEVE in scores, \
            f"the sieve did not run against {comp} — absent means not-shaken, and a " \
            "component silently exempt from a gate is the vacuous green"
    for f in live["findings"]:
        if f["method"] != _SIEVE:
            continue
        site = Path(f["values"]["site"].rsplit(":", 1)[0])
        assert (site if site.is_absolute() else _REPO_ROOT / site).exists(), \
            f"the sieve named a file the world does not hold: {f}"

    print("address sieve proofs: all teeth green")


if __name__ == "__main__":
    main()
