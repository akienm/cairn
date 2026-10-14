"""inference_domain is in the device list and answers the bus (ticket e194f4b4cb3e).

The ticket was born when a chart's tree stratum read 'unavailable': nothing answered the
inference_domain address, so every embed hung. Akien's answer to open-55b04185f30f rules out a
standing daemon — the asker's reach bus pulses the shim in-process — so clause (1)'s "a live
pid" is measured as what it was FOR: the device is listed and its face answers over the bus.

Live box, marked testing (every request's ``why`` says so); clause (2) dials hex.local through
the one door with a nonce'd prompt so the cache cannot answer for the host. Invariants, never
snapshots:
  1. LISTED AND ANSWERING: ``bin/cairn list`` names inference_domain, and its yield view answers
     a bus ``get`` (unbounded: the first reach pays the in-process bring-up).
  2. A BUS infer NAMING A MODEL RETURNS hex.local's ANSWER INSIDE 10s, not from the cache.
  3. AN UNREACHABLE HOST IS REFUSED BY NAME INSIDE 10s: the resolver raises HostUnreachable
     naming the dead endpoint, so a hang is never the client's timeout.
  4. THE TREE STRATUM IS AVAILABLE: orient packets berthed after 2026-09-07 exist and none
     carries 'tree stratum unavailable'.

Run: python3 cairn/devices/inference_domain/proofs/test_inference_domain_answers_the_bus.py
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "e194f4b4cb3e": {
        "1": "test_the_device_is_listed_and_its_face_answers_the_bus",
        "2": "test_a_bus_infer_naming_a_model_returns_the_hosts_answer_inside_10s",
        "3": "test_an_unreachable_host_is_refused_by_name_inside_10s",
        "4": "test_no_orient_packet_since_the_fix_reports_the_tree_stratum_unavailable",
    },
}


def _bus():
    from cairn.tools.bus_client.bus_client import reach
    return reach("inference_domain")


def test_the_device_is_listed_and_its_face_answers_the_bus():
    listed = subprocess.run([str(_REPO_ROOT / "bin/cairn"), "list"], cwd=_REPO_ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            timeout=120).stdout.split()
    assert "inference_domain" in listed, "`cairn list` does not name inference_domain"
    t0 = time.monotonic()
    st = _bus().request(sender="proof_e194", to="inference_domain", verb="get",
                        why="e194 tooth 1 (testing)", body={"what": "yield"})
    took = time.monotonic() - t0
    assert isinstance(st, dict) and "spent" in json.dumps(st.get("body", st)), f"no yield view: {st}"
    # No time bound here: clause (1) asks that the device be up and answering, and the first
    # reach pays the in-process bring-up (12.7s measured cold, 2026-10-14). The ticket's 10s
    # bounds are clauses (2) and (3)'s, and those teeth carry them.
    print(f"   yield view answered in {took:.2f}s")
    print("ok test_the_device_is_listed_and_its_face_answers_the_bus")


def test_a_bus_infer_naming_a_model_returns_the_hosts_answer_inside_10s():
    t0 = time.monotonic()
    r = _bus().request(sender="proof_e194", to="inference_domain", verb="infer",
                       why="e194 tooth 2 (testing)",
                       body={"prompt": f"Reply with the single word: ok (e194 proof nonce {time.time_ns()})",
                             "model": "qwen2.5:7b"})
    took = time.monotonic() - t0
    b = (r or {}).get("body") or {}
    host = (b.get("provenance") or {}).get("host") or ""
    assert b.get("answer") is not None, f"no answer: {b}"
    assert "hex.local" in host, f"answered from {host!r}, not hex.local"
    assert not b.get("hit"), "a nonce'd prompt came back from the cache"
    assert took < 10, f"the infer took {took:.2f}s"
    print("ok test_a_bus_infer_naming_a_model_returns_the_hosts_answer_inside_10s")


def test_an_unreachable_host_is_refused_by_name_inside_10s():
    from cairn.devices.inference_domain import host as h
    dead = "http://127.0.0.1:9"
    t0 = time.monotonic()
    try:
        h.ollama_resolver(model="qwen2.5:7b", endpoint=dead, timeout=10.0)(
            {"kind": "generate", "prompt": "ok"})
    except h.HostUnreachable as exc:
        assert "127.0.0.1:9" in str(exc), f"the refusal does not name the host: {exc}"
    else:
        raise AssertionError("an unreachable host answered")
    took = time.monotonic() - t0
    assert took < 10, f"the refusal took {took:.2f}s"
    print("ok test_an_unreachable_host_is_refused_by_name_inside_10s")


def test_no_orient_packet_since_the_fix_reports_the_tree_stratum_unavailable():
    packets = os.path.expanduser("~/.cairn/devices/chart/0/packets")
    late = [p for p in glob.glob(f"{packets}/orient-*.json")
            if os.path.basename(p)[7:15] > "20260907"]
    assert late, "no orient packet berthed after 2026-09-07 to read"
    bad = [p for p in late if "tree stratum unavailable" in open(p).read()]
    assert not bad, f"{len(bad)} packets report the tree stratum unavailable: {bad[:3]}"
    print("ok test_no_orient_packet_since_the_fix_reports_the_tree_stratum_unavailable")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
