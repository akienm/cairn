"""gate — a gate opens on an ``==`` compare, and never on an opinion.

AKIEN, 2026-08-13, and it is the whole specification:

    "NO GATES MAY CONSULT ORACLES EVER PERIOD. A GATE ONLY OPENS WHEN A FINDINGS REPORT
     MATCHES WHAT IT ALLOWS. ITS AN == compare. Must be identical. NO ORACLE."

So this module is four lines of meaning wearing a lot of documentation. A gate holds a
findings report and an allowlist; it opens when they are IDENTICAL. Not "no worse than",
not "within tolerance", not "a judge says close enough". Identical.

WHY IDENTICAL AND NOT SUBSET, which is the thing everyone reaches for first. A subset
compare ("nothing unexpected") makes the allowlist a PERMISSION SLIP: it can only ever be
too generous, and it goes stale in the safe-looking direction — the day a finding stops
firing, the gate keeps allowing it and nobody learns that the world improved. Identity
makes the allowlist a SPECIFICATION OF THE EXPECTED STATE. A finding that disappears
closes the gate exactly as loudly as one that appears, and somebody has to look and
re-baseline. That is Law 9 turned into a compare: green is earned every time, never
inherited from the last time somebody wrote the list.

WHAT IS NORMALIZED, AND IT IS ONLY ONE THING. Findings are compared as canonical JSON,
SORTED. Sorting is not a loosening: without it the gate measures the scanner's iteration
order rather than its findings, and a dict rebuild or a filesystem walk in a different
order would close a gate that found precisely what it was supposed to find. Duplicates are
NOT collapsed — two identical findings are two findings, so the compare is a multiset
compare, and a scanner that starts double-firing is caught rather than deduplicated into
looking correct.

WHY THE VERDICT CARRIES THE DIFF BOTH WAYS. A closed gate that says only "closed" makes
the next mind re-run it to find out what happened, which is the incomplete-diagnostic
defect (I-complete-diagnostic-on-first-pass). ``verdict`` returns the unexpected findings
AND the allowed entries that went missing, so one read is enough.

THIS TOOL IS HOW GATE-NESS BECOMES MEASURABLE. Before it, "is this a gate?" lived in
prose in a charter, where nothing could check it and where a gate could quietly grow an
oracle. Now a gate is a component whose import closure reaches ``cairn.tools.gate``, which
``cairn determinism`` reads with the same walk it uses for the LLM — so "no gate consults
an oracle" is a walk over two import facts, not a sentence anyone has to remember. The
enforcement lives at determinism's proof, which the corpus runs; a gate that grows a path
to the inference host turns the whole corpus red.

    from cairn.tools.gate import gate
    v = gate.verdict(findings, allowed)
    if not v["opens"]: ...            # v["unexpected"], v["missing"] say exactly why

A TOOL HAS USERS, NOT AN OWNER (Law 6). This holds no state — the findings and the
allowlist both arrive as arguments, and nothing is remembered between calls.

AN ABSENT BASELINE IS AN ERROR, NOT AN EMPTY ONE (Akien, 2026-08-13: "an absent
allowed.json is an ERROR"). The first cut read a missing file as an empty allowlist, which
sounds strict — it closes the gate — and is still wrong, because it DECIDES ON THE
OPERATOR'S BEHALF and then reports a verdict as though someone had declared it. There are
three states, and the middle one is the whole point: "I looked and this gate allows
nothing" is `[]`, an authored file, a claim somebody made; "there is no file" is a gate
that was never configured, and a gate that has not been configured has no business
returning a verdict at all. Collapsing the two makes an unconfigured gate indistinguishable
from a deliberately strict one, and the record of the run cannot tell them apart afterwards
either. So ``allowed_from`` RAISES. An empty file is legal, meaningful, and cheap to write.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

OPEN = "OPEN"
CLOSED = "CLOSED"

BASELINE = "allowed.json"


class NoBaseline(Exception):
    """A gate was asked for a verdict with no declared allowlist on disk.

    Loud and terminal by ruling. Not a warning, not a default, not an empty list: an
    unconfigured gate must not produce a verdict, because a verdict from one cannot be
    told from a verdict from a gate that deliberately allows nothing.
    """


def allowed_from(path) -> list:
    """Read a gate's declared baseline. ABSENT IS AN ERROR (Akien, 2026-08-13).

    ``path`` may be the baseline file or the directory holding it. An authored ``[]`` is
    the way to say "this gate allows nothing" — that is a declaration, and declaring it
    costs one line.
    """
    path = Path(path)
    if path.is_dir():
        path = path / BASELINE
    if not path.is_file():
        raise NoBaseline(
            f"no baseline at {path} — a gate with no declared allowlist may not return a "
            "verdict. If this gate allows nothing, say so: write `[]` to that file. An "
            "absent baseline is an ERROR, never an empty one (Akien, 2026-08-13)."
        )
    return json.loads(path.read_text())


def canonical(finding) -> str:
    """One finding as one canonical string: sorted keys, no whitespace slack.

    ``default=str`` so a Path or a datetime inside a finding renders rather than raising —
    a gate that crashes on an unusual finding is a gate that fails open, and the shape of
    a finding is the caller's business, not this tool's.
    """
    return json.dumps(finding, sort_keys=True, separators=(",", ":"), default=str)


def canonical_report(findings) -> list[str]:
    """A findings report as a sorted list of canonical strings — the compared form.

    Sorted so scan order cannot decide a verdict; a LIST, not a set, so duplicates survive
    into the compare.
    """
    return sorted(canonical(f) for f in findings)


def opens(findings, allowed=()) -> bool:
    """Akien's sentence, executable: identical, or the gate stays shut."""
    return canonical_report(findings) == canonical_report(allowed)


def verdict(findings, allowed=()) -> dict:
    """The gate's whole answer in one read.

    ``unexpected`` — fired but not allowed. ``missing`` — allowed but did not fire; the
    allowlist is stale in the direction that looks safe, which is the direction identity
    exists to catch.
    """
    got, want = Counter(canonical_report(findings)), Counter(canonical_report(allowed))
    unexpected, missing = got - want, want - got
    is_open = not unexpected and not missing
    return {
        "verdict": OPEN if is_open else CLOSED,
        "opens": is_open,
        "compared": len(got),
        "allowed": len(want),
        "unexpected": [json.loads(k) for k, n in sorted(unexpected.items()) for _ in range(n)],
        "missing": [json.loads(k) for k, n in sorted(missing.items()) for _ in range(n)],
        "why": (
            "identical — the findings report matches what this gate allows"
            if is_open else
            f"{sum(unexpected.values())} unexpected, {sum(missing.values())} missing — "
            "a gate opens only on an identical compare"
        ),
    }
