"""Proof for ticket ee4e874a2d61: a component reads yellow until what depends on it is resealed.

Outline 9.4.2.3.7.1 (Akien 2026-11-13): passing its own proofs at commit puts a component in
service, yellow — proven where it changed, not yet measured against what depends on it. The
hourly tier (9.4.2.3.7.2) reseals the dependents. The inspector reports the wait in inspect()'s
existing ``yellow`` list (open-8c76dcbbd304), never among its findings.

Fixture: a scratch repo with components cairn/a and cairn/b. B's proof is green and its seal
recorded ``evidence.reached = {"cairn/a": seal_digest(A)}``; then A reseals, so its digest moves.

  1. inspect() over A carries a component-waits-on-dependents entry for A naming B's proof;
  2. after B's proof reseals with A's current digest, the yellow list carries no entry for A;
  3. A whose own seal is stale reads red (component_color) and carries no yellow entry, and the
     findings are the same whether or not a dependent waits: yellow changes no finding or gate.

    bin/cairn test cairn/devices/codemother/machines/build_inspector/proofs/test_a_component_reads_yellow_until_its_dependents_reseal.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"ee4e874a2d61": {
    "1": "test_a_changed_component_waits_on_its_dependent",
    "2": "test_the_wait_ends_when_the_dependent_reseals",
    "3": "test_red_wins_and_yellow_changes_no_finding"}}

B_PROOF = "cairn/b/proofs/test_b.py"


def _seal(comp: Path, stem: str, fingerprint: str, reached: dict | None = None) -> None:
    evidence = {"source_fingerprint": fingerprint}
    if reached is not None:
        evidence["reached"] = reached
    (comp / "validations").mkdir(exist_ok=True)
    (comp / "validations" / f"{stem}.json").write_text(json.dumps([{
        "claim": stem, "caller": "fixture", "date": "2026-11-13T00:00:00", "method": "fixture",
        "verdict": "green", "evidence": evidence, "falsifier": "fixture", "horizon": "fixture"}]),
        encoding="utf-8")


def _component(root: Path, name: str) -> Path:
    c = root / "cairn" / name
    (c / "proofs").mkdir(parents=True)
    (c / "intention+why.json").write_text(json.dumps({"component": name}), encoding="utf-8")
    (c / "proofs" / f"test_{name}.py").write_text(f"# proof {name}\n", encoding="utf-8")
    return c


def _world(root: Path, *, a_stale: bool = False) -> tuple[Path, Path]:
    """A sealed green over its own tree, B sealed reaching A, then A resealed (its digest moves)."""
    from cairn.devices.codemother.machines.build_inspector.inspector import _source_fingerprint
    from cairn.tools.validation_store.validation_store import seal_digest
    a, b = _component(root, "a"), _component(root, "b")
    _seal(a, "test_a", _source_fingerprint(a))
    _seal(b, "test_b", _source_fingerprint(b), reached={"cairn/a": seal_digest(str(a))})
    (a / "proofs" / "test_a2.py").write_text("# a second proof: A changed\n", encoding="utf-8")
    _seal(a, "test_a", _source_fingerprint(a))
    _seal(a, "test_a2", _source_fingerprint(a))
    assert seal_digest(str(a)) != json.loads((b / "validations" / "test_b.json").read_text(
        encoding="utf-8"))[-1]["evidence"]["reached"]["cairn/a"], "A's digest did not move"
    if a_stale:
        (a / "code.py").write_text("x = 1\n", encoding="utf-8")
    return a, b


def _waits(report: dict, component: str) -> list[dict]:
    return [y for y in report.get("yellow", [])
            if y.get("kind") == "component-waits-on-dependents" and y.get("component") == component]


def test_a_changed_component_waits_on_its_dependent():
    from cairn.devices.codemother.machines.build_inspector.inspector import inspect
    root = Path(scratch_dir("testing-ee4e-waits-"))
    _world(root)
    report = inspect(root=root / "cairn", component="a")
    assert not [f for f in report["findings"] if f["method"] == "component_color"], report["findings"]
    waits = _waits(report, "a")
    assert len(waits) == 1 and waits[0]["waiting_on"] == [B_PROOF], report.get("yellow")


def test_the_wait_ends_when_the_dependent_reseals():
    from cairn.devices.codemother.machines.build_inspector.inspector import inspect, _source_fingerprint
    from cairn.tools.validation_store.validation_store import seal_digest
    root = Path(scratch_dir("testing-ee4e-resealed-"))
    a, b = _world(root)
    assert _waits(inspect(root=root / "cairn", component="a"), "a"), "the fixture never waited"
    _seal(b, "test_b", _source_fingerprint(b), reached={"cairn/a": seal_digest(str(a))})
    report = inspect(root=root / "cairn", component="a")
    assert _waits(report, "a") == [], report.get("yellow")


def test_red_wins_and_yellow_changes_no_finding():
    from cairn.devices.codemother.machines.build_inspector.inspector import inspect, _source_fingerprint
    from cairn.tools.validation_store.validation_store import seal_digest
    root = Path(scratch_dir("testing-ee4e-red-"))
    a, b = _world(root, a_stale=True)
    red = inspect(root=root / "cairn", component="a")
    assert [f for f in red["findings"] if f["method"] == "component_color"], \
        "the stale seal did not read red: the tooth would pass for the wrong reason"
    assert _waits(red, "a") == [], f"a red component read yellow: {red.get('yellow')}"
    # The same world with the dependent resealed: the findings must not move.
    root2 = Path(scratch_dir("testing-ee4e-same-"))
    a2, b2 = _world(root2)
    waiting = inspect(root=root2 / "cairn", component="a")
    _seal(b2, "test_b", _source_fingerprint(b2), reached={"cairn/a": seal_digest(str(a2))})
    resealed = inspect(root=root2 / "cairn", component="a")
    assert _waits(waiting, "a") and not _waits(resealed, "a"), "the fixture did not toggle yellow"
    strip = lambda r: sorted(json.dumps({k: v for k, v in f.items() if k != "at"}, sort_keys=True,
                                        default=str).replace(str(root2), "<root>") for f in r["findings"])
    assert strip(waiting) == strip(resealed), "a yellow changed the findings a gate renders from"
    assert waiting["clean"] == resealed["clean"], (waiting["clean"], resealed["clean"])


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
