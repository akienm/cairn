"""Teeth for ticket 32978fb58c94 — /sail seals through `cairn test --seal`, not a network seal.

After d80360545e91 retired the network seal, get_isolation('netns') raises, so a SKILL.md that
tells the builder to seal with ``run_proof(..., isolation="netns")`` hands every voyage an
instruction that fails. The falsifier is the skill text itself: no ``isolation="netns"``, and
the seal step names ``cairn test --seal``. Reads skills/sail/SKILL.md only.

Run:  cd ~/dev/src/cairn && bin/cairn test skills/sail/proofs/test_sail_seals_through_cairn_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "32978fb58c94": {
        "all": "test_the_seal_step_names_cairn_test_seal_and_no_network_seal",
    },
}

_SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"
_SEAL_HEADING = "## 4. Journal PROVEME, then seal"


def _seal_step(text: str) -> str:
    """The body of step 4, up to the next '## ' heading ('' when the heading is gone)."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(_SEAL_HEADING)), None)
    if start is None:
        return ""
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end])


def test_the_seal_step_names_cairn_test_seal_and_no_network_seal():
    text = _SKILL_MD.read_text(encoding="utf-8")
    assert text.count('isolation="netns"') == 0, "SKILL.md still names the retired network seal"
    step = _seal_step(text)
    assert step, f"no {_SEAL_HEADING!r} heading in SKILL.md"
    assert "cairn test --seal" in step, f"step 4 does not name `cairn test --seal`:\n{step}"
    print("step 4 seals through `cairn test --seal`; no isolation=\"netns\" in SKILL.md")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
