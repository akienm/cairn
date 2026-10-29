#!/usr/bin/env python3
"""Proof that a certificate is a record type only the base gate class writes.

Ticket 5dc4d8a0b4d2, child 1 of e41a94da3fd0. Outline 19.14.2: 'The certificate is one file
type you can't write'; 19.14.3: signing belongs in the base gate class. Akien's answer to
open-6dbeb274245e: 'only a gate can write a certificate. how we get there is less important
to me than that you bump your nose if you try.' So there is no key: the nose-bump is the
PreToolUse block (bin/cmd/artifactgate), the door's verb and writer check, and the pre-commit
check; the certificate's own hashes say whether its bytes are intact.

Teeth, one per falsifier clause (PROVES below), over a scratch world the proof owns
(``artifact.set_diagnostic_roots``), each binding the new names at call time so the hollow
reading (no certify, no rule, no verb) reds the tooth instead of crashing the reader:
  (1) TransitionGate.certify over a green record writes a certificate verify_certificate
      accepts; over a red record it raises the gate's exception and writes nothing;
  (2) artifactgate's verdict refuses a Write, an Edit and a shell redirect onto a certificate;
  (3) the door refuses verb 'cast' on a certificate, and verb 'certify' on a ticket;
  (4) the door refuses verb 'certify' from any caller but TransitionGate.certify, and a
      second write to an existing certificate;
  (5) a certificate written around the door, or edited after certify, is a fault for both
      verify_certificate and artifact.check_staged;
  (6) verify_certificate recomputes every hash: changing one body field, the findings, or a
      hash alone is a fault.

    bin/cairn test cairn/tools/base/proofs/test_only_the_gate_writes_a_certificate.py
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"5dc4d8a0b4d2": {
    "1": "test_certify_writes_what_verify_accepts",
    "2": "test_the_pretooluse_gate_refuses_a_certificate",
    "3": "test_the_door_holds_certificates_to_the_certify_verb",
    "4": "test_only_transitiongate_certify_writes_and_only_once",
    "5": "test_a_certificate_around_the_door_fails_both_checks",
    "6": "test_every_hash_is_recomputed",
}, "e41a94da3fd0": {
    "1": "test_certify_writes_what_verify_accepts",
    "2": "test_a_certificate_around_the_door_fails_both_checks",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout


def _world(tmp: Path) -> Path:
    from cairn.tools.artifact import artifact as A
    commons = tmp / "CairnCommons"
    (commons / "tickets").mkdir(parents=True)
    (commons / "certificates").mkdir(parents=True)
    cairn = tmp / "cairn"
    cairn.mkdir()
    for r in (commons, cairn):
        _git(r, "init", "-q")
        _git(r, "config", "user.email", "proof@cairn")
        _git(r, "config", "user.name", "proof")
        _git(r, "config", "commit.gpgsign", "false")
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    # The ticket store's charter, so a refusal of verb 'certify' on a ticket (tooth 3) is the
    # verb rule's and not the keys check's (1fc53d5d96cc) refusing an unreadable charter.
    A.write_json(commons / "tickets" / "_charter+why.json", {"plan_fields": ["id"]},
                 verb="cast", why="proof: the scratch ticket store's charter")
    return commons


class _Red(Exception):
    def __init__(self, msg, findings=None):
        super().__init__(msg)
        self.findings = findings


def _gate():
    from cairn.tools.base.gate_class import TransitionGate
    return TransitionGate("proof_gate", exception_class=_Red)


def _green():
    from cairn.tools.gate import gate
    return [gate.proved(identity="lane_a", expected=True, actual=True),
            gate.proved(identity="lane_b", expected=[], actual=[])]


def _red():
    from cairn.tools.gate import gate
    return [gate.proved(identity="lane_a", expected=True, actual=False)]


def _certs(commons: Path) -> list[Path]:
    return sorted((commons / "certificates").glob("*.cert.json"))


def test_certify_writes_what_verify_accepts(commons: Path) -> None:
    from cairn.tools.base.gate_class import verify_certificate
    path = Path(_gate().certify(_green(), ticket="abcdef012345", target="PROVEME"))
    body = json.loads(path.read_text(encoding="utf-8"))
    faults = verify_certificate(path)
    under = path.parent == commons / "certificates" and path.name.endswith(".cert.json")
    shape = (body.get("gate") == "proof_gate" and body.get("ticket") == "abcdef012345"
             and body.get("target") == "PROVEME" and body.get("findings") == _green())
    before = _certs(commons)
    raised = False
    try:
        _gate().certify(_red(), ticket="abcdef012345", target="PROVEME")
    except _Red:
        raised = True
    nothing = _certs(commons) == before
    check("test_certify_writes_what_verify_accepts",
          faults == [] and under and shape and raised and nothing,
          f"faults {faults}; under certificates/ {under}; body shape {shape}; "
          f"red raised {raised}; red wrote nothing {nothing}")


def test_the_pretooluse_gate_refuses_a_certificate(commons: Path) -> None:
    spec = importlib.util.spec_from_loader(
        "artifactgate_cert_proof",
        importlib.machinery.SourceFileLoader("artifactgate_cert_proof",
                                             str(_REPO / "bin" / "cmd" / "artifactgate")))
    gate_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate_mod)
    cert = commons / "certificates" / "abcdef012345-PROVEME-hand.cert.json"
    asks = {
        "Write": gate_mod.verdict("Write", {"file_path": str(cert), "content": "{}"}),
        "Edit": gate_mod.verdict("Edit", {"file_path": str(cert), "old_string": "a", "new_string": "b"}),
        "redirect": gate_mod.verdict("Bash", {"command": f"echo '{{}}' > {cert}", "cwd": str(commons)}),
    }
    allowed = sorted(k for k, v in asks.items() if v is None)
    check("test_the_pretooluse_gate_refuses_a_certificate", not allowed, f"allowed: {allowed}")


def test_the_door_holds_certificates_to_the_certify_verb(commons: Path) -> None:
    from cairn.tools.artifact import artifact as A
    body = json.dumps({"kind": "certificate"}, indent=2) + "\n"
    cert = commons / "certificates" / "abcdef012345-PROVEME-cast.cert.json"
    cast_refused = False
    try:
        A.write(cert, body, verb="cast", why="proof: a cast onto a certificate")
    except A.Refused:
        cast_refused = True
    ticket = commons / "tickets" / "abcdef012345-proof.json"
    certify_refused = False
    try:
        A.write(ticket, json.dumps({"id": "abcdef012345"}, indent=2) + "\n",
                verb="certify", why="proof: certify onto a ticket")
    except A.Refused:
        certify_refused = True
    check("test_the_door_holds_certificates_to_the_certify_verb",
          cast_refused and not cert.exists() and certify_refused and not ticket.exists(),
          f"cast refused {cast_refused}; certify on a ticket refused {certify_refused}")


def test_only_transitiongate_certify_writes_and_only_once(commons: Path) -> None:
    from cairn.tools.artifact import artifact as A
    body = json.dumps({"kind": "certificate"}, indent=2) + "\n"
    cert = commons / "certificates" / "abcdef012345-PROVEME-forged.cert.json"
    forged_refused = False
    try:
        A.write(cert, body, verb="certify", why="proof: certify from a proof, not the gate")
    except A.Refused:
        forged_refused = True
    path = Path(_gate().certify(_green(), ticket="abcdef012345", target="PROVED"))
    first = path.read_bytes()
    again_refused = False
    try:
        A.write(path, body, verb="certify", why="proof: a second write to a certificate")
    except A.Refused:
        again_refused = True
    check("test_only_transitiongate_certify_writes_and_only_once",
          forged_refused and not cert.exists() and again_refused and path.read_bytes() == first,
          f"forged refused {forged_refused}; rewrite refused {again_refused}")


def test_a_certificate_around_the_door_fails_both_checks(commons: Path) -> None:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.base.gate_class import verify_certificate
    real = Path(_gate().certify(_green(), ticket="abcdef012345", target="BUILDME"))
    around = commons / "certificates" / "abcdef012345-BUILDME-around.cert.json"
    around.write_bytes(real.read_bytes())
    edited = Path(_gate().certify(_green(), ticket="abcdef012345", target="PROVEME"))
    doc = json.loads(edited.read_text(encoding="utf-8"))
    doc["target"] = "PROVED"
    edited.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    v_around, v_edited = verify_certificate(around), verify_certificate(edited)
    _git(commons, "add", "-A")
    staged = A.check_staged("CairnCommons")
    s_around = any(around.name in f for f in staged)
    s_edited = any(edited.name in f for f in staged)
    _git(commons, "reset", "-q")
    around.unlink()
    check("test_a_certificate_around_the_door_fails_both_checks",
          bool(v_around) and bool(v_edited) and s_around and s_edited,
          f"verify around {v_around}; verify edited {v_edited}; "
          f"check_staged names around {s_around}, edited {s_edited}")


def test_every_hash_is_recomputed(commons: Path) -> None:
    from cairn.tools.base.gate_class import verify_certificate
    path = Path(_gate().certify(_green(), ticket="abcdef012345", target="PROVED"))
    good = json.loads(path.read_text(encoding="utf-8"))

    def faults_after(mutate) -> list[str]:
        doc = json.loads(json.dumps(good))
        mutate(doc)
        scratch = path.parent.parent / "mutated.cert.json"
        scratch.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            return verify_certificate(scratch)
        finally:
            scratch.unlink()

    # A mutated copy sits outside certificates/, so locate() refuses it whatever the hashes
    # say; the hash faults are read for by name instead of by count.
    def names(faults: list[str], word: str) -> bool:
        return any(word in f for f in faults)

    cases = {
        "a body field": names(faults_after(lambda d: d.update(gate="another_gate")), "body_sha256"),
        "the findings": names(faults_after(lambda d: d["findings"].append(
            {"identity": "lane_c", "expected": 1, "actual": 1})), "findings_sha256"),
        "body_sha256 alone": names(faults_after(lambda d: d.update(body_sha256="0" * 64)), "body_sha256"),
        "findings_sha256 alone": names(faults_after(lambda d: d.update(findings_sha256="0" * 64)),
                                       "findings_sha256"),
    }
    missed = sorted(k for k, v in cases.items() if not v)
    check("test_every_hash_is_recomputed", not missed and verify_certificate(path) == [],
          f"no hash fault named after changing: {missed}")


def main() -> int:
    teeth = (test_certify_writes_what_verify_accepts,
             test_the_pretooluse_gate_refuses_a_certificate,
             test_the_door_holds_certificates_to_the_certify_verb,
             test_only_transitiongate_certify_writes_and_only_once,
             test_a_certificate_around_the_door_fails_both_checks,
             test_every_hash_is_recomputed)
    with tempfile.TemporaryDirectory(prefix="cairn-certificate-proof-") as d:
        commons = None
        try:
            commons = _world(Path(d))
        except Exception as exc:  # noqa: BLE001 — a world that cannot be built reds every tooth
            for tooth in teeth:
                check(tooth.__name__, False, f"world raised {type(exc).__name__}: {exc}")
        if commons is not None:
            try:
                for tooth in teeth:
                    try:
                        tooth(commons)
                    except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red
                        check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
            finally:
                from cairn.tools.artifact import artifact as A
                A.set_diagnostic_roots(None)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
