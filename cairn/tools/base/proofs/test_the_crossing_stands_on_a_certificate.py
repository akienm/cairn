#!/usr/bin/env python3
"""Proof that a crossing into a gate stands on the certificate that gate wrote.

Ticket 7c41e2b09d5a, child 4 of e41a94da3fd0. The parent's falsifier: 'every crossing past an
entry gate names the certificate it stands on'. Akien on open-f17382e51f4f: 'the probe just
tells it, you can now advance to x'; on open-6dbeb274245e: 'only a gate can write a
certificate ... you bump your nose if you try'; 2026-10-28: the only writer question is LLM or
deterministic code, and only for gate-pass certificates.

Teeth, one per falsifier clause (PROVES below), over a scratch world the proof owns
(``artifact.set_diagnostic_roots``), each binding the new names at call time so the hollow
reading reds the tooth instead of crashing the reader:
  (1) a ticketed forward crossing into TICKETME, journaled under the door's cairn root,
      records a ``certificate`` that verify_certificate accepts, written by gate 'ticket' for
      that ticket and target, holding exactly the record's ``proved`` list;
  (2) a back-edge, a ticketless crossing, and a crossing whose history lies outside the
      door's cairn root each record no certificate and write none;
  (3) TransitionGate.certify called directly, with gate_class._LIVE_COMMONS pointed at this
      world's commons, refuses (CertifyRefused) and writes nothing; under emit it writes;
  (4) gate_probes.fire puts the certificate in the envelope body when it is given one, and
      leaves the key out when it is not;
  (5) a ticket with no demo flag can cross into PROVED on a certificate: every row the demo
      seat adds to the proved list passes the gate's own compare (FIXME 1, after the harbor
      refused this ticket's PROVED on demo_gate_binding_check).

    bin/cairn test cairn/tools/base/proofs/test_the_crossing_stands_on_a_certificate.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# The node-class table, resolved where hollow does: beside the repo, else under $HOME
# (measured 2026-10-28 on 66ee1ffc1ec7: the repo-relative default is absent in a hollow worktree).
_NODE_CLASSES = next((c / "node_classes" for c in (_REPO.parent / "CairnCommons",
                                                   Path.home() / "dev" / "src" / "CairnCommons")
                      if (c / "node_classes" / "code-seam.json").is_file()), None)

PROVES = {"7c41e2b09d5a": {
    "1": "test_a_gated_crossing_names_a_certificate_that_verifies",
    "2": "test_no_gate_no_ticket_no_class_space_no_certificate",
    "3": "test_certify_outside_emit_bumps_its_nose",
    "4": "test_the_probe_carries_the_certificate",
    "5": "test_a_proved_crossing_without_demo_can_be_certified",
}}

FAILURES: list[str] = []

_TICKET = "abcdef012345"
_AT_THINK = "code-seam@v2: [THINKME:waiting] -> TICKETME -> BUILDME -> PROVEME -> PROVED"
_AT_TICKET = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout


def _world(tmp: Path) -> dict:
    from cairn.tools.artifact import artifact as A
    commons = tmp / "CairnCommons"
    (commons / "certificates").mkdir(parents=True)
    cairn = tmp / "cairn"
    (cairn / "cairn" / "tools" / "example").mkdir(parents=True)
    for r in (commons, cairn):
        _git(r, "init", "-q")
        _git(r, "config", "user.email", "proof@cairn")
        _git(r, "config", "user.name", "proof")
        _git(r, "config", "commit.gpgsign", "false")
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    return {"tmp": tmp, "commons": commons, "cairn": cairn}


def _certs(w: dict) -> list[Path]:
    return sorted((w["commons"] / "certificates").glob("*.cert.json"))


def _emit(w: dict, workflow: str, target: str, *, where: Path | None = None, **extra) -> dict:
    """Cross once and return the record the crossing journaled."""
    from cairn.tools.base import transitions as T
    d = where or (w["cairn"] / "cairn" / "tools" / "example")
    d.mkdir(parents=True, exist_ok=True)
    h, s = d / "history.json", d / "state.json"
    T.emit(workflow, target, history_path=str(h), state_path=str(s), actor="proof",
           why="proof crossing", node_class_root=_NODE_CLASSES or T._NODE_CLASSES, **extra)
    return json.loads(h.read_text(encoding="utf-8"))[-1]


def test_a_gated_crossing_names_a_certificate_that_verifies(w: dict) -> None:
    from cairn.tools.base.gate_class import verify_certificate
    before = _certs(w)
    rec = _emit(w, _AT_THINK, "TICKETME", ticket=_TICKET)
    new = [p for p in _certs(w) if p not in before]
    named = rec.get("certificate")
    path = (w["commons"] / named) if isinstance(named, str) else None
    body = json.loads(path.read_text(encoding="utf-8")) if path and path.is_file() else {}
    faults = verify_certificate(path) if path else ["no certificate named"]
    ok = (len(new) == 1 and path == new[0] and faults == [] and body.get("gate") == "ticket"
          and body.get("ticket") == _TICKET and body.get("target") == "TICKETME"
          and body.get("findings") == rec.get("proved"))
    check("test_a_gated_crossing_names_a_certificate_that_verifies", ok,
          f"certificate {named!r}; new files {len(new)}; faults {faults}; gate "
          f"{body.get('gate')!r}; findings equal proved {body.get('findings') == rec.get('proved')}")


def test_no_gate_no_ticket_no_class_space_no_certificate(w: dict) -> None:
    before = _certs(w)
    back = _emit(w, _AT_TICKET, "THINKME", ticket=_TICKET)
    bare = _emit(w, _AT_THINK, "TICKETME")
    outside = _emit(w, _AT_THINK, "TICKETME", ticket=_TICKET,
                    where=w["tmp"] / "elsewhere" / "example")
    named = {k: r.get("certificate") for k, r in
             (("back", back), ("ticketless", bare), ("outside", outside))}
    written = len(_certs(w)) - len(before)
    # The control: the same world certifies a gated crossing, so the three Nones are not a
    # crossing that certifies nothing at all.
    control = _emit(w, _AT_THINK, "TICKETME", ticket=_TICKET).get("certificate")
    check("test_no_gate_no_ticket_no_class_space_no_certificate",
          all(v is None for v in named.values()) and written == 0 and isinstance(control, str),
          f"certificates named {named}; files written {written}; control named {control!r}")


def test_certify_outside_emit_bumps_its_nose(w: dict) -> None:
    from cairn.tools.base import gate_class as G
    from cairn.tools.gate import gate

    class _Red(Exception):
        def __init__(self, msg, findings=None):
            super().__init__(msg)

    refused = None
    saved = getattr(G, "_LIVE_COMMONS", None)
    G._LIVE_COMMONS = w["commons"]
    try:
        before = _certs(w)
        try:
            G.TransitionGate("ticket", exception_class=_Red).certify(
                [gate.proved(identity="lane", expected=True, actual=True)],
                ticket=_TICKET, target="TICKETME")
        except Exception as exc:  # noqa: BLE001 — which exception is the tooth's question
            refused = type(exc).__name__
        by_hand = len(_certs(w)) - len(before)
        rec = _emit(w, _AT_THINK, "TICKETME", ticket=_TICKET)
        under_emit = isinstance(rec.get("certificate"), str)
    finally:
        G._LIVE_COMMONS = saved
    check("test_certify_outside_emit_bumps_its_nose",
          refused == "CertifyRefused" and by_hand == 0 and under_emit,
          f"direct certify raised {refused}; wrote {by_hand}; under emit named {under_emit}")


def test_the_probe_carries_the_certificate(w: dict) -> None:
    from cairn.tools.base import gate_probes

    class _Bus:
        def __init__(self):
            self.posts = []

        def post(self, **kw):
            self.posts.append(kw)
            return {"id": len(self.posts)}

    roots = {"repo": w["tmp"] / "repo", "commons": w["commons"], "instance": w["tmp"] / "inst"}
    folder = gate_probes.probes_dir("ticket", roots)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "cc.json").write_text(json.dumps(
        {"to": "cc", "event": "certified", "message": "{event} on {ticket}"}))
    crossing = dict(ticket=_TICKET, component="cairn/tools/example", from_="THINKME",
                    to="TICKETME", direction="forward", fingerprint="f" * 64)
    with_cert, without = _Bus(), _Bus()
    cert = "certificates/%s-TICKETME-x.cert.json" % _TICKET
    try:
        gate_probes.fire(**crossing, certificate=cert, roots=roots, bus=with_cert)
    except TypeError as exc:
        check("test_the_probe_carries_the_certificate", False, f"fire refused the key: {exc}")
        return
    gate_probes.fire(**crossing, roots=roots, bus=without)

    def body(bus):
        b = bus.posts[0].get("body") if bus.posts else None
        return b if isinstance(b, dict) else {}
    check("test_the_probe_carries_the_certificate",
          body(with_cert).get("certificate") == cert and "certificate" not in body(without),
          f"with: {body(with_cert).get('certificate')!r}; without has key "
          f"{'certificate' in body(without)}")


def test_a_proved_crossing_without_demo_can_be_certified(w: dict) -> None:
    from cairn.tools.base import ticket_file as TF
    from cairn.tools.base import transitions as T
    from cairn.tools.base.gate_class import TransitionGate
    from cairn.tools.gate import gate
    folder = w["commons"] / "tickets"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_TICKET}-demo-less.json").write_text(json.dumps({"id": _TICKET}))
    saved = TF._TICKETS
    TF._TICKETS = folder
    try:
        _note, rows = T._require_demo(_TICKET, {})
    finally:
        TF._TICKETS = saved
    failing = [r.get("identity") for r in rows if not gate.passed(r)]
    refused = None
    try:
        TransitionGate("demo", exception_class=T.CertificateRed).run(rows)
    except Exception as exc:  # noqa: BLE001 — which exception is the tooth's question
        refused = type(exc).__name__
    check("test_a_proved_crossing_without_demo_can_be_certified",
          bool(rows) and not failing and refused is None,
          f"rows {[r.get('identity') for r in rows]}; failing {failing}; gate raised {refused}")


def main() -> int:
    teeth = (test_a_gated_crossing_names_a_certificate_that_verifies,
             test_no_gate_no_ticket_no_class_space_no_certificate,
             test_certify_outside_emit_bumps_its_nose,
             test_the_probe_carries_the_certificate,
             test_a_proved_crossing_without_demo_can_be_certified)
    with tempfile.TemporaryDirectory(prefix="cairn-crossing-certificate-proof-") as d:
        w = None
        try:
            w = _world(Path(d))
        except Exception as exc:  # noqa: BLE001 — a world that cannot be built reds every tooth
            for tooth in teeth:
                check(tooth.__name__, False, f"world raised {type(exc).__name__}: {exc}")
        if w is not None:
            try:
                for tooth in teeth:
                    try:
                        tooth(w)
                    except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red
                        check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
            finally:
                from cairn.tools.artifact import artifact as A
                A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
