#!/usr/bin/env python3
"""Proof: a sole-path admission holds at any depth of the graph (ticket 3ff3ae16b2b9).

Measured 2026-11-10: ticket 3721d82be75c's PROVED was refused because the inference sole-path
rule, shaken over a graph taken at cairn/devices/ (the cairn device's parent), saw the bus TCP
proof as cairn/machines/bus/proofs/test_the_bus_speaks_tcp.py, and its admission
"bus/proofs/test_the_bus_speaks_tcp.py" (question open-06cfefbe745e) is matched only at the
graph's root. The same file, admitted, reds or not depending on which component's parent the
graph was taken over. An admission names a path relative to SOME directory; a wider graph sees
the same file under more leading segments, so the admission is matched at every segment
boundary.

  1. an admitted file under extra leading segments is not caught; a sibling and a look-alike
     directory (xbus/) still are.
  2. the inference rule shaken over the real cairn/devices/ graph catches nothing.
  3. the old shape holds: an admission given as one string still admits at the root, and a
     door outside every admission is still caught at any depth.

    python3 cairn/tools/import_sieve/proofs/test_an_admission_holds_at_any_depth.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.import_sieve import sieve

PROVES = {"3ff3ae16b2b9": {
    "1": "test_an_admitted_file_is_admitted_under_leading_segments",
    "2": "test_the_inference_rule_is_clean_over_the_devices_graph",
    "3": "test_the_old_shape_holds",
}}

DIALS = ("urllib.request", "urllib.error", "http.client", "requests", "httpx",
         "aiohttp", "socket", "ftplib", "telnetlib")
# The inference rule as the PROVED gate states it (prefixes relative to a component's parent);
# question open-10941757e6b7 (remote.py), open-06cfefbe745e (tls.py, the bus TCP proof),
# open-52b86b71a12d (web_operator, Q#74).
INFERENCE = {"kind": "sole_path", "capability": "the inference host", "modules": DIALS,
             "only": ("inference_domain/", "bus_client/remote.py", "bus_client/tls.py",
                      "bus/proofs/test_the_bus_speaks_tcp.py", "web_operator/")}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _caught_paths(graph, rule) -> list[str]:
    return sorted(c.split(" imports ", 1)[0] for c in sieve.catches(graph, rule, floor=1))


def test_an_admitted_file_is_admitted_under_leading_segments() -> None:
    import importlib.util  # the world berths under fixtures/ (ticket 3751ba501581)
    spec = importlib.util.spec_from_file_location(
        "a_file_admitted_at_depth", Path(__file__).parent / "fixtures" / "a_file_admitted_at_depth.py")
    fx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fx)
    graph, rule = fx.GRAPH, fx.RULE
    got = _caught_paths(graph, rule)
    want = ["cairn/machines/bus/other.py", "cairn/machines/xbus/proofs/test_x.py"]
    check("test_an_admitted_file_is_admitted_under_leading_segments", got == want, f"caught {got}, wanted {want}")


def test_the_inference_rule_is_clean_over_the_devices_graph() -> None:
    graph = sieve.import_graph(str(_REPO / "cairn" / "devices"))
    bus = "cairn/machines/bus/proofs/test_the_bus_speaks_tcp.py"
    lacks = []
    if bus not in graph or "socket" not in graph[bus]:
        lacks.append(f"the graph does not show {bus} importing socket — the tooth would be vacuous")
    caught = sieve.catches(graph, INFERENCE)
    if caught:
        lacks.append(f"caught {caught}")
    check("test_the_inference_rule_is_clean_over_the_devices_graph", not lacks, "; ".join(lacks))


def test_the_old_shape_holds() -> None:
    graph = {"db_domain/tools/client/store.py": {"psycopg2"},
             "cairn/devices/rogue/probe.py": {"socket"}}
    db = _caught_paths(graph, {"kind": "sole_path", "capability": "5432",
                               "modules": ("psycopg2",), "only": "db_domain/"})
    host = _caught_paths(graph, INFERENCE)
    ok = db == [] and host == ["cairn/devices/rogue/probe.py"]
    check("test_the_old_shape_holds", ok, f"db caught {db}; host caught {host}")


def main() -> int:
    for tooth in (test_an_admitted_file_is_admitted_under_leading_segments,
                  test_the_inference_rule_is_clean_over_the_devices_graph, test_the_old_shape_holds):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
