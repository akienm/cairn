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
    python3 cairn/intention_extractor/proofs/test_intention_extractor.py   # exit 0 = green
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.intention_extractor import extractor
from cairn.intention_extractor.extractor import (
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
    dev = IntentionExtractorDevice()
    draft = _good_draft()
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(draft)))
    assert out["verdict"] == "PASS" and out["findings"] == []
    assert out["candidate"] == draft, "the candidate is returned UNCHANGED — judged, not repaired"
    assert out["checks_run"] == sorted(CHECKS), "every registered check ran"
    assert out["source_digest"] == source_digest(_SOURCE)


def test_a_fabricated_anchor_is_caught():
    dev = IntentionExtractorDevice()
    draft = _good_draft()
    fabricated = "the graph type is a coordinate, not a class"  # the founding specimen
    draft["anchors"].append(fabricated)
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(draft)))
    assert out["verdict"] == "REFUSED", "an invented quote must refuse the draft"
    assert [f["check"] for f in out["findings"]] == ["anchors_verbatim"]
    assert out["findings"][0]["evidence"]["anchor"] == fabricated, \
        "the fabricated anchor is carried WHOLE in the finding (first-pass diagnostic)"


def test_a_missing_why_and_field_drift_are_refused():
    dev = IntentionExtractorDevice()
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
    dev = IntentionExtractorDevice()
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
    dev = IntentionExtractorDevice()
    fenced = "```json\n" + json.dumps(_good_draft()) + "\n```"
    out = dev.extract(_SOURCE, resolve=_resolver_returning(fenced))
    assert out["verdict"] == "PASS", "a markdown fence is wrapping, not content"


def test_a_quote_wrapped_anchor_is_not_a_fabrication():
    """Live-caught 2026-07-27, first live fire: qwen2.5:7b quoted the source verbatim but
    wrapped every anchor in literal quotation marks — all three honest quotes refused as
    fabricated. Wrapping is not content; and stripping it must NOT admit an actual
    fabrication that arrives wearing quotes."""
    dev = IntentionExtractorDevice()
    honest = _good_draft()
    honest["anchors"] = [f'"{a}"' for a in honest["anchors"]]
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(honest)))
    assert out["verdict"] == "PASS", "a verbatim quote in quotation marks is still verbatim"

    dressed = _good_draft()
    dressed["anchors"] = ['"the graph type is a coordinate, not a class"']
    out = dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(dressed)))
    assert out["verdict"] == "REFUSED", "quote marks must not launder a fabrication"


def test_an_empty_source_never_touches_the_host():
    dev = IntentionExtractorDevice()
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
    dev = IntentionExtractorDevice()
    try:
        dev.extract(_SOURCE, resolve=None)
        raise AssertionError("no seam must mean no extraction — nothing is invented")
    except ExtractionRefused as e:
        assert "sole path" in str(e)


def test_every_check_is_taught_and_pinned():
    assert sorted(CHECKS) == ["anchors_verbatim", "record_shape"], \
        "registry pinned to the teeth — a new check joins by editing this proof too"
    for name, check in CHECKS.items():
        doc = check.__doc__ or ""
        assert "Provenance:" in doc and re.search(r"\d{4}-\d{2}-\d{2}", doc), \
            f"check {name} carries no dated correction — a check nobody was taught by"


def test_the_crossings_are_no_longer_silent():
    """Born instrumented — the silent-devices trouble (2026-07-27) applied at birth, not
    retrofitted: one breadcrumb per extraction crossing, REFUSED riding the same shape as
    PASS (a refusal is the checks working), reads adding nothing, HELD when no receiver."""
    dev = IntentionExtractorDevice()
    assert dev.held_diagnostics() == [], "construction is not a crossing"
    dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(_good_draft())))
    bad = _good_draft()
    bad["anchors"] = ["never said this anywhere at all"]
    dev.extract(_SOURCE, resolve=_resolver_returning(json.dumps(bad)))
    held = dev.held_diagnostics()
    assert [h["gate"] for h in held] == ["extract", "extract"]
    assert held[0]["values"] == {"verdict": "PASS", "checks_failed": []}
    assert held[1]["values"] == {"verdict": "REFUSED", "checks_failed": ["anchors_verbatim"]}
    assert all(h["pointer"] == source_digest(_SOURCE) for h in held)
    assert all(h["home"] == "held" for h in held), \
        "with no receiver wired the records HOLD (Law 7) — never silently dropped"
    before = len(dev.held_diagnostics())
    dev.state(), dev.settings(), dev.intention()
    assert len(dev.held_diagnostics()) == before, "reads emit nothing"


def test_device_hood_and_owned_state():
    dev = IntentionExtractorDevice()
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
    allowed = {"__future__", "hashlib", "json", "cairn.base.device"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert imported <= allowed, f"unexpected imports in extractor.py: {sorted(imported - allowed)}"


def _main() -> int:
    for check in (test_a_grounded_draft_passes,
                  test_a_fabricated_anchor_is_caught,
                  test_a_missing_why_and_field_drift_are_refused,
                  test_an_unparseable_draft_is_loud_and_still_breadcrumbs,
                  test_a_fenced_draft_parses,
                  test_a_quote_wrapped_anchor_is_not_a_fabrication,
                  test_an_empty_source_never_touches_the_host,
                  test_no_seam_no_extraction,
                  test_every_check_is_taught_and_pinned,
                  test_the_crossings_are_no_longer_silent,
                  test_device_hood_and_owned_state,
                  test_the_extractor_opens_no_door_of_its_own):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — intention_extractor: drafts are judged not believed, fabricated attribution "
          "refuses, the why cannot be skipped, empty sources never touch the host, every check "
          "is taught, the crossings breadcrumb, and the module opens no door of its own")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
