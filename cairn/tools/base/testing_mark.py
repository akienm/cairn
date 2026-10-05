"""testing_mark — the one definition of the testing mark (ticket be4a7b3c7caa, child of 71d1bbfa98b0).

Test against live, marked as testing (Akien, ruled 2026-09-28, reshaped 2026-10-05): the live
system is the test surface, and an artifact a test puts on it carries a mark. The mark carries a
KIND, which says what the receiver does with it:

  - ``return`` — the only kind today. The receiving device's SHIM sends the artifact back to the
    tester unacted on, and the device never sees it. The return itself is the "got here"; the
    tester matches it to ``test`` and marks that test complete (Akien: "code mother should return
    it to the tester ... "Yep, got here" is implicit in the return").
  - a future "perform this test" kind passes through to the device (Akien: "device gets the
    "perform this test" kind later"). Nothing builds it yet, so ``mark()`` refuses it; ``mark_of()``
    still reads it, so it fits without a reshape.

The mark rides under ``FIELD`` on any artifact as ``{"kind": <kind>, "test": <test id>}``.
Stdlib only: it sits at the base floor, beside ``address``.
"""
from __future__ import annotations

FIELD = "testing"      # the key the mark rides under on any artifact
RETURN = "return"      # the receiving shim sends it back to the tester, unacted on
KINDS = (RETURN,)      # the kinds this code builds; "perform this test" joins later


def mark(test: str, kind: str = RETURN) -> dict:
    """The mark for an artifact a test sends: ``{"kind": kind, "test": test}``."""
    if not isinstance(test, str) or not test:
        raise ValueError("a testing mark names the test it belongs to")
    if kind not in KINDS:
        raise ValueError(f"no testing mark of kind {kind!r} is built yet; built: {KINDS}")
    return {"kind": kind, "test": test}


def mark_of(artifact) -> dict | None:
    """The well-formed mark riding on ``artifact``, or None. Any kind is returned; the reader
    decides what a kind means (the shim acts on ``RETURN`` only)."""
    if not isinstance(artifact, dict):
        return None
    m = artifact.get(FIELD)
    if not isinstance(m, dict):
        return None
    kind, test = m.get("kind"), m.get("test")
    if isinstance(kind, str) and kind and isinstance(test, str) and test:
        return m
    return None
