"""Proof for the breadcrumb log — a record written by a device SURVIVES THE PROCESS.

THE TOOTH THIS FILE EXISTS FOR is the cross-process one, and the trouble that cast the ticket
wrote the reason down before the code existed: *"A device emits at a gate; the record is on disk
afterward, readable by a separate process. The proof runs the emit in one process and reads the
file in another — a same-process assertion would pass on the in-memory hold and prove nothing."*
Everything ``DiagnosticBase`` does today already passes a same-process assertion; the whole
finding (#4) is that the list dies with the process. So a green here that never crossed a
process boundary would be the hollow build Law 8 exists to refuse, and it would be hollow in
exactly the way the thing under test is supposed to fix.

WHAT ELSE IS PINNED, and why each one is a tooth rather than a comment:

  - APPEND, NOT REPLACE. The bytes on disk after the first write are still the FIRST bytes after
    the second. This is the whole difference between this file and ``liveness.json`` sitting next
    to it, and both existing JSONL writers in the house replace, so the divergence is deliberate
    and has to be held by something.
  - NO ``.tmp`` IS EVER PRODUCED. The read-modify-write shape leaves one; its absence is what
    says a record already on disk was never rewritten (Law 7).
  - THE ADDRESS COMES FROM THE ONE OWNER. An injected roots table lands the trail under a temp
    directory — proved by construction AND by grepping this module's own source for
    ``Path.home()`` and a literal ``.cairn``, because the address module was built out of ten
    hand-spelled derivations and the reflex is what has to be caught.
  - THE PROOF DOES NOT SEED THE THING IT WILL BE JUDGED BY. Running these teeth writes NOTHING
    into the live instance tree. The ticket's acceptance is a human reading the live file, and
    that read is worthless if running the proof could have written it.
  - THE STAND-IN WAS HONEST. ``Inspector.inspect`` consumes ``records()`` off the disk log with
    no change to ``inspector.py`` — which is the charter's claim about its ``Mailbox`` ("the v0
    in-memory STAND-IN ... NEVER the runtime home") tested rather than believed, and
    ``inspector.py``'s import list is checked to have not grown to make it true.
  - THE TWO FAILURE MODES STAY DIFFERENT. An unserializable payload DEGRADES and the crossing is
    still recorded; a trail that will not parse is LOUD by line number, never silently truncated.
    Losing the fact that a gate was crossed is the one loss this file exists to end.
  - LAW 6 ON THE FILE ITSELF. Two devices get two trails. There is no shared file for two owners
    to write into, which is what makes the ownership rule physics rather than a convention.

NOT PINNED, deliberately: nothing here asserts a live path, a count, or any snapshot of the
running system. The teeth run entirely against injected temp roots; the live claim is the
ticket's own falsifier and is run by hand at acceptance, which is what the ticket demands.

    python3 cairn/diagnostic_inspector/proofs/test_breadcrumb_log.py     # exit 0 = green
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.diagnostic import DiagnosticBase
from cairn.diagnostic_inspector import CompletenessRegistry, Inspector, by_gate, by_pointer
from cairn.diagnostic_inspector.log import RECORD_NAME, BreadcrumbLog, LogUnreadable

_LOG_SOURCE = _REPO_ROOT / "cairn" / "diagnostic_inspector" / "log.py"
_INSPECTOR_SOURCE = _REPO_ROOT / "cairn" / "diagnostic_inspector" / "inspector.py"

# A device name no real device answers to, so a tooth that accidentally reached the live tree
# would create something recognisable rather than colliding with a real instance's space.
_FAKE = "proof_only_device_breadcrumb_log"

_PASSES: list[str] = []


def ok(condition, why: str) -> None:
    if not condition:
        raise AssertionError(why)
    _PASSES.append(why)


class _Dev(DiagnosticBase):
    """A minimal device carrying the real emit mechanism — the breadcrumb source, unfaked."""


def _t(us: int):
    return datetime(2026, 8, 12, 12, 0, 0, us, tzinfo=timezone.utc)


def _code_attributes_and_strings(source: str) -> tuple[set, list]:
    """Everything the module's CODE reaches for, docstrings excluded. Docstring constants are
    identified by position (the first statement of a module/class/function), which is the only
    thing that actually distinguishes prose from a literal in a parsed tree."""
    tree = ast.parse(source)
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]
    return attrs, literals


def _roots(tmp: Path) -> dict:
    return {"repo": _REPO_ROOT, "commons": _REPO_ROOT.parent / "CairnCommons", "instance": tmp}


# ── THE TOOTH THE TROUBLE DEMANDED ───────────────────────────────────────────

_CHILD = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from cairn.base.diagnostic import DiagnosticBase
from cairn.diagnostic_inspector.log import BreadcrumbLog

class Dev(DiagnosticBase):
    pass

tmp = Path(sys.argv[2])
roots = {"repo": Path(sys.argv[1]), "commons": Path(sys.argv[1]), "instance": tmp}
dev = Dev()
dev.set_diagnostic_receiver(BreadcrumbLog(sys.argv[3], 0, roots=roots))
rec = dev.emit("subscribe", pointer="ticket/from-another-process", values={"pid": "child"})
assert rec["home"] == "sent", rec
print(rec["ts"])
"""


