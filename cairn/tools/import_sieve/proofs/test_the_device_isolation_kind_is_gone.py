"""Proof for ticket 27f5ad6f62dc — import_sieve no longer carries the unused device_isolation rule kind.

Measured 2026-11-13 on akienyoga9i at main: nothing declared a {"kind": "device_isolation"} rule
(git grep over the rule sets, every charter and build_inspector found it only in sieve.py and its
own three proof tests). The RULE 1 check is build_inspector's encapsulation_holds (ticket
124c0312c2d8), and the kind's split on os.sep read a '/'-keyed graph as no devices at all on
Windows, so it was green there without looking. Unused code goes; history keeps it.

  1. a rule of kind device_isolation is refused as an unknown kind, and the refusal names no such kind;
  2. the kinds still in use still catch: a sole_path rule over a planted dialer reds it.

    bin/cairn test cairn/tools/import_sieve/proofs/test_the_device_isolation_kind_is_gone.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cairn.tools.import_sieve import sieve  # noqa: E402

PROVES = {"27f5ad6f62dc": {
    "1": "test_a_device_isolation_rule_is_an_unknown_kind",
    "2": "test_a_sole_path_rule_still_catches_a_planted_dialer"}}

KIND = "device" + "_isolation"


def test_a_device_isolation_rule_is_an_unknown_kind():
    graph = {"web_server/listener.py": {"cairn.devices.librarian.shim"}, "librarian/shim.py": set()}
    rule = {"kind": KIND, "capability": "cross-device import", "module_prefix": "cairn.devices."}
    try:
        got = sieve.catches(graph, rule, floor=1)
    except ValueError as e:
        assert KIND not in str(e).split("—", 1)[-1], f"the refusal still lists the kind: {e}"
        return
    raise AssertionError(f"a {KIND} rule was still judged: {got}")


def test_a_sole_path_rule_still_catches_a_planted_dialer():
    graph = {"rogue/dialer.py": {"urllib.request"}, "fine/x.py": {"json"}}
    rule = {"kind": "sole_path", "capability": "the inference host",
            "modules": ("urllib.request",), "only": "inferenceproxy/"}
    caught = sieve.catches(graph, rule, floor=1)
    assert len(caught) == 1 and caught[0].startswith("rogue/dialer.py"), caught


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
