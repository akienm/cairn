"""origin — the one definition of the testing mark (ticket be4a7b3c7caa, child 1 of 71d1bbfa98b0).

Test against live, marked as testing (Akien, ruled 2026-09-28, extended 2026-10-04): the live
system is the test surface, and everything a test puts on it carries a mark so it can be thrown
away. The mark has two faces and this module is the only place either is spelled:

  - the PROCESS mark: the tester sets ``CAIRN_TESTER_ORIGIN=<run id>`` in a proof's environment
    (env var naming: CAIRN_<COMPONENT>_<NAME>). ``test_origin()`` reads it as
    ``{"kind": "test", "run": <id>}``, the stamp an emission born under it carries; unset or
    empty, it is ``None`` and nothing is stamped.
  - the NAME mark: a device id, folder or addressee a test puts on the live bus starts
    ``testing-``. ``is_testing_name()`` says so, so a consumer can tolerate and ignore it.

Stdlib only (``os``): it sits at the base floor beside ``address``, imported by DiagnosticBase.
"""
from __future__ import annotations

import os

ENV = "CAIRN_TESTER_ORIGIN"
TESTING_PREFIX = "testing-"


def test_origin() -> dict | None:
    """The stamp for anything born in this process: ``{"kind": "test", "run": id}``, or None."""
    run = os.environ.get(ENV, "")
    return {"kind": "test", "run": run} if run else None


def is_testing_name(name) -> bool:
    """True iff ``name`` is a string carrying the testing mark at its start."""
    return isinstance(name, str) and name.startswith(TESTING_PREFIX)