def a_record_emitted_in_one_process_is_read_back_in_another(tmp: Path) -> None:
    """THE tooth. The emit happens in a child process that then EXITS; the assertions run here,
    after it is gone. Nothing about this can pass on the in-memory hold — the list it would
    have lived in was freed with the child."""
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD, str(_REPO_ROOT), str(tmp), _FAKE],
        capture_output=True, text=True, timeout=60,
    )
    ok(proc.returncode == 0,
       f"the emitting child process exits clean (stderr: {proc.stderr.strip()!r})")
    ok(proc.stdout.strip(), "the child reports the stamp of the record it emitted")

    log = BreadcrumbLog(_FAKE, 0, roots=_roots(tmp))
    got = log.records()
    ok(len(got) == 1,
       "THE CROSS-PROCESS TOOTH: exactly one record is on disk after the writing process died")
    ok(got[0]["gate"] == "subscribe" and got[0]["pointer"] == "ticket/from-another-process",
       "the record read in THIS process is the one the OTHER process emitted, gate and pointer intact")
    ok(got[0]["home"] == "sent",
       "the record says home='sent', not 'held' — a receiver was wired and it took it")
    ok(got[0]["values"] == {"pid": "child"},
       "the payload crossed the process boundary whole")
    ok(got[0]["ts"] == proc.stdout.strip(),
       "the record on disk is byte-for-byte the stamp the child said it wrote — not a lookalike")


# ── THE WRITE ────────────────────────────────────────────────────────────────

def construction_touches_no_disk(tmp: Path) -> None:
    log = BreadcrumbLog("never_written", 0, roots=_roots(tmp))
    ok(not log.path.exists(),
       "constructing a log creates nothing — computing an address opens no file (address.py's own bound)")
    ok(not log.path.parent.exists(),
       "and it does not provision the device's space either; provisioning is a different act with a different owner (Law 6)")
    ok(log.records() == [],
       "an absent trail reads as EMPTY, not as an error — nothing has crossed a gate yet is a true state")


def the_write_appends_and_never_rewrites(tmp: Path) -> None:
    dev = _Dev()
    log = BreadcrumbLog("appender", 0, roots=_roots(tmp))
    dev.set_diagnostic_receiver(log)

    dev.emit("first", pointer="p1", now=_t(1))
    first_bytes = log.path.read_bytes()
    dev.emit("second", pointer="p2", now=_t(2))
    after = log.path.read_bytes()

    ok(after.startswith(first_bytes),
       "APPEND, NOT REPLACE: the bytes written first are still the first bytes, untouched — "
       "a record already on disk is never rewritten (Law 7)")
    ok(len(after.splitlines()) == len(first_bytes.splitlines()) + 1,
       "the second write added exactly one line")
    ok(not list(log.path.parent.glob("*.tmp")),
       "NO .tmp IS PRODUCED — the read-modify-write shape both house precedents use leaves one, "
       "and its absence is what says this file is a trail rather than a snapshot")
    ok([r["gate"] for r in log.records()] == ["first", "second"],
       "the trail reads back in the order it was written")


