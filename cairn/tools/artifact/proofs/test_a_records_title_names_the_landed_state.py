#!/usr/bin/env python3
"""Proof that a records commit is titled by the state its ticket landed (cdac80129536).

WHAT IT PROVES: git log is read as the history of crossings, and a records commit's title is
written by whoever commits. CairnCommons 708067e8 read "records: e194f4b4cb3e PROVED" over a
crossing clearance had bounced to [FIXME:waiting] — a permanent false record (Law 7). The
artifact door now asks the commit-msg question: a subject ``records: <ticket> <STATE>``, where
STATE is a state of that ticket's workflow, lands only when the ticket's cursor stands at STATE.

Teeth, one per falsifier clause (PROVES below), over a scratch commons (``set_diagnostic_roots``):
  (1) a ticket at [FIXME:waiting] under "records: <id> PROVED" faults, the fault naming FIXME;
  (2) a ticket at [PROVED] under the same subject passes, and one at [BUILDME:waiting] under
      "records: <id> BUILDME" passes;
  (3) subjects whose word is no state ("records: <id> cast", "records: <id> hollow seal",
      "<id>: build — x") pass;
  (4) a scratch git repo given the hook by ``install-title-hook`` refuses the lying commit and
      lands the honest one.

    bin/cairn test cairn/tools/artifact/proofs/test_a_records_title_names_the_landed_state.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

# Bound at CALL time, never at import, so a reverted subject reds the teeth instead of
# crashing the reader (the seam test_a_json_record_lands_in_one_canonical_form.py uses).
A = None  # type: ignore[assignment]

PROVES = {"cdac80129536": {
    "1": "test_a_title_naming_a_state_the_cursor_never_reached_faults",
    "2": "test_a_title_naming_the_landed_state_passes",
    "3": "test_a_title_whose_word_is_no_state_passes",
    "4": "test_the_installed_hook_refuses_the_lie_and_lands_the_truth",
}}

FAILURES: list[str] = []

BOUNCED = "c0ac00000001"
LANDED = "c0ac00000002"
BUILDING = "c0ac00000003"
PATH = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> "


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout


def _world(tmp: Path) -> Path:
    commons = tmp / "CairnCommons"
    (commons / "tickets").mkdir(parents=True)
    _git(commons, "init", "-q")
    _git(commons, "config", "user.email", "proof@cairn")
    _git(commons, "config", "user.name", "proof")
    _git(commons, "config", "commit.gpgsign", "false")
    plans = {BOUNCED: ("title fixture bounced to fixme", PATH.replace("PROVEME -> ", "PROVEME -> [FIXME:waiting] -> PROVED")),
             LANDED: ("title fixture landed proved", PATH + "[PROVED]"),
             BUILDING: ("title fixture waiting at buildme", "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED")}
    for tid, (slug, wf) in plans.items():
        (commons / "tickets" / f"{tid}-{slug.replace(' ', '-')}.json").write_text(
            json.dumps({"id": tid, "workflow_and_state": wf}, indent=2) + "\n")
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO, "parked": tmp / "parked"})
    return commons


def _faults(subject: str) -> list[str] | None:
    fn = getattr(A, "check_title", None)
    return None if fn is None else fn(subject)


def test_a_title_naming_a_state_the_cursor_never_reached_faults(commons: Path) -> None:
    f = _faults(f"records: {BOUNCED} PROVED")
    check("test_a_title_naming_a_state_the_cursor_never_reached_faults",
          bool(f) and "FIXME" in f[0], "check_title absent" if f is None else repr(f)[:160])


def test_a_title_naming_the_landed_state_passes(commons: Path) -> None:
    got = {s: _faults(s) for s in (f"records: {LANDED} PROVED", f"records: {BUILDING} BUILDME")}
    check("test_a_title_naming_the_landed_state_passes",
          all(v == [] for v in got.values()), repr(got)[:200])


def test_a_title_whose_word_is_no_state_passes(commons: Path) -> None:
    subs = [f"records: {BOUNCED} cast", f"records: {BOUNCED} hollow seal — 1 measured",
            f"{BOUNCED}: build — x", f"records: {BOUNCED} seal — proof green"]
    got = {s: _faults(s) for s in subs}
    check("test_a_title_whose_word_is_no_state_passes",
          all(v == [] for v in got.values()), repr({k: v for k, v in got.items() if v != []})[:200])


def test_the_installed_hook_refuses_the_lie_and_lands_the_truth(commons: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(REPO), "CAIRN_REPO": str(REPO),
           "CAIRN_ARTIFACT_ROOTS": json.dumps({"CairnCommons": str(commons)})}
    r = subprocess.run([sys.executable, "-m", "cairn.tools.artifact", "install-title-hook", "CairnCommons"],
                       capture_output=True, text=True, cwd=REPO, env=env)
    hook = commons / ".git" / "hooks" / "commit-msg"
    _git(commons, "add", "-A")
    lie = subprocess.run(["git", "-C", str(commons), "commit", "-qm", f"records: {BOUNCED} PROVED"],
                         capture_output=True, text=True, env=env)
    truth = subprocess.run(["git", "-C", str(commons), "commit", "-qm", f"records: {LANDED} PROVED"],
                           capture_output=True, text=True, env=env)
    log = subprocess.run(["git", "-C", str(commons), "log", "--format=%s"], capture_output=True,
                         text=True).stdout.splitlines()
    ok = (r.returncode == 0 and hook.exists() and lie.returncode != 0 and "FIXME" in lie.stderr
          and truth.returncode == 0 and log == [f"records: {LANDED} PROVED"])
    check("test_the_installed_hook_refuses_the_lie_and_lands_the_truth", ok,
          f"install rc {r.returncode} {r.stderr.strip()[-80:]!r}; lie rc {lie.returncode}; "
          f"truth rc {truth.returncode}; log {log}")


def main() -> int:
    global A
    try:
        from cairn.tools.artifact import artifact as door
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject cairn.tools.artifact.artifact does not load: {exc!r}")
        for n in PROVES["cdac80129536"].values():
            check(n, False, "subject absent")
        return 1
    A = door
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-records-title-proof-") as d:
            tmp = Path(d)
            try:
                commons = _world(tmp)
                test_a_title_naming_a_state_the_cursor_never_reached_faults(commons)
                test_a_title_naming_the_landed_state_passes(commons)
                test_a_title_whose_word_is_no_state_passes(commons)
                test_the_installed_hook_refuses_the_lie_and_lands_the_truth(commons)
            finally:
                A.set_diagnostic_roots(None)
    except Exception as exc:  # noqa: BLE001
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["cdac80129536"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
