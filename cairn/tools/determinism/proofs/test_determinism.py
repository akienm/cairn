"""Proof for determinism — the three verdicts, the seam split, and the floor under a green.

THE FAILURE MODE THIS COMPONENT HAS. A reach report is satisfied by a hollow implementation
in two opposite directions, and each one reads as success:

  - a walk that stops short returns an empty closure, finds no oracle, and reports the whole
    corpus DETERMINISTIC. That is the loudest possible green and it means nothing.
  - a walk that over-matches reports everything as reaching an oracle, and a scan that reds
    everything gets ignored, which is the same as not existing.

So every verdict tooth here is PAIRED: the same rule is measured over a planted tree that
must produce it and over a tree that must not. Either half alone is passed by sheet metal.

The third way to be wrong is specific to this module and it already happened once, on the
first run, which is why it has a tooth rather than a comment: the fire path and the learning
seam are two paths, and collapsing them reported build_inspector — the corpus's own gate —
as consulting an oracle. Tooth (e) plants a component whose ONLY oracle reach is through
nexus.py and pins both halves: the fire verdict must stay clean AND the seam reach must
still be reported, because dropping it silently would be the opposite defect.

    python3 cairn/tools/determinism/proofs/test_determinism.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.scratch import scratch_dir
from cairn.tools.determinism import determinism as D
from cairn.tools.import_sieve import sieve


def _tree(**components) -> Path:
    """A synthetic corpus: {component_path: {filename: source}}, each with a charter.

    Padded past import_sieve's hollow floor so a clean result here is a real one — the same
    reason the sieve's own proof plants filler.
    """
    root = scratch_dir("determinism-proof-")
    for i in range(25):
        f = root / "filler" / f"mod_{i}.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("import json\n")
    (root / "filler" / "intention+why.json").write_text(json.dumps({"component": "filler"}))
    for rel, files in components.items():
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        (d / "intention+why.json").write_text(json.dumps({"component": Path(rel).name}))
        for name, src in files.items():
            (d / name).write_text(src)
    return root


def _row(report, path):
    for r in report["rows"]:
        if r["path"] == path:
            return r
    raise AssertionError(f"{path} missing from roster: {[r['path'] for r in report['rows']]}")


# ── the three verdicts, each pinned against its opposite ──────────────────────


def test_a_pure_imports_are_deterministic():
    """Nothing off-box, no shell — the verdict a gate must be able to earn."""
    root = _tree(**{"tools/pure": {"pure.py": "import json\nimport os\n"}})
    row = _row(D.measure(root), "tools/pure")
    assert row["verdict"] == D.DETERMINISTIC, row
    assert not row["oracles"] and not row["shells"], row


def test_b_a_shell_is_mostly_not_deterministic():
    """subprocess leaves the process. It replays over a committed tree, so it is MOSTLY —
    and the pairing with tooth (a) is what proves the walk distinguishes at all."""
    root = _tree(**{"tools/shells": {"shells.py": "import subprocess\n"}})
    row = _row(D.measure(root), "tools/shells")
    assert row["verdict"] == D.MOSTLY, row
    assert row["shells"], "a shell-out that reports no shell site is a finding without evidence"


def test_c_an_oracle_is_caught_transitively():
    """The oracle is TWO hops out. A one-hop check passes this while the fire path really
    does arrive at 5432 — which is the whole reason `reaches` is a walk and not a read."""
    root = _tree(**{
        "tools/front": {"front.py": "import mid.mid\n"},
        "mid": {"mid.py": "import psycopg2\n"},
    })
    row = _row(D.measure(root), "tools/front")
    assert row["verdict"] == D.ORACLE, row
    assert "psycopg2" in row["oracles"], row
    assert "->" in row["oracles"]["psycopg2"], "the chain must say HOW, not just that"


def test_d_an_oracle_off_the_path_is_not_caught():
    """The other half of (c): a component that breaches identically but is NOT reachable
    from this one must stay clean. Without this, `catch everything` passes tooth (c)."""
    root = _tree(**{
        "tools/clean": {"clean.py": "import json\n"},
        "elsewhere": {"elsewhere.py": "import psycopg2\n"},
    })
    row = _row(D.measure(root), "tools/clean")
    assert row["verdict"] == D.DETERMINISTIC, row


# ── the seam split: the defect this module shipped with, now physics ──────────


def test_e_a_learning_seam_does_not_red_the_fire_path():
    """build_inspector's real shape: a clean fire path plus a nexus that reaches the trees.

    BOTH halves are the tooth. The verdict must ignore the seam (or every question-nexus
    reds its own gate), and the seam's reach must still be REPORTED (or a genuine oracle
    hides behind a filename).
    """
    root = _tree(**{"machines/gate": {"gate.py": "import json\n",
                                      "nexus.py": "import psycopg2\n"}})
    row = _row(D.measure(root), "machines/gate")
    assert row["verdict"] == D.DETERMINISTIC, f"the seam red the fire path: {row}"
    assert "psycopg2" in row["seam_oracles"], f"the seam's reach went unreported: {row}"


# ── the roster is disk, and the floor under a clean report ────────────────────


def test_f_a_charter_with_no_code_is_not_on_the_roster():
    """Prose-as-implementation ships no fire path. Reporting it DETERMINISTIC would be a
    green earned by having nothing to measure."""
    root = _tree(**{"skills/prose": {}})
    assert not any(r["path"] == "skills/prose" for r in D.measure(root)["rows"])


def test_g_the_hollow_floor_refuses_an_unread_tree():
    """A report over zero files finds zero oracles and looks perfect (Law 8)."""
    empty = scratch_dir("determinism-empty-")
    try:
        D.measure(empty)
    except sieve.HollowScan:
        return
    raise AssertionError("a report over an unread tree came back clean instead of refusing")


def test_h_the_real_corpus_is_read_by_invariant():
    """Against the live tree — asserted as INVARIANTS, never as today's counts, so this
    tooth cannot go red merely because the corpus grew (I-proof-over-live-data)."""
    report = D.measure(_REPO_ROOT)
    assert report["rows"], "the real corpus reported no components at all"
    for r in report["rows"]:
        charter = _REPO_ROOT / r["path"] / D.CHARTER
        assert charter.is_file(), f"invented a component with no charter on disk: {r['path']}"
        assert r["verdict"] in (D.DETERMINISTIC, D.MOSTLY, D.ORACLE), r
        if r["verdict"] == D.ORACLE:
            assert r["oracles"], f"{r['path']} reds with no oracle named — incomplete finding"
    # This tool's own fire path reaches nothing off-box: an instrument that measures
    # replayability and is not itself replayable cannot be trusted about anything.
    assert _row(report, "cairn/tools/determinism")["verdict"] == D.DETERMINISTIC


def _run() -> int:
    fails = []
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — the proof reports, it does not propagate
            fails.append((name, exc))
            print(f"  RED  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{'RED' if fails else 'green'}: {len(fails)} failing")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_run())