def two_devices_get_two_trails(tmp: Path) -> None:
    a, b = _Dev(), _Dev()
    log_a = BreadcrumbLog("owner_a", 0, roots=_roots(tmp))
    log_b = BreadcrumbLog("owner_b", 0, roots=_roots(tmp))
    a.set_diagnostic_receiver(log_a)
    b.set_diagnostic_receiver(log_b)
    a.emit("gate_a", pointer="a")
    b.emit("gate_b", pointer="b")

    ok(log_a.path != log_b.path, "two owners, two files — there is no shared trail")
    ok([r["gate"] for r in log_a.records()] == ["gate_a"],
       "LAW 6 ON THE FILE: one owner's records never land in another owner's space")
    ok([r["gate"] for r in log_b.records()] == ["gate_b"],
       "and the other direction holds too")
    ok(log_a.path.parent.name == "0" and log_a.path.parent.parent.name == "owner_a",
       "the trail sits in the owning device INSTANCE's space — instance 0 is the singleton, not an exemption")
    ok(log_a.path.name == RECORD_NAME,
       "the file's name is the module's one constant, not a string a caller spells")


# ── THE ADDRESS ──────────────────────────────────────────────────────────────

def the_address_comes_from_the_one_owner(tmp: Path) -> None:
    log = BreadcrumbLog("addressed", 3, roots=_roots(tmp))
    ok(str(log.path).startswith(str(tmp)),
       "an injected roots table lands the trail under it — which is what lets a proof run without "
       "writing into the live tree it will later be judged against")
    ok(log.path == tmp / "devices" / "addressed" / "3" / RECORD_NAME,
       "and the shape is the settled one: devices/<device>/<instance>/, the instance never omitted")

    source = _LOG_SOURCE.read_text()
    # Measured over the PARSED module, not the raw text. A first pass grepped the file and went
    # red on the docstring's own sentence saying there is no Path.home() below — prose naming
    # the drift it avoids is not the drift. What the tooth means is "no CODE spells the address",
    # so it reads code: attribute accesses and non-docstring string literals.
    attrs, literals = _code_attributes_and_strings(source)
    ok("home" not in attrs,
       "no code in the module reaches Path.home() — that reflex is what put ten copies of this "
       "address in class-space and is what the address module was built out of")
    ok(not [s for s in literals if ".cairn" in s],
       "and no code-level string spells the instance root either")
    ok("from cairn.base.address import instance_path" in source,
       "it composes the one owner of where things live, rather than re-deriving it")


def running_this_proof_writes_nothing_into_the_live_tree(tmp: Path) -> None:
    """Not a snapshot assertion: the invariant is that these teeth cannot reach the live
    instance root at all, checked against a device name no real device answers to."""
    live = BreadcrumbLog(_FAKE, 0)          # no roots -> the REAL table
    ok(not live.path.exists(),
       "the live instance tree gained nothing from running these teeth — the acceptance read-back "
       "measures the running system, and a proof that could seed it would make that read meaningless")
    ok(str(live.path) != str(BreadcrumbLog(_FAKE, 0, roots=_roots(tmp)).path),
       "and the injected table really is a different address, so the check above is not vacuous")


# ── THE DROP-IN ──────────────────────────────────────────────────────────────

def the_disk_log_drops_into_the_inspector_unchanged(tmp: Path) -> None:
    dev = _Dev()
    log = BreadcrumbLog("inspected", 0, roots=_roots(tmp))
    dev.set_diagnostic_receiver(log)
    dev.emit("verify", pointer="ticket/A", values={"expected": "2", "actual": "123"}, now=_t(300))
    dev.emit("enter", pointer="ticket/A", values={"arg": "x"}, now=_t(100))
    dev.emit("noise", pointer="ticket/B", values={"other": "thing"}, now=_t(200))

    findings = Inspector(CompletenessRegistry()).inspect(log.records(), by_pointer("ticket/A"))
    ok(findings["gates"] == ["enter", "verify"],
       "THE STAND-IN WAS HONEST: Inspector.inspect consumes records() off DISK with no adaptation, "
       "ordered by the 6th-decimal stamp exactly as it does for the in-memory Mailbox")
    ok([r["gate"] for r in findings["steps"]] == findings["gates"],
       "and the ordered slice agrees with its own gate list — the trail read off disk is one "
       "reading, not two that could disagree")
    ok(all(r["pointer"] == "ticket/A" for r in findings["steps"]),
       "and the other pointer never bleeds in — Law 6 survives the change of home")

    narrowed = Inspector(CompletenessRegistry()).inspect(
        log.records(), by_pointer("ticket/A"), by_gate("verify"))
    ok(narrowed["gates"] == ["verify"],
       "filters still conjoin over the disk trail")

    imports = [l for l in _INSPECTOR_SOURCE.read_text().splitlines()
               if l.startswith("import ") or l.startswith("from ")]
    ok(imports == ["from __future__ import annotations", "import copy", "import json",
                   "from pathlib import Path"],
       "inspector.py's imports did NOT grow to make that true — the charter's fork-independence "
       "edge wants that surface argued, not grown, so the new code lives in its own module")


