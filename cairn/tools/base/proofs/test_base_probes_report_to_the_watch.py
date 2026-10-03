"""PROOF — every standing base probe reports to harbor_master's watch verb (ticket 8ecb99998254).

835b5736bf2b's decision D2 names the receiver for every standing WATCHME probe: harbor_master's
``watch`` verb (a88d6a368cfb), which reads ``{ticket, holds, finding}`` and sends a red ticket to
FIXME. This proof measures the cairn/tools/base child: the helper that states the three fields
once (``watch_carry``), every standing base probe posting through it, every such spec naming the
receiver, and the one probe no receiver could use (b0c0c47835c1) standing at FIXME instead.

What a hollow build cannot pass (Law 8):
  - No ``watch_carry`` in probe.py fails watch_carry_states_holds_and_finding at import.
  - A probe left verbless, or carrying its ticket's PATH as ``ticket``, fails
    every_standing_base_probe_posts_watch, which reads each live payload's verb, ``to``,
    ``ticket``, ``holds`` and ``finding``.
  - A helper that inverts the predicate, swallows a raise as green, or drops the address fails
    the fixture cases of watch_carry_states_holds_and_finding.

The population is read from the commons, never listed here: every ticket at a rest (PROVED or
WATCHME) whose watchme probe berths under cairn/tools/base/probes. Live payloads are asserted
as INVARIANTS only — a holds value is the world's to change.

    python3 cairn/tools/base/proofs/test_base_probes_report_to_the_watch.py   # exit 0 = green
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.transitions import parse_workflow  # noqa: E402
from cairn.tools.base.watchme_spec import watchme_spec_error  # noqa: E402

PROVES = {
    "8ecb99998254": {
        "all": "test_base_probes_report_to_the_watch",
    },
}

BERTH = "cairn/tools/base/probes/"
RECEIVER = {"what": "harbor_master watch verb", "in": "cairn/devices/cairn/machines/harbor_master"}
UNRECEIVABLE = "b0c0c47835c1"


def _main_tree() -> Path:
    """The hollow runs this proof in a /tmp worktree with no CairnCommons beside it; the commons
    is read beside the main tree (the test_watch_receives_a_finding.py precedent)."""
    common = subprocess.run(["git", "-C", str(_REPO_ROOT), "rev-parse", "--path-format=absolute",
                             "--git-common-dir"], capture_output=True, text=True)
    return Path(common.stdout.strip()).parent if common.returncode == 0 else _REPO_ROOT


def _tickets() -> Path:
    return _main_tree().parent / "CairnCommons" / "tickets"


def _specs(doc: dict) -> list[dict]:
    w = doc.get("watchme")
    specs = w if isinstance(w, list) else [w]
    return [s for s in specs if isinstance(s, dict)]


def _standing() -> list[tuple[str, dict, dict]]:
    """(id, ticket, spec) for every ticket at a rest whose watchme probe berths in base."""
    out = []
    for path in sorted(_tickets().glob("*.json")):
        try:
            doc = json.loads(path.read_text("utf-8"))
            here = parse_workflow(doc["workflow_and_state"]).here
        except Exception:  # noqa: BLE001 — not a standing ticket this proof can read
            continue
        if here not in ("PROVED", "WATCHME") or doc.get("id") == UNRECEIVABLE:
            continue
        for spec in _specs(doc):
            if str(spec.get("probe", "")).startswith(BERTH):
                out.append((doc["id"], doc, spec))
    assert out, f"no standing ticket names a probe under {BERTH} — the population vanished"
    return out


# --- teeth ------------------------------------------------------------------

def test_watch_carry_states_holds_and_finding():
    from cairn.tools.base.probe import watch_carry

    tid = "ab12cd34ef56"
    fired = watch_carry(tid, lambda c: {"finding": "fixture fault"}, fails=lambda now, c: True)({})
    assert fired == {"finding": "fixture fault", "ticket": tid, "holds": False}, fired
    quiet = watch_carry(tid, lambda c: {"finding": "x"}, fails=lambda now, c: False)({})
    assert quiet["holds"] is True and quiet["ticket"] == tid, quiet
    assert watch_carry(tid, holds=lambda c: True)({})["holds"] is True
    blank = watch_carry(tid, holds=lambda c: False)({})
    assert blank["holds"] is False and blank["finding"].strip(), blank

    def _boom(*_):
        raise RuntimeError("fixture raise")
    broke = watch_carry(tid, _boom, fails=lambda now, c: False)({})
    assert broke["holds"] is False and "RuntimeError" in broke["finding"], broke
    broke = watch_carry(tid, lambda c: {}, holds=_boom)({})
    assert broke["holds"] is False and "RuntimeError" in broke["finding"], broke

    moved = watch_carry(tid, lambda c: {"ticket": "/x.json"}, holds=lambda c: True)({})
    assert moved["ticket"] == tid and moved["ticket_path"] == "/x.json", moved

    for bad, kw in (("abc", {"holds": lambda c: True}), (tid, {}),
                    (tid, {"holds": lambda c: True, "fails": lambda n, c: True})):
        try:
            watch_carry(bad, **kw)
        except (ValueError, TypeError):
            continue
        raise AssertionError(f"watch_carry({bad!r}, {sorted(kw)}) was not refused")


def test_every_standing_base_probe_posts_watch():
    for tid, _doc, spec in _standing():
        mod = spec["probe"][:-3].replace("/", ".")
        probe = importlib.import_module(mod).PROBE
        assert probe.verb == "watch", f"{tid}: {spec['probe']} posts verb {probe.verb!r}"
        assert probe.to == "harbor_master", f"{tid}: {spec['probe']} posts to {probe.to!r}"
        payload = probe.payload({})
        assert payload.get("ticket") == tid, \
            f"{tid}: {spec['probe']}'s payload names ticket {payload.get('ticket')!r}"
        assert isinstance(payload.get("holds"), bool), f"{tid}: holds is {payload.get('holds')!r}"
        if payload["holds"] is False:
            assert isinstance(payload.get("finding"), str) and payload["finding"].strip(), \
                f"{tid}: holds False with no finding"


def test_every_standing_base_spec_names_the_receiver():
    for tid, doc, spec in _standing():
        assert spec.get("receiver") == RECEIVER, f"{tid}: receiver is {spec.get('receiver')!r}"
        err = watchme_spec_error(doc) or ""
        assert "receiver" not in err, f"{tid}: {err}"


def test_the_unreceivable_probe_sent_its_ticket_to_fixme():
    [path] = list(_tickets().glob(f"{UNRECEIVABLE}-*.json"))
    doc = json.loads(path.read_text("utf-8"))
    assert "[FIXME" in doc["workflow_and_state"], doc["workflow_and_state"]
    assert any(isinstance(f, dict) and f.get("kind") == "watchme" for f in doc.get("fixme") or []), \
        doc.get("fixme")


def test_base_probes_report_to_the_watch():
    """The composite tooth (the falsifier carries no numbered clauses)."""
    test_watch_carry_states_holds_and_finding()
    test_every_standing_base_probe_posts_watch()
    test_every_standing_base_spec_names_the_receiver()
    test_the_unreceivable_probe_sent_its_ticket_to_fixme()


if __name__ == "__main__":
    checks = [
        test_watch_carry_states_holds_and_finding,
        test_every_standing_base_probe_posts_watch,
        test_every_standing_base_spec_names_the_receiver,
        test_the_unreceivable_probe_sent_its_ticket_to_fixme,
        test_base_probes_report_to_the_watch,
    ]
    failures = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — every standing base probe reports {ticket, holds, finding} to the watch verb")
