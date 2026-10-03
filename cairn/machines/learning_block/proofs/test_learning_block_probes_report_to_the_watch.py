"""PROOF — every standing learning_block probe reports to harbor_master's watch verb (ticket 3c035a838446).

835b5736bf2b's decision D2 names the receiver for every standing WATCHME probe: harbor_master's
``watch`` verb (a88d6a368cfb), which reads ``{ticket, holds, finding}`` and sends a red ticket to
FIXME. This proof measures the cairn/machines/learning_block child: every standing learning_block probe posting through watch_carry to harbor_master's watch verb, and every such spec naming the receiver. 18693659d16b, whose spec names a probe file that never existed, stands at FIXME and so is outside the population.

What a hollow build cannot pass (Law 8):
  - An unreceivable ticket (18693659d16b) not at FIXME, or at FIXME with no watchme
    finding, fails test_the_unreceivable_probes_sent_their_tickets_to_fixme.
  - A probe left verbless, or carrying its ticket's PATH as
    ``ticket`` fails every_standing_learning_block_probe_posts_watch, which reads each live payload's
    verb, ``to``, ``ticket``, ``holds`` and ``finding``.

The population is read from the commons, never listed here: every ticket at a rest (PROVED or
WATCHME) whose watchme probe berths under cairn/machines/learning_block/probes. Live payloads are
asserted as INVARIANTS only — a holds value is the world's to change.

    python3 cairn/machines/learning_block/proofs/test_learning_block_probes_report_to_the_watch.py   # exit 0 = green
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
    "3c035a838446": {
        "all": "test_learning_block_probes_report_to_the_watch",
    },
}

BERTH = "cairn/machines/learning_block/probes/"
UNRECEIVABLE = ('18693659d16b',)
RECEIVER = {"what": "harbor_master watch verb", "in": "cairn/devices/cairn/machines/harbor_master"}


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
    """(id, ticket, spec) for every ticket at a rest whose watchme probe berths in learning_block."""
    out = []
    for path in sorted(_tickets().glob("*.json")):
        try:
            doc = json.loads(path.read_text("utf-8"))
            here = parse_workflow(doc["workflow_and_state"]).here
        except Exception:  # noqa: BLE001 — not a standing ticket this proof can read
            continue
        if here not in ("PROVED", "WATCHME"):
            continue
        for spec in _specs(doc):
            if str(spec.get("probe", "")).startswith(BERTH):
                out.append((doc["id"], doc, spec))
    assert out, f"no standing ticket names a probe under {BERTH} — the population vanished"
    return out


# --- teeth ------------------------------------------------------------------

def test_every_standing_learning_block_probe_posts_watch():
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


def test_every_standing_learning_block_spec_names_the_receiver():
    for tid, doc, spec in _standing():
        assert spec.get("receiver") == RECEIVER, f"{tid}: receiver is {spec.get('receiver')!r}"
        err = watchme_spec_error(doc) or ""
        assert "receiver" not in err, f"{tid}: {err}"


def test_the_unreceivable_probes_sent_their_tickets_to_fixme():
    """A probe no receiver can use (Akien's answer to open-291189a9766a) sends its ticket to
    FIXME through the watch verb, which takes it out of the standing population."""
    for uid in UNRECEIVABLE:
        [path] = list(_tickets().glob(f"{uid}-*.json"))
        doc = json.loads(path.read_text("utf-8"))
        assert "[FIXME" in doc["workflow_and_state"], f"{uid}: {doc['workflow_and_state']}"
        assert any(isinstance(f, dict) and f.get("kind") == "watchme" for f in doc.get("fixme") or []), \
            f"{uid}: no watchme finding in fixme: {doc.get('fixme')}"


def test_learning_block_probes_report_to_the_watch():
    """The composite tooth (the falsifier carries no numbered clauses)."""
    test_every_standing_learning_block_probe_posts_watch()
    test_every_standing_learning_block_spec_names_the_receiver()
    test_the_unreceivable_probes_sent_their_tickets_to_fixme()


if __name__ == "__main__":
    checks = [
        test_every_standing_learning_block_probe_posts_watch,
        test_every_standing_learning_block_spec_names_the_receiver,
        test_the_unreceivable_probes_sent_their_tickets_to_fixme,
        test_learning_block_probes_report_to_the_watch,
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
    print("green — every standing learning_block probe reports {ticket, holds, finding} to the watch verb")