# ── THE TWO FAILURE MODES ────────────────────────────────────────────────────

def an_unserializable_payload_degrades_but_the_crossing_is_still_recorded(tmp: Path) -> None:
    dev = _Dev()
    log = BreadcrumbLog("degrader", 0, roots=_roots(tmp))
    dev.set_diagnostic_receiver(log)
    dev.emit("crossing", pointer="p", values={"obj": object()}, now=_t(5))

    got = log.records()
    ok(len(got) == 1,
       "the crossing IS recorded — losing the fact that a gate was crossed is the exact loss this "
       "file exists to end, so an unwritable payload never costs the record")
    ok(got[0]["gate"] == "crossing" and got[0]["pointer"] == "p",
       "gate and pointer survive intact; it is the payload that degrades, not the breadcrumb")
    ok("values_unwritable" in got[0] and "object" in got[0]["values_unwritable"],
       "and the degradation is NAMED with what failed — loud, not a quietly empty values dict (Law 7)")
    ok(got[0]["values"] == {},
       "the unwritable payload is not half-written; it is replaced, with the failure beside it")


def a_trail_that_will_not_parse_is_loud_by_line_number(tmp: Path) -> None:
    dev = _Dev()
    log = BreadcrumbLog("corrupted", 0, roots=_roots(tmp))
    dev.set_diagnostic_receiver(log)
    dev.emit("good", pointer="p", now=_t(1))
    with open(log.path, "a", encoding="utf-8") as fh:
        fh.write("{this is not json\n")

    try:
        log.records()
    except LogUnreadable as exc:
        ok("line 2" in str(exc),
           "an unreadable trail names the LINE — a diagnostic surface that drops the line it could "
           "not parse is reporting a world it did not read, and that line is the likely one")
        ok("this is not json" in str(exc),
           "and it carries the raw text, so the resolver needs no second look (complete first pass)")
    else:
        raise AssertionError("a corrupt line must raise LogUnreadable, never be silently skipped")

    ok(log.path.read_text().count("\n") == 2,
       "and reading did not repair or truncate the file — a reader never mutates what it counts")


def blank_lines_are_not_records(tmp: Path) -> None:
    dev = _Dev()
    log = BreadcrumbLog("blanks", 0, roots=_roots(tmp))
    dev.set_diagnostic_receiver(log)
    dev.emit("one", pointer="p", now=_t(1))
    with open(log.path, "a", encoding="utf-8") as fh:
        fh.write("\n   \n")
    ok(len(log.records()) == 1,
       "whitespace between records is not a record — a trailing newline must not read as a crossing")


# ── THE ROSTER, DERIVED ──────────────────────────────────────────────────────

def _main() -> int:
    # Derived, never hand-listed: a tooth added below and forgotten in a roster above is a tooth
    # that silently does not run, which is the failure ten proof files in this corpus still carry.
    checks = [obj for name, obj in sorted(globals().items())
              if callable(obj) and not name.startswith("_") and name != "ok"
              and getattr(obj, "__module__", None) == __name__]
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        for check in checks:
            check(tmp)
            print(f"  PASS  {check.__name__}")
    print(f"green — breadcrumb log: {len(_PASSES)} assertions over {len(checks)} teeth. A record "
          "emitted by a device in one process is read back from disk in another (the tooth the "
          "trouble demanded); the trail appends and never rewrites; its address comes from the one "
          "owner and lands in the owning device instance's own space; it drops into the Inspector "
          "with inspector.py untouched; and the two failure modes stay different — a payload "
          "degrades, a corrupt trail is loud.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
