"""cairn/machines/ruling/corpus.py — the falsifier for filed edge (b), kept re-runnable.

THE EDGE: nothing makes me OPEN a packet. The Stop hook reports rulings that exist; it
cannot see one that was never recorded. The obvious reach is a UserPromptSubmit hook that
notices ruling-shaped language in Akien's prompt and says "record this" — the same shape
turnscan already proved workable one layer up.

THE MEASUREMENT SAYS NO, and that is why this file exists rather than that hook. Measured
2026-07-31 over the real transcript corpus: ruling-shaped language fires on 28.5% of 855
Akien prompts. A hook that interrupts on better than one prompt in four is noise, and noise
gets trained away inside a day — it would end up worse than nothing, because a detector
everyone ignores still LOOKS like coverage.

Kept here, not in a scratchpad, for one reason: a number cited in CLAUDE.md whose script
was deleted is folklore — a measurement that has to be re-derived to be trusted, which is
a Law 1 defect and the exact way "~7400 chars" got loose in this system. Re-run it and the
claim either holds or it does not.

IT IS NOT A DETECTOR AND MUST NOT BECOME ONE. The tiers below were chosen to be GENEROUS —
to find the ceiling of what a lexical rule could ever catch, not to draw a usable line. A
future reader wanting the hook wants the host's LLM-adjudicated prompt hook (the ceiling
named in the turnscan charter for its sibling residue), not a tuned version of this.

    python3 -m cairn.machines.ruling.cli --corpus            # re-measure
"""

from __future__ import annotations

import glob
import json
import os
import re

# Deliberately generous. Narrowing these to cut the rate would be tuning a detector, which
# is the thing the measurement says not to build.
TIERS = {
    "ratify": [r"^\s*(yes|yeah|yep|correct|exactly)\b[\s,.!]", r"\bdo (that|it)\b",
               r"\bgo ahead\b", r"\bship it\b"],
    "negate": [r"^\s*(no|nope)\b[\s,.!]", r"\bthat'?s wrong\b", r"\bnot what i\b",
               r"\bwe (don'?t|do not|won'?t|will not)\b", r"\blet'?s not\b",
               r"\bstop\b", r"\bnever\b", r"\bis retired\b", r"\bkill (it|that)\b"],
    "correct": [r"\bi (told|said)\b", r"\byou (selected|chose|took)\b",
                r"\bthat'?s not\b", r"\binstead of\b", r"\bi meant\b"],
    "direct": [r"\bit should\b", r"\bit needs to\b", r"\bwe should\b", r"\bmake it\b",
               r"\bchange it to\b", r"\bfrom now on\b"],
}
_C = {k: [re.compile(p, re.I | re.M) for p in v] for k, v in TIERS.items()}

DEFAULT_CORPUS = os.path.expanduser("~/.claude/projects/-home-akien-dev-src-cairn/*.jsonl")


def _prompts(pattern: str):
    """Akien's actual prompts. Tool results, hook injections and //-command echoes are
    the harness talking, not him, and counting them would inflate the denominator — which
    would make the rate look BETTER than it is, in the direction that favours building the
    hook. Excluded on purpose."""
    for f in sorted(glob.glob(pattern)):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("type") != "user":
                    continue
                content = d.get("message", {}).get("content")
                if isinstance(content, list):
                    txt = "\n".join(b.get("text", "") for b in content
                                    if isinstance(b, dict) and b.get("type") == "text")
                elif isinstance(content, str):
                    txt = content
                else:
                    continue
                if not txt.strip() or "<local-command" in txt or "tool_use_id" in txt:
                    continue
                if txt.lstrip().startswith("<"):
                    continue
                yield txt


def measure(pattern: str = DEFAULT_CORPUS) -> dict:
    total, hits, any_hit = 0, {k: 0 for k in TIERS}, 0
    for txt in _prompts(pattern):
        total += 1
        fired = False
        for k, pats in _C.items():
            if any(p.search(txt) for p in pats):
                hits[k] += 1
                fired = True
        any_hit += 1 if fired else 0
    return {"prompts": total, "by_tier": hits, "any": any_hit,
            "rate": (any_hit / total) if total else 0.0}


def report(pattern: str = DEFAULT_CORPUS) -> int:
    r = measure(pattern)
    if not r["prompts"]:
        print(f"no prompts matched {pattern}")
        return 1
    print(f"{r['prompts']} Akien prompt(s)\n")
    for k, n in r["by_tier"].items():
        print(f"  {k:8} {n:5}  ({100.0 * n / r['prompts']:4.1f}%)")
    print(f"\n  ANY      {r['any']:5}  ({100.0 * r['rate']:4.1f}%)  "
          f"<- what a lexical UserPromptSubmit hook would fire on")
    print("\nRecorded 2026-07-31: 28.5% of 855. A hook firing on better than one prompt in "
          "four is noise, not physics — filed edge (b) stays an IOU, and its ceiling is the "
          "host's LLM-adjudicated prompt hook, not a tuned version of this.")
    return 0
