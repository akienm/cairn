"""One mouth answers the learning question (ticket 96f71a89a0fa).

`learning_declared` reads `how_it_learns` only: blank or absent reds, the retired `learns`
key reds on its return, and an unparseable charter reds instead of raising. The watch over
the corpus (probes/one_mouth_answers_the_learning_question.py) reads offenders and the
falsification run. The live corpus answers once.

WHY A PROOF OF ITS OWN, NOT TEETH INSIDE test_inspector.py: the hollow reading reverts each
file the build wrote, one at a time, and reruns the ticket's proofs per reversion. This build
wrote 92 charters. Inside the whole-inspector proof (~10 min a run) that was ~16 hours, and
measured 2026-11-12 it was killed at 1500s and at 4000s with nothing sealed. Here a run is
seconds, so every charter's reversion is read.

Hermetic but for the last tooth, which asserts an invariant over the live corpus (never a
snapshot of its size).
"""

from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

# The teeth run in order and the live census is the last of them, so it closes ok only when
# the one-field, retired-field, unparseable and probe teeth all held.
PROVES = {
    "96f71a89a0fa": {"all": "every live charter answers the learning question with one mouth"},
}


class _Teeth:
    """Announce-style teeth: tooth(name) closes the previous section ok and opens the next."""

    def __init__(self) -> None:
        self.open: str | None = None

    def __call__(self, name: str) -> None:
        if self.open:
            print(f"  ok    {self.open}")
        self.open = name

    def done(self) -> None:
        if self.open:
            print(f"  ok    {self.open}")
        self.open = None

    def failed(self, exc: BaseException) -> None:
        print(f"  FAIL  {self.open or 'setup'}")
        print(f"        {type(exc).__name__}: {exc}")
        self.open = None


tooth = _Teeth()


def _component(root: Path, name: str, **charter_extra) -> Path:
    """A fixture component the whole inspector reads clean: charter, device, sealed proof."""
    from cairn.machines.build_inspector.inspector import _source_fingerprint
    d = root / name
    (d / "proofs").mkdir(parents=True)
    charter = {"component": name, "runtime_role": "tool", "gated_by": ["CC"],
               "how_it_learns": "fixture component — does not learn", "public_interface": [],
               "claim_provenance": {"role": "cc-read", "what": "cc-read", "why": "cc-read"}}
    charter.update(charter_extra)
    (d / "intention+why.json").write_text(json.dumps(charter))
    (d / "proofs" / "test_x.py").write_text("assert True\n")
    (d / "dev.py").write_text("from base import BaseDevice\n\n\nclass D(BaseDevice):\n"
                              "    def work(self):\n        self.emit('gate')\n")
    (d / "validations").mkdir()
    (d / "validations" / "test_x.json").write_text(json.dumps([{
        "claim": "fixture", "caller": "test", "date": "2026-01-01T00:00:00",
        "method": "fixture", "verdict": "green",
        "evidence": {"source_fingerprint": _source_fingerprint(d),
                     "teeth_green": ["test_the_fixture"]},
        "falsifier": "test", "horizon": "test"}]))
    return d


def _methods(root: Path, name: str) -> list[str]:
    from cairn.machines.build_inspector.inspector import inspect
    return [f["method"] for f in inspect(root=root, component=name)["findings"]]


