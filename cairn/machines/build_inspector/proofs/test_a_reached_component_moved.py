"""Proof: a seal that reached another component turns yellow when that component's seals move.

Ticket 50e0581737e8 (parent of f43b5705ea03, which gave ``seal_digest``, and 734b22d09f2e,
which gave ``evidence.reached``). Yellow is not red: the proof's own code has not moved, a
component it ran through has re-sealed since, so the green it carries was earned against
something that is no longer there. ``component_color`` stays silent on it — one mouth per
defect, and this is not that defect.

Fixture components in a scratch root, the sieve called directly with that root:

  1. A's green seal records reached={cairn/b: seal_digest(B)} — zero findings while B is unchanged.
  2. B's current validation record changes — exactly one finding, naming B, color yellow.
  3. component_color over A in case (2) reads no finding: yellow is not red.
  4. A seal without ``reached`` reads no finding.
  5. No gate composes it: inspect() carries the yellow under ``yellow`` and none of it among
     the ``findings`` its proof record (and so the PROVEME build gate) is rendered from.

    python3 cairn/machines/build_inspector/proofs/test_a_reached_component_moved.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "50e0581737e8": {
        "1": "test_an_unmoved_reach_reads_no_finding",
        "2": "test_a_moved_reach_reads_one_yellow_finding",
        "3": "test_yellow_is_not_red",
        "4": "test_a_seal_without_reached_reads_no_finding",
        "5": "test_no_gate_composes_the_yellow",
    },
}


def _row(name):
    return {"component": name, "dir": name, "charter_on_disk": True, "proofs": 1,
            "validations": [], "device_subclasses": [],
            "self_emit_call_sites_outside_proofs": 0}


def _seal_b(b: Path, fingerprint: str) -> None:
    vals = b / "validations"
    vals.mkdir(parents=True, exist_ok=True)
    (vals / "test_b.json").write_text(json.dumps([{
        "claim": "b", "caller": "fixture", "date": "2026-11-02T00:00:00", "method": "fixture",
        "verdict": "green", "evidence": {"source_fingerprint": fingerprint},
        "falsifier": "fixture", "horizon": "fixture"}]), encoding="utf-8")


def _fixture(root: Path, *, reached: bool = True) -> Path:
    """Components cairn/a and cairn/b under ``root``; A sealed green over its own tree."""
    from cairn.machines.build_inspector.inspector import _source_fingerprint
    from cairn.tools.validation_store.validation_store import seal_digest
    b = root / "cairn" / "b"
    (b / "proofs").mkdir(parents=True)
    (b / "proofs" / "test_b.py").write_text("# proof b\n", encoding="utf-8")
    _seal_b(b, "b-fingerprint-first")
    a = root / "cairn" / "a"
    (a / "proofs").mkdir(parents=True)
    (a / "intention+why.json").write_text(json.dumps({"component": "a"}), encoding="utf-8")
    (a / "proofs" / "test_thing.py").write_text("# proof a\n", encoding="utf-8")
    evidence = {"source_fingerprint": _source_fingerprint(a)}
    if reached:
        evidence["reached"] = {"cairn/b": seal_digest(str(b))}
    (a / "validations").mkdir()
    (a / "validations" / "test_thing.json").write_text(json.dumps([{
        "claim": "a", "caller": "fixture", "date": "2026-11-02T00:00:00", "method": "fixture",
        "verdict": "green", "evidence": evidence,
        "falsifier": "fixture", "horizon": "fixture"}]), encoding="utf-8")
    return a


def _sieve(a: Path, root: Path) -> list:
    from cairn.machines.build_inspector.inspector import a_reached_component_moved
    return a_reached_component_moved(_row("a"), a, repo_root=root)


def test_an_unmoved_reach_reads_no_finding():
    with scratch_dir("reached_component_unmoved_") as root:
        a = _fixture(root)
        assert _sieve(a, root) == [], _sieve(a, root)


def test_a_moved_reach_reads_one_yellow_finding():
    with scratch_dir("reached_component_moved_") as root:
        a = _fixture(root)
        _seal_b(root / "cairn" / "b", "b-fingerprint-second")
        findings = _sieve(a, root)
        assert len(findings) == 1, findings
        f = findings[0]
        assert f["method"] == "a_reached_component_moved", f
        assert f["values"]["reached"] == "cairn/b", f
        assert f["values"]["color"] == "yellow", f


def test_yellow_is_not_red():
    from cairn.machines.build_inspector.inspector import component_color
    with scratch_dir("reached_component_not_red_") as root:
        a = _fixture(root)
        _seal_b(root / "cairn" / "b", "b-fingerprint-second")
        assert len(_sieve(a, root)) == 1
        assert component_color(_row("a"), a) == [], component_color(_row("a"), a)


def test_a_seal_without_reached_reads_no_finding():
    with scratch_dir("reached_component_absent_") as root:
        a = _fixture(root, reached=False)
        _seal_b(root / "cairn" / "b", "b-fingerprint-second")
        assert _sieve(a, root) == [], _sieve(a, root)


def test_no_gate_composes_the_yellow():
    from cairn.machines.build_inspector.inspector import inspect
    with scratch_dir("reached_component_no_gate_") as root:
        _fixture(root)
        _seal_b(root / "cairn" / "b", "b-fingerprint-second")
        report = inspect(root=root / "cairn", component="a")
        assert [f["values"]["reached"] for f in report.get("yellow", [])] == ["cairn/b"], \
            report.get("yellow")
        assert not [f for f in report["findings"]
                    if f["method"] == "a_reached_component_moved"], report["findings"]


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
