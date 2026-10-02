"""Proof for ticket 07f415c15970 — an inference call's task ticket lands in the logs tree.

Akien (open-5ec505c169c1, 2026-10-02): "they are a logging artifact, so the intention is that
they wind up in the logging tree." Their consumers are learning loops (relearn off the same
calls without rerunning them) and forensics (the complete trail of every call for 30 days).
The logs tree is the address whose why is that retention (``address.log_path``, Akien
2026-08-18), and it is the one tree every proof sandbox leaves empty — which is what stops a
pile growing ~280 files a day from riding into each sandbox (measured 2026-10-02: 2048 files,
73MB at the old address, and test_isolation red at 182MB against its 150MB bound).

One tooth per numbered falsifier clause:

  1. tickets_dir() IS THE LOGS-TREE ADDRESS: it equals address.log_path('inference_domain', 0)
     / 'tickets' and does not lie under the device's state directory.
  2. A WRITTEN TICKET LANDS THERE AND READS BACK, under a temp roots table — off disk, never
     off tickets_dir's own return value.
  3. THE OLD ADDRESS HOLDS NO TICKET on the live host — no stale writer still lands there.
  4. THE TICKETS MOVED, NOT VANISHED: the live logs-tree folder holds tickets.

    python3 cairn/devices/inference_domain/proofs/test_task_tickets_land_in_the_logs_tree.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.inference_domain import domain
from cairn.tools.base import address
from cairn.tools.scratch.scratch import scratch_dir

PROVES = {"07f415c15970": {
    "1": "tickets_dir_is_the_logs_tree_address",
    "2": "a_written_ticket_lands_in_the_logs_tree_and_reads_back",
    "3": "the_old_address_holds_no_ticket",
    "4": "the_tickets_moved_not_vanished",
}}

OLD = address.instance_path("inference_domain", 0) / "tickets"
NEW = address.log_path("inference_domain", 0) / "tickets"

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def tickets_dir_is_the_logs_tree_address():
    got = domain.tickets_dir()
    assert got == NEW, f"tickets_dir() is {got}, not the logs-tree address {NEW}"
    state = address.instance_path("inference_domain", 0)
    assert state not in got.parents, f"{got} lies under the device's state directory {state}"


def a_written_ticket_lands_in_the_logs_tree_and_reads_back():
    tmp = scratch_dir("testing-07f415c15970-")
    table = {**address.ROOTS, "instance": tmp}
    marker = "testing-07f415c15970"
    path = domain._write_task_ticket({"canonical_digest": "0" * 64, "caller": marker},
                                     roots=table)
    expected = tmp / "logs" / "inference_domain" / "0" / "tickets"
    assert Path(path).parent == expected, f"the ticket landed at {path}, not under {expected}"
    on_disk = [json.loads(p.read_text(encoding="utf-8")) for p in expected.glob("*.json")]
    assert [t.get("caller") for t in on_disk] == [marker], on_disk
    assert not (tmp / "devices").exists(), "something still wrote under the temp state tree"
    back = domain.read_task_tickets(roots=table)
    assert [t.get("caller") for t in back] == [marker], back


def the_old_address_holds_no_ticket():
    stragglers = sorted(OLD.glob("*.json")) if OLD.is_dir() else []
    assert not stragglers, (f"{len(stragglers)} ticket(s) at the old address {OLD}, newest "
                            f"{stragglers[-1].name} — a writer still lands there")


def the_tickets_moved_not_vanished():
    held = list(NEW.glob("*.json")) if NEW.is_dir() else []
    assert held, f"the logs-tree tickets folder {NEW} holds no ticket — moved, or deleted?"


TEETH = [tickets_dir_is_the_logs_tree_address,
         a_written_ticket_lands_in_the_logs_tree_and_reads_back,
         the_old_address_holds_no_ticket,
         the_tickets_moved_not_vanished]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
