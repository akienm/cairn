"""Proof for intention_extractor — the first cocoon stage: drafts are judged, never believed.

Teeth a hollow extractor could not pass:
  - A GROUNDED DRAFT PASSES: anchored, four-field, verbatim — candidate returned unchanged.
  - A FABRICATED ANCHOR IS CAUGHT: the founding defect (2026-07-26 fabricated attribution)
    refuses the draft, names the check, and carries the invented quote whole.
  - A MISSING WHY IS REFUSED, and so is field drift (an extra field, a skipped ``read``).
  - AN UNPARSEABLE DRAFT IS LOUD: raw draft carried whole in the refusal; the crossing still
    breadcrumbs (tokens were spent).
  - AN EMPTY SOURCE NEVER TOUCHES THE HOST: refused before the resolver, which is never called.
  - NO SEAM, NO EXTRACTION: the sole path is the injected resolve — nothing is invented.
  - EVERY CHECK IS TAUGHT: provenance naming a dated correction, registry pinned to the teeth.
  - THE CROSSINGS ARE NOT SILENT (born instrumented — the silent-devices lesson applied at
    birth): PASS and REFUSED breadcrumb alike; reads add nothing.
  - THE MODULE OPENS NO DOOR OF ITS OWN: import-pure by AST scan.

Runnable bare (NO host, NO DB, NO network):
    python3 cairn/devices/intention_extractor/proofs/test_intention_extractor.py   # exit 0 = green
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.core_values import CoreValuesMixin
from cairn.devices.intention_extractor import extractor
from cairn.devices.intention_extractor.extractor import (
    CHECKS,
    ExtractionRefused,
    IntentionExtractorDevice,
    source_digest,
)

# A source with a real what and why in it, long enough to clear the floor.
_SOURCE = (
    "we need a prebuild type step for you on each thing we design. like it goes to become "
    "a formal intention, and the first thing that happens is a hex call that does prebuild "
    "on that specific thing. because we'd build from the start as a learning device."
)


def _fresh_extractor() -> IntentionExtractorDevice:
    """A IntentionExtractorDevice, SILENCED — the proof reads its breadcrumbs off the device.

    Ticket a-device-logs-without-being-wired (2026-08-18): a device with no receiver used to HOLD
    its breadcrumbs, so a proof got the held list for free. It now derives its own component name
    and WRITES to ``~/.cairn/logs/intention_extractor/0/`` — which would empty every held-list assertion in this
    file and seed the live tree from a proof in the same stroke. ``set_diagnostic_receiver(None)``
    asks for the holding that used to be an accident. Law 7 is untouched: the record is never
    silently dropped, only its default home moved.
    """
    dev = IntentionExtractorDevice()
    dev.set_diagnostic_receiver(None)
    return dev


def _resolver_returning(text: str, counter: list | None = None):
    """A fake resolve seam in inference_domain.resolve's return shape, optionally counting calls."""
    def resolve(request: dict) -> dict:
        if counter is not None:
            counter.append(request)
        assert request["kind"] == "generate", "the seam speaks inference_domain's request shape"
        return {"answer": {"text": text}, "hit": False, "canonical": "x"}
    return resolve


def _good_draft() -> dict:
    return {
        "what": "a prebuild step that runs before each design becomes a formal intention",
        "why": "so the build starts from a learning device rather than a guess",
        "anchors": [
            "we need a prebuild type step for you on each thing we design",
            "we'd build from the start as a learning device",
        ],
        "read": "",
    }


def test_a_grounded_draft_passes():
    dev = _fresh_extractor()
    draft = _good_draft()
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(draft)))
    assert out["verdict"] == "PASS" and out["findings"] == []
    assert out["candidate"] == draft, "the candidate is returned UNCHANGED — judged, not repaired"
    assert out["checks_run"] == sorted(CHECKS), "every registered check ran"
    assert out["source_digest"] == source_digest(_SOURCE)


def test_a_fabricated_anchor_is_caught():
    dev = _fresh_extractor()
    draft = _good_draft()
    fabricated = "the graph type is a coordinate, not a class"  # the founding specimen
    draft["anchors"].append(fabricated)
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(draft)))
    assert out["verdict"] == "REFUSED", "an invented quote must refuse the draft"
    assert [f["check"] for f in out["findings"]] == ["anchors_verbatim"]
    assert out["findings"][0]["evidence"]["anchor"] == fabricated, \
        "the fabricated anchor is carried WHOLE in the finding (first-pass diagnostic)"


