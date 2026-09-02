"""gate_class — the block-general gate abstraction.

One class, instantiable per-gate with config. Every gate in the system:
1. Has a name (identity — a proof record or notification says WHO)
2. Verdicts a proof record: expected == actual for every entry, no oracle
3. Returns (note, record) on green; raises its exception on red

The inspect step is domain-specific — each gate brings its own. The class
owns the verdict and the raise, and those two are the gate pattern: the
part that was replicated five times in transitions.py and is now stated
once.

build_inspector is the FIRST TENANT, not the owner (the relation ruling
2026-08-07-the-nest-is-block-general applies here the same way). A tenant
derives its proof record however its domain demands, then verdicts it
HERE.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from cairn.tools.gate import gate


class TransitionGate:
    """A named, instantiated gate at the block-general level.

    Config: name (identity), exception_class (what to raise on red).
    Contract: run(record) -> (note, record) on green, raise on red.
    """

    def __init__(self, name: str, *, exception_class: type,
                 notifies: str = "harbor_master"):
        self.name = name
        self.exception_class = exception_class
        self.notifies = notifies

    def run(self, record: list[dict], *,
            note: str | None = None,
            red_fn=None) -> tuple[str, list[dict]]:
        """The verdict, rendered: (note, record) or raise.

        record: list of gate.proved() entries — the proof the gate inspected.
        note: clean note for the journal. Default renders from the record.
        red_fn: callable(record, bad) -> str for the refusal message. Default
                renders from the mismatches.
        """
        bad = [e for e in record if not gate.passed(e)]
        if bad:
            msg = red_fn(record, bad) if red_fn else self._default_red(bad, record)
            raise self.exception_class(msg, self._extract_findings(bad))
        return (note or self._default_note(record), record)

    def _default_note(self, record: list[dict]) -> str:
        identities = ", ".join(e["identity"] for e in record)
        return "clean — the %s proved %d check(s): %s" % (
            self.name, len(record), identities)

    def _default_red(self, bad: list[dict], record: list[dict]) -> str:
        lines = []
        for e in bad:
            lines.append("  [%s] expected %r, actual %r" % (
                e["identity"], e["expected"], e["actual"]))
            findings = (e.get("values") or {}).get("findings")
            if findings:
                for f in findings:
                    lines.append("    - %s" % f.get("about", str(f)))
        return (
            "%s refused — %d of %d checks did not match — a gate opens only "
            "when every expected equals its actual. Nothing was journaled.\n%s"
            % (self.name, len(bad), len(record), "\n".join(lines)))

    def construct(self, seeds_dir: str | Path, instance_root: str | Path) -> Path:
        """Write seed files into instance-space, creating the gate tree.

        Returns the tree path. On first construction the tree is byte-identical
        to the seeds; on subsequent calls existing files are left alone (the
        instance-space copy is the living state, seeds are the starting state).
        """
        seeds_dir = Path(seeds_dir)
        tree = Path(instance_root) / "tools" / "gate" / self.name
        tree.mkdir(parents=True, exist_ok=True)
        for seed in sorted(seeds_dir.glob("*.json")):
            dest = tree / seed.name
            if not dest.exists():
                shutil.copy2(seed, dest)
        return tree

    @staticmethod
    def _extract_findings(bad: list[dict]) -> list[dict]:
        """Findings read back out of the record's mismatches."""
        out: list[dict] = []
        for entry in bad:
            found = (entry.get("values") or {}).get("findings")
            out.extend(found or [{
                "about": "lane %s refused and named no finding" % entry["identity"],
                "expected": entry["expected"],
                "actual": entry["actual"],
                "compare": "exact",
                "method": entry["identity"],
                "component": entry["identity"],
            }])
        return out
