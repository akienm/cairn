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
import os
import shutil
import time
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
        self._tree: Path | None = None

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
        self._collect_feedback(record, bad)
        if bad:
            msg = red_fn(record, bad) if red_fn else self._default_red(bad, record)
            raise self.exception_class(msg, self._extract_findings(bad))
        return (note or self._default_note(record), record)

    @property
    def _feedback_dir(self) -> Path | None:
        return self._tree / "feedback" if self._tree else None

    def _collect_feedback(self, record: list[dict],
                          bad: list[dict]) -> None:
        """Write a structured feedback record after every gate firing."""
        if self._feedback_dir is None:
            return
        self._feedback_dir.mkdir(parents=True, exist_ok=True)
        stamp = "%.6f" % time.time()
        fb = {
            "gate": self.name,
            "timestamp": stamp,
            "verdict": "red" if bad else "green",
            "checks_total": len(record),
            "checks_passed": len(record) - len(bad),
            "checks_failed": len(bad),
            "record": record,
        }
        if bad:
            fb["mismatches"] = [
                {"identity": e["identity"],
                 "expected": e["expected"],
                 "actual": e["actual"]}
                for e in bad
            ]
        path = self._feedback_dir / ("%s-%s-%s.json" % (
            stamp, self.name, os.urandom(4).hex()))
        path.write_text(json.dumps(fb, indent=2, ensure_ascii=False),
                        encoding="utf-8")

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
        self._tree = tree
        return tree

    def adjust(self, sieve_name: str, dial: str, value) -> dict:
        """Adjust a sieve dial in the instance-space tree. Returns the prior state.

        Validates: tree must be constructed, sieve must exist in it,
        dial must be a non-empty string, value must be JSON-serializable.
        """
        if self._tree is None:
            raise ValueError(
                "%s has no instance-space tree — call construct() first" % self.name)
        if not isinstance(dial, str) or not dial.strip():
            raise ValueError("dial must be a non-empty string, got %r" % (dial,))
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError("value must be JSON-serializable: %s" % e) from e

        sieve_path = self._tree / ("%s.json" % sieve_name)
        if not sieve_path.is_file():
            raise ValueError(
                "sieve %r not in the living tree at %s" % (sieve_name, self._tree))

        data = json.loads(sieve_path.read_text(encoding="utf-8"))
        prior = data.get("dials", {}).get(dial)
        if "dials" not in data:
            data["dials"] = {}
        data["dials"][dial] = value
        sieve_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        return {"sieve": sieve_name, "dial": dial, "prior": prior, "new": value}

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