def test_a_missing_why_and_field_drift_are_refused():
    dev = _fresh_extractor()
    hollow = _good_draft()
    hollow["why"] = "  "
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(hollow)))
    assert out["verdict"] == "REFUSED" and any(
        "why" in f["finding"] for f in out["findings"]
    ), "silence is not a valid answer — an empty why is refused"

    drifted = _good_draft()
    drifted["confidence"] = 0.95          # an extra field is drift
    del drifted["read"]                    # a skipped labeling decision is a hole
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(drifted)))
    shape = [f for f in out["findings"] if f["check"] == "record_shape"]
    assert out["verdict"] == "REFUSED" and shape
    assert shape[0]["evidence"] == {"missing": ["read"], "extra": ["confidence"]}, \
        "the drift is NAMED both ways, not just detected"


def test_an_unparseable_draft_is_loud_and_still_breadcrumbs():
    dev = _fresh_extractor()
    prose = "Sure! The intention here seems to be about prebuild steps."
    try:
        dev.extract(_SOURCE, resolve=_resolver_returning(prose))
        raise AssertionError("prose is not a candidate — must refuse loudly")
    except ExtractionRefused as e:
        assert prose in str(e), "the raw draft is carried WHOLE in the refusal (Law 7)"
    held = dev.held_diagnostics()
    assert [h["gate"] for h in held] == ["extract"] and \
        held[0]["values"]["verdict"] == "UNPARSEABLE", \
        "tokens were spent — the crossing breadcrumbs even when the draft is garbage"


def test_a_fenced_draft_parses():
    dev = _fresh_extractor()
    fenced = "```json\n" + json.dumps(_good_draft()) + "\n```"
    out = dev.extract(_SOURCE, resolve=_resolver_returning(fenced))
    assert out["verdict"] == "PASS", "a markdown fence is wrapping, not content"


def test_a_quote_wrapped_anchor_is_not_a_fabrication():
    """Live-caught 2026-07-27, first live fire: qwen2.5:7b quoted the source verbatim but
    wrapped every anchor in literal quotation marks — all three honest quotes refused as
    fabricated. Wrapping is not content; and stripping it must NOT admit an actual
    fabrication that arrives wearing quotes."""
    dev = _fresh_extractor()
    honest = _good_draft()
    honest["anchors"] = [f'"{a}"' for a in honest["anchors"]]
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(honest)))
    assert out["verdict"] == "PASS", "a verbatim quote in quotation marks is still verbatim"

    dressed = _good_draft()
    dressed["anchors"] = ['"the graph type is a coordinate, not a class"']
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(dressed)))
    assert out["verdict"] == "REFUSED", "quote marks must not launder a fabrication"


def test_an_empty_source_never_touches_the_host():
    dev = _fresh_extractor()
    calls: list = []
    seam = _resolver_returning(json.dumps(_good_draft()), calls)
    for source in ("", "   \n  ", "too short to mean"):
        try:
            dev.extract(source, resolve=seam)
            raise AssertionError(f"source {source!r} is under the floor — must refuse")
        except ExtractionRefused:
            pass
    assert calls == [], "the resolver was NEVER called — refused before the host"
    assert dev.held_diagnostics() == [], "nothing crossed, so nothing breadcrumbs"


def test_no_seam_no_extraction():
    dev = _fresh_extractor()
    try:
        dev.extract(_SOURCE, resolve=None)
        raise AssertionError("no seam must mean no extraction — nothing is invented")
    except ExtractionRefused as e:
        assert "sole path" in str(e)


def test_the_judge_is_HELD_not_housed():
    """The device re-exports the judge's names, and that is all it does with them: the
    checks berth as machines/judge/ because bin/cmd/determinism read this component as a
    gate that could reach an oracle at SLEEP (live.py). The lane-level teeth live with
    the judge; what belongs HERE is that the two halves are still wired together and that
    this module has not quietly grown a second copy."""
    from cairn.devices.intention_extractor.machines.judge import judge
    assert extractor.INSPECTORS is judge.INSPECTORS, "the device must HOLD, not fork"
    assert extractor.CHECKS is judge.CHECKS
    src = Path(extractor.__file__).read_text(encoding="utf-8")
    assert "def inspect_record_shape" not in src and "def anchors_verbatim" not in src, \
        "a check defined here again is the carve-out undone"


