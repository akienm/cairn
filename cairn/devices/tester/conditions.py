"""The conditions a proof run was measured under — and the green that moved them (f0aad0cd0f56).

Akien's answer to open-ed0a56ce6357: a change can pass "the before test before, and the after
test after, but only because the conditions of measurment have changed ... that's probably an
item to check with operator" — "we let it complete AND notify me". So every run records what it
was measured under (measure), and a sealed green that replaces a red recorded under other
conditions completes and posts one notice naming what changed (compare). Measured 2026-10-04:
three tester proofs sealed red at a 120s timeout and green at 900s, and nothing on record said so.

The store replaces rather than appends (validation_store, 2026-08-16), so the standing record a
green reads just before its own persist IS the red it replaces; no trail is kept here. Env values
are recorded as digests, so no raw CAIRN_* value ever enters a validation.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def _tree_digest(root: Path) -> str | None:
    if not root.is_dir():
        return None
    h = hashlib.sha256()
    for p in sorted(root.rglob("*"), key=lambda q: q.relative_to(root).as_posix()):
        rel = p.relative_to(root)
        if not p.is_file() or "__pycache__" in rel.parts:
            continue
        h.update(rel.as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def measure(proof_path, *, iso_name: str, seal_verdict: str, instance_seal_verdict: str,
            timeout, env: dict) -> dict:
    proof = Path(proof_path)
    return {
        "proof": hashlib.sha256(proof.read_bytes()).hexdigest(),
        "fixtures": _tree_digest(proof.parent / "fixtures"),
        "interpreter": f"{sys.executable} {sys.version.split()[0]}",
        "isolation": f"{iso_name} seal={seal_verdict} instance-seal={instance_seal_verdict}",
        "timeout": timeout,
        "env": {k: hashlib.sha256(v.encode()).hexdigest()[:12]
                for k, v in sorted(env.items()) if k.startswith("CAIRN_")},
    }


def changed(before: dict, after: dict) -> list[str]:
    """Only keys on both sides compare, so a condition key added later never notifies by itself.

    The timeout is recorded but never compared (ticket 8383a32d20c5): a proof declares its own
    PROOF_TIMEOUT_S, so a budget is the proof's byte rather than a condition the run was
    measured under, and a green over a red that only the timeout explains posts no notice.
    """
    return sorted(k for k in before.keys() & after.keys()
                  if k != "timeout" and before[k] != after[k])


def _line(k: str, before: dict, after: dict) -> str:
    if k == "env":
        b, a = before["env"] or {}, after["env"] or {}
        moved = sorted(n for n in b.keys() | a.keys() if b.get(n) != a.get(n))
        return f"env: {', '.join(moved)} differ"
    return f"{k}: {before[k]} -> {after[k]}"


def compare(record: dict, proof_path) -> None:
    """A sealed green over a standing red: post one notice if the red ran under other conditions.

    Mutates record['evidence'] only (never a ninth field). The store is reached as a module
    attribute so a proof can stand recorders in for it.
    """
    from cairn.tools.validation_store import validation_store as vs
    from cairn.tools.proof_coverage.proof_coverage import declared
    from cairn.devices.tester import notices

    standing = vs.read_validations(str(proof_path))
    if not standing:
        return
    last = standing[-1]
    if last.get("verdict") != "red":
        return
    evidence = record["evidence"]
    before = (last.get("evidence") or {}).get("conditions")
    if not before:
        evidence["conditions_compared"] = (
            "the standing red predates the conditions instrument (ticket f0aad0cd0f56) — "
            "nothing to compare, nothing posted")
        return
    after = evidence["conditions"]
    keys = changed(before, after)
    if not keys:
        return
    diff = "\n".join(_line(k, before, after) for k in keys)
    ticket = ",".join(sorted(declared(proof_path))) or "none"
    nid = notices.post_conditions(ticket, str(proof_path), diff, keys)
    evidence["conditions_moved"] = {"notified": nid, "changed": keys}
