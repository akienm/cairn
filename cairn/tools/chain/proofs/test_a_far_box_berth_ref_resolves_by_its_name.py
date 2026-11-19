"""Proof for ticket 4e84a96955a1 — a chart berth ref recorded on another box resolves by its own name.

Measured 2026-11-19 on akiendelllinux: a4892e762b70 was charted on akiendell, so its verdict
artifact's ``validate_ref`` (and the validate packet's ``hypothesize_ref``) are
``C:\\Users\\akien\\.cairn\\devices\\chart\\0\\packets\\<name>``. verdict_contract._read_chain
opened them with a bare open(); the verdict gate answered FileNotFoundError and the close kicked
the ticket to FIXME, although ``<commons>/berths/chart/<name>`` held both copies (chain.carry_berth,
ticket e8fb6bcd23c5). 1e99a571dd6d fixed the same miss inside sail.validate_path only.

1. clause_1_resolve_berth_finds_the_copy_by_its_name: chain.resolve_berth returns a local file as
   itself; a Windows-recorded ref and an absent posix ref resolve to the commons copy of the same
   file name; a ref whose name is in neither place resolves to None;
2. clause_2_the_verdict_contract_reads_a_far_box_chain: verdict_contract.unanswered over a verdict
   whose validate_ref is Windows-recorded, its validate packet's hypothesize_ref Windows-recorded
   too, both copies in the commons mirror, every criterion passed and every hypothesis disposed,
   returns [] — not "the claiming chain cannot be read".

The commons is repointed by ``artifact.set_diagnostic_roots`` and restored in ``finally``. Every
subject is bound at tooth time.

Run bare:  PYTHONPATH=. python3 cairn/tools/chain/proofs/test_a_far_box_berth_ref_resolves_by_its_name.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "4e84a96955a1": {
        "1": "clause_1_resolve_berth_finds_the_copy_by_its_name",
        "2": "clause_2_the_verdict_contract_reads_a_far_box_chain",
    },
}

FAILURES: list[str] = []
WIN = "C:\\Users\\akien\\.cairn\\devices\\chart\\0\\packets\\"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:800]}")
    if not ok:
        FAILURES.append(name)


def clause_1(tmp: Path, mirror: Path) -> None:
    name = "clause_1_resolve_berth_finds_the_copy_by_its_name"
    try:
        from cairn.tools.chain import chain
        local = tmp / "validate-20261119T000000-local.json"
        local.write_text("{}", newline="\n")
        copy = mirror / "validate-20261113T005908-win.json"
        copy.write_text("{}", newline="\n")
        got = {
            "local": chain.resolve_berth(str(local)),
            "windows": chain.resolve_berth(WIN + copy.name),
            "posix": chain.resolve_berth("/home/elsewhere/.cairn/devices/chart/0/packets/" + copy.name),
            "neither": chain.resolve_berth(WIN + "validate-20261113T005908-gone.json"),
        }
        want = {"local": str(local), "windows": str(copy), "posix": str(copy), "neither": None}
        check(name, got == want, f"got {got}, want {want}")
    except Exception as exc:  # noqa: BLE001 — a crash is a red tooth, named
        check(name, False, f"{type(exc).__name__}: {exc}")


def clause_2(mirror: Path) -> None:
    name = "clause_2_the_verdict_contract_reads_a_far_box_chain"
    try:
        from cairn.tools.chain import verdict_contract as vc
        hyp = mirror / "hypothesize-20261113T005800-win.json"
        hyp.write_text(json.dumps({"hypotheses": [{"piece": "p1", "expect": "e1"}]}), newline="\n")
        val = mirror / "validate-20261113T005908-chain.json"
        val.write_text(json.dumps({"criteria": [{"claim": "C1", "instrument": "bin/cairn test x.py"}],
                                   "hypothesize_ref": WIN + hyp.name}), newline="\n")
        artifact = {"validate_ref": WIN + val.name,
                    "verdicts": [{"claim": "C1", "outcome": "pass", "instrument": "bin/cairn test x.py",
                                  "evidence": "green"}],
                    "dispositions": [{"piece": "p1", "expect": "e1", "disposition": "confirmed"}]}
        got = vc.unanswered(artifact)
        check(name, got == [], f"unanswered -> {got}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-4e84a96955a1-far-box-ref-")
    commons = tmp / "CairnCommons"
    mirror = commons / "berths" / "chart"
    mirror.mkdir(parents=True)
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
    try:
        clause_1(tmp, mirror)
        clause_2(mirror)
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
