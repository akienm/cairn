"""Proof for cairn/machines/installer — the projection over host-seam intentions.

Teeth a hollow build could not pass:

  - DISCOVERY BY NODE_CLASS, NOT BY NAME. Given a directory with host-seam and
    non-host-seam files, gather_host_seams returns ONLY the host-seam nodes.
    A build that hand-lists seams trips this.
  - VERIFY-FIRST IS IDEMPOTENT. A seam whose verify already passes is reported
    as already_applied and its apply steps are never presented. A build that
    blindly re-applies trips this.
  - OPERATOR DECLINE IS RESPECTED. A seam the operator says N to is reported
    as skipped. A build that applies without asking trips this.
  - RED ON VERIFY FAILURE. A seam whose verify fails after apply is reported
    as failed/RED, never silently installed. A build that swallows verify
    failures trips this.
  - DRY-RUN OFFERS WITHOUT APPLYING. With dry_run=True, applicable seams are
    listed but no ask/apply/verify cycle runs. A build that ignores the flag
    trips this.
  - ASK_USER.SH IS A DUMB GATE. It forks on Y/N, runs one of two command
    strings via bash -c, owns nothing it runs, and exits non-zero on bad
    input. A build where the gate knows what the commands do trips this.
  - THE CORPUS IS COMPILED, NEVER HAND-LISTED. Adding a fixture seam to the
    directory causes gather_host_seams to return it with no code change.
    A build with a seam registry trips this.

Self-contained (fixture host-seams in a temp dir) and self-cleaning.
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

from cairn.machines.installer.installer import (
    gather_host_seams,
    install,
    run_verify,
)

ASK_USER = REPO / "cairn" / "machines" / "installer" / "ask_user.sh"

failures: list[str] = []


def fail(name: str, msg: str) -> None:
    failures.append(f"  FAIL [{name}]: {msg}")


def make_seam(
    sid: str,
    verify_cmd: str,
    *,
    node_class: str = "host-seam",
    apply_steps: dict | None = None,
) -> dict:
    seam: dict = {
        "id": sid,
        "node_class": node_class,
        "intention": f"fixture seam {sid}",
        "verify": {"command": verify_cmd},
    }
    if apply_steps:
        seam["apply"] = apply_steps
    return seam


def write_seam(d: Path, seam: dict) -> Path:
    p = d / f"{seam['id']}.json"
    p.write_text(json.dumps(seam, indent=2))
    return p


def test_discovery():
    """gather_host_seams returns only host-seam nodes, skipping others."""
    with tempfile.TemporaryDirectory(prefix="cairn_installer_proof_") as td:
        d = Path(td)
        write_seam(d, make_seam("seam-a", "true"))
        write_seam(d, make_seam("seam-b", "true"))
        write_seam(d, make_seam("not-a-seam", "true", node_class="code-seam"))
        # charter files start with _ and should be skipped
        (d / "_charter+why.json").write_text(json.dumps({"node_class": "host-seam"}))

        found = gather_host_seams(d)
        ids = [s["id"] for s in found]

        if "not-a-seam" in ids:
            fail("discovery", "non-host-seam node was included")
        if "seam-a" not in ids or "seam-b" not in ids:
            fail("discovery", f"host-seam nodes missing: got {ids}")
        if len(found) != 2:
            fail("discovery", f"expected 2 host-seams, got {len(found)}")


def test_verify_first_idempotent():
    """A seam whose verify passes is already_applied — apply never runs."""
    with tempfile.TemporaryDirectory(prefix="cairn_installer_proof_") as td:
        d = Path(td)
        write_seam(d, make_seam("already-done", "true"))

        results = install(intentions_dir=d, ask_fn=lambda q: True)

        if len(results) != 1:
            fail("idempotent", f"expected 1 result, got {len(results)}")
            return
        r = results[0]
        if r["status"] != "already_applied":
            fail("idempotent", f"expected already_applied, got {r['status']}")


def test_operator_decline():
    """A seam the operator declines is skipped."""
    with tempfile.TemporaryDirectory(prefix="cairn_installer_proof_") as td:
        d = Path(td)
        write_seam(d, make_seam("unwanted", "false"))

        results = install(intentions_dir=d, ask_fn=lambda q: False)

        if len(results) != 1:
            fail("decline", f"expected 1 result, got {len(results)}")
            return
        r = results[0]
        if r["status"] != "skipped":
            fail("decline", f"expected skipped, got {r['status']}")


def test_red_on_verify_failure():
    """A seam whose verify fails after apply is RED."""
    with tempfile.TemporaryDirectory(prefix="cairn_installer_proof_") as td:
        d = Path(td)
        write_seam(d, make_seam(
            "bad-seam", "false",
            apply_steps={"1_step": "this step does not fix the verify"},
        ))

        results = install(intentions_dir=d, ask_fn=lambda q: True)

        if len(results) != 1:
            fail("red_on_fail", f"expected 1 result, got {len(results)}")
            return
        r = results[0]
        if r["status"] != "failed":
            fail("red_on_fail", f"expected failed, got {r['status']}")
        if "RED" not in r["detail"]:
            fail("red_on_fail", f"detail should contain RED: {r['detail']}")


def test_dry_run():
    """dry_run lists seams without asking or applying."""
    asked = []
    with tempfile.TemporaryDirectory(prefix="cairn_installer_proof_") as td:
        d = Path(td)
        write_seam(d, make_seam("pending", "false"))

        results = install(
            intentions_dir=d,
            dry_run=True,
            ask_fn=lambda q: (asked.append(q), True)[1],
        )

        if asked:
            fail("dry_run", "ask_fn was called during dry run")
        if len(results) != 1:
            fail("dry_run", f"expected 1 result, got {len(results)}")
            return
        r = results[0]
        if r["status"] != "offered":
            fail("dry_run", f"expected offered, got {r['status']}")


def test_corpus_is_compiled():
    """Adding a seam to the directory includes it — no code change needed."""
    with tempfile.TemporaryDirectory(prefix="cairn_installer_proof_") as td:
        d = Path(td)
        write_seam(d, make_seam("original", "true"))

        found_before = gather_host_seams(d)
        write_seam(d, make_seam("newcomer", "true"))
        found_after = gather_host_seams(d)

        if len(found_before) != 1:
            fail("compiled", f"before: expected 1, got {len(found_before)}")
        if len(found_after) != 2:
            fail("compiled", f"after: expected 2, got {len(found_after)}")
        ids_after = [s["id"] for s in found_after]
        if "newcomer" not in ids_after:
            fail("compiled", f"newcomer not found after add: {ids_after}")


def test_ask_user_yn():
    """ask_user.sh forks on Y/N and runs the right branch."""
    for answer, expect in [("Y", "yes-branch"), ("N", "no-branch")]:
        result = subprocess.run(
            ["bash", str(ASK_USER), "question?", "YN",
             "echo yes-branch", "echo no-branch"],
            input=f"{answer}\n", capture_output=True, text=True,
        )
        got = result.stdout.strip()
        if got != expect:
            fail("ask_yn", f"input={answer}: expected '{expect}', got '{got}'")
        if result.returncode != 0:
            fail("ask_yn", f"input={answer}: exit {result.returncode}")


def test_ask_user_bad_type():
    """ask_user.sh exits non-zero on an unknown type."""
    result = subprocess.run(
        ["bash", str(ASK_USER), "question?", "MENU", "echo y", "echo n"],
        input="Y\n", capture_output=True, text=True,
    )
    if result.returncode == 0:
        fail("ask_bad_type", "should exit non-zero on unknown type")


def test_ask_user_bad_input():
    """ask_user.sh exits non-zero on input that is neither Y nor N."""
    result = subprocess.run(
        ["bash", str(ASK_USER), "question?", "YN", "echo y", "echo n"],
        input="maybe\n", capture_output=True, text=True,
    )
    if result.returncode == 0:
        fail("ask_bad_input", "should exit non-zero on 'maybe'")


def test_applied_and_verified():
    """A seam that is accepted + verify passes after apply → applied."""
    with tempfile.TemporaryDirectory(prefix="cairn_installer_proof_") as td:
        d = Path(td)
        marker = Path(td) / "applied_marker"
        write_seam(d, make_seam(
            "good-seam", f"test -f {marker}",
            apply_steps={"1_create": f"touch {marker}"},
        ))

        # The operator says yes; verify fails initially but the test
        # creates the marker to simulate a successful manual apply.
        def ask_and_apply(q):
            marker.touch()
            return True

        results = install(intentions_dir=d, ask_fn=ask_and_apply)

        if len(results) != 1:
            fail("applied", f"expected 1 result, got {len(results)}")
            return
        r = results[0]
        if r["status"] != "applied":
            fail("applied", f"expected applied, got {r['status']}: {r['detail']}")


def test_run_verify_no_command():
    """run_verify returns (False, reason) when no command is declared."""
    passed, output = run_verify({"verify": {}})
    if passed:
        fail("no_cmd", "should not pass with no verify command")
    if "no verify command" not in output:
        fail("no_cmd", f"unexpected output: {output}")


def main() -> int:
    tests = [
        test_discovery,
        test_verify_first_idempotent,
        test_operator_decline,
        test_red_on_verify_failure,
        test_dry_run,
        test_corpus_is_compiled,
        test_ask_user_yn,
        test_ask_user_bad_type,
        test_ask_user_bad_input,
        test_applied_and_verified,
        test_run_verify_no_command,
    ]

    for t in tests:
        t()

    if failures:
        print(f"RED — {len(failures)} failure(s):")
        for f in failures:
            print(f)
        return 1

    print(f"GREEN — {len(tests)} teeth, all pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