def test_the_crossings_are_no_longer_silent():
    """Born instrumented — the silent-devices trouble (2026-07-27) applied at birth, not
    retrofitted: one breadcrumb per extraction crossing, REFUSED riding the same shape as
    PASS (a refusal is the checks working), reads adding nothing, HELD when no receiver."""
    dev = _fresh_extractor()
    assert dev.held_diagnostics() == [], "construction is not a crossing"
    dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(_good_draft())))
    bad = _good_draft()
    bad["anchors"] = ["never said this anywhere at all"]
    dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(bad)))
    held = dev.held_diagnostics()
    assert [h["gate"] for h in held] == ["extract", "extract"]
    # The breadcrumb names what RAN as well as what objected: a PASS whose lane list is
    # shorter is a check that stopped running, and `checks_failed: []` alone said nothing
    # about that either way (2026-08-13).
    assert held[0]["values"]["verdict"] == "PASS" and held[0]["values"]["checks_failed"] == []
    assert held[1]["values"] == dict(held[0]["values"], verdict="REFUSED",
                                     checks_failed=["anchors_verbatim"]), held[1]["values"]
    assert held[0]["values"]["checks_proved"] == len(held[0]["values"]["lanes"]) >= 6
    assert all(h["pointer"] == source_digest(_SOURCE) for h in held)
    assert all(h["home"] == "held" for h in held), \
        "with no receiver wired the records HOLD (Law 7) — never silently dropped"
    before = len(dev.held_diagnostics())
    dev.state(), dev.settings(), dev.intention()
    assert len(dev.held_diagnostics()) == before, "reads emit nothing"


def test_device_hood_and_owned_state():
    dev = _fresh_extractor()
    assert isinstance(dev, CoreValuesMixin), "the extractor is a device (Law 2)"
    assert list(dev.introspect()) == ["intention", "state", "settings", "other"], "Form v0 #2 order"
    dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(_good_draft())))
    s = dev.state()
    assert s["extractions"] == 1 and s["verdicts"]["PASS"] == 1
    assert s["last_source_digest"] == source_digest(_SOURCE)


def test_the_extractor_opens_no_door_of_its_own():
    """extractor.py is import-pure: no outbound-capable module — the host is reached only
    through the caller-injected seam (live wiring lives in live.py, through
    inference_domain). Same tooth-shape as orient's tooth 15."""
    tree = ast.parse(Path(extractor.__file__).read_text(encoding="utf-8"))
    # cairn.tools.gate joined the allowlist 2026-08-13: it mints the seed's proof-record
    # entry and reads a pass back out — pure data shaping, no outbound capability, and it
    # is what makes the checks report what they PROVED rather than only what they refused.
    # The judge machine joined the allowlist 2026-08-13 when the checks were carved out
    # of this module: it is import-pure (its own proof measures that), so holding it does
    # not give the device a door. The gate TOOL is deliberately NOT here — a device that
    # imports it is a gate, and this device has a sleep seam.
    allowed = {"__future__", "hashlib", "json", "cairn.tools.base.device",
               "cairn.devices.intention_extractor.machines.judge.judge"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert imported <= allowed, f"unexpected imports in extractor.py: {sorted(imported - allowed)}"


def _main() -> int:
    # DERIVED, NOT TYPED — the same defect the validation_store proof was carrying on
    # 2026-08-13: two teeth added here were defined, never listed, and never ran, and the
    # file printed the same PASS lines it prints when everything runs. Declaration order.
    checks = [v for k, v in globals().items()
              if k.startswith("test_") and callable(v)]
    assert len(checks) >= 12, (
        "the derived roster collapsed — a roster that shrinks silently is the defect it "
        f"replaced: {len(checks)}")
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — intention_extractor: anchored, labeled, refused first-pass")
    return 0

if __name__ == "__main__":
    raise SystemExit(_main())