def main() -> None:
    from cairn.machines.build_inspector.inspector import inspect, learning_declared
    from cairn.machines.build_inspector.probes import one_mouth_answers_the_learning_question as OM

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        root = tmp / "cairn"
        (tmp / "base.py").write_text("from cairn.tools.base.diagnostic import DiagnosticBase\n\n\n"
                                     "class BaseDevice(DiagnosticBase):\n    pass\n")

        tooth("learning_declared reads how_it_learns: blank or absent reds, populated passes")
        _component(root, "healthy")
        assert inspect(root=root, component="healthy")["clean"], \
            "a charter with a populated how_it_learns and no learns must pass"
        _component(root, "blank", how_it_learns="")
        assert _methods(root, "blank") == ["learning_declared"], \
            "a charter with how_it_learns: '' must red exactly learning_declared"
        absent = _component(root, "absent")
        c = json.loads((absent / "intention+why.json").read_text())
        del c["how_it_learns"]
        (absent / "intention+why.json").write_text(json.dumps(c))
        f = learning_declared(c, absent)
        assert [x["method"] for x in f] == ["learning_declared"], \
            f"a charter with no how_it_learns key must red learning_declared: {f}"

        # The retired key coming back is a second mouth: it reds whatever its value, even
        # beside a populated how_it_learns (the falsification run the watch requires).
        tooth("learning_declared refuses the retired field")
        two = _component(root, "two_mouths", learns="It does not.")
        f = inspect(root=root, component="two_mouths")["findings"]
        assert [x["method"] for x in f] == ["learning_declared"], \
            f"a charter carrying learns beside how_it_learns must red exactly learning_declared: {f}"
        assert "retired" in f[0]["about"] and f[0]["values"]["retired"] == "learns", f
        assert two.is_dir()

        # An unparseable charter reds, and the inspector does not raise over it.
        tooth("learning_declared reds an unparseable charter")
        broken = _component(root, "bad_json")
        (broken / "intention+why.json").write_text('{"component": "bad_json",')
        f = learning_declared({"component": "bad_json"}, broken)
        assert [x["method"] for x in f] == ["learning_declared"] and "parses" in f[0]["about"] \
            and f[0]["values"]["error"], f"an unparseable charter must red learning_declared: {f}"
        (broken / "intention+why.json").write_text("[]")
        f = learning_declared({"component": "bad_json"}, broken)
        assert len(f) == 1 and "parses" in f[0]["about"], \
            f"a charter whose top level is not an object must red learning_declared: {f}"
        # The whole inspector over unparseable text must not raise. (A "[]" charter raises in
        # orient's device census, outside this sieve: idea 2026-11-12-orient-s-device-census-...)
        (broken / "intention+why.json").write_text('{"component": "bad_json",')
        inspect(root=root, component="bad_json")

    # The watch over the corpus: its census, its trigger and its enough, over scratch roots.
    tooth("the one-mouth probe reads offenders and the falsification run")
    assert dataclasses.is_dataclass(OM.PROBE) and callable(OM.PROBE.carry) \
        and callable(OM.PROBE.enough), "PROBE must be a Probe with a carry and an enough"
    with tempfile.TemporaryDirectory() as t:
        world = Path(t) / "repo"
        (world / "a").mkdir(parents=True)
        (world / "b").mkdir()
        (world / "a" / "intention+why.json").write_text(json.dumps({"how_it_learns": "It does not."}))
        (world / "b" / "intention+why.json").write_text(
            json.dumps({"how_it_learns": "Yes, by counting.", "learns": "It does not."}))
        ctx = {"roots": {"cairn": str(world)}}
        c = OM.census(world)
        assert (c["charters"], c["both"], c["contradictions"], c["offenders"]) == \
            (2, 1, 1, ["b/intention+why.json"]), c
        assert OM.PROBE.trigger(None, ctx) and not OM.PROBE.enough(ctx), \
            "one charter with two mouths must trigger the watch and keep it open"
        (world / "b" / "intention+why.json").write_text(json.dumps({"how_it_learns": "Yes."}))
        ctx = {"roots": {"cairn": str(world)}}
        assert not OM.PROBE.trigger(None, ctx) and not OM.PROBE.enough(ctx), \
            "a clean corpus with no falsification run on record must not clear the watch"
        v = world / OM._VALIDATION
        v.parent.mkdir(parents=True)
        v.write_text(json.dumps([{"verdict": "green",
                                  "evidence": {"teeth_green": [OM._TOOTH]}}]))
        ctx = {"roots": {"cairn": str(world)}}
        assert OM.PROBE.enough(ctx), "a clean corpus and a green falsification run clear it"

    # And the live corpus answers once: no charter in this repo carries learns or lacks
    # how_it_learns (an invariant over live data, not a snapshot of its size).
    tooth("every live charter answers the learning question with one mouth")
    live = OM.census()
    assert live["charters"] > 0 and live["offenders"] == [] and live["both"] == 0, \
        {k: v for k, v in live.items() if k != "charters"}

    tooth.done()
    print("one mouth answers the learning question: all teeth green")


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        tooth.failed(e)
        raise
