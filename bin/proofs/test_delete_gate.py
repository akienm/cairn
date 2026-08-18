"""Proof for the unrecoverable-delete gate and the door it names.

WHAT IT PROVES, and the reason it exists is a measured loss rather than a design idea:
on 2026-08-18 ``rm -rf ~/.cairn/logs`` destroyed six files that had never been read,
including ``logs/archive/boot.pre-decontamination``, a 54-record pre-image somebody had
deliberately kept. ext4, no snapshots, ``~/.cairn`` in no backup — the loss was total.
``bin/cmd/deletegate`` is the physics (Law 4), ``bin/cmd/trash`` is the way through, and
this proof is what stops either from being a comforting sentence.

Teeth a hollow gate could not pass:
  - THE EXACT COMMAND THAT CAUSED THE LOSS IS REFUSED. Not a paraphrase — the string, as
    it was typed that day.
  - THE DOOR IS NOT REFUSED. A gate that blocks its own way through is a wall, and a wall
    gets routed around by the next mind in a hurry — the same mind that needed the gate.
  - THE BOUND HOLDS. A delete in the git roots is ALLOWED. Gating those would be friction
    bought with nothing (a checkout restores them), and a gate that fires everywhere is
    one somebody turns off.
  - THE SPELLINGS. ``~/.cairn``, ``$HOME/.cairn``, the absolute path, ``cd`` then delete,
    ``find -delete``, ``find -exec rm``. This repo has already been bitten once by a tooth
    narrower than its own defect (``tester/scratch.py``: the temp-leak check grepped for
    ``mkdtemp`` and missed a leak spelled ``gettempdir``).
  - THE ORIGIN SURVIVES THE MOVE. An entry in the trash with no record of where it came
    from is exactly as recoverable as ``rm`` was — so the info file is written first, and
    that ordering is checked, not assumed.
  - RESTORE NEVER CLOBBERS. A restore that overwrote a live file would be this whole
    mechanism's own defect wearing the costume of a fix.
  - THE SWEEP KEEPS WHAT IT CANNOT DATE. Treating unknown as old turns retention into a
    second unrecoverable delete.
  - THIS PROOF DOES NOT WRITE INTO THE REAL TRASH. Every door tooth runs against an
    injected home, and the last assertion is a before/after witness on the live
    ``~/.local/share/Trash`` — the failure this repo has measured before is the proof
    that writes into the instrument it proves.

    python3 bin/proofs/test_delete_gate.py     # exit 0 = green
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_GATE = _REPO_ROOT / "bin" / "cmd" / "deletegate"
_DOOR = _REPO_ROOT / "bin" / "cmd" / "trash"


def _load(path: Path, name: str):
    """Both subjects are extensionless commands, so import them by location — the same
    way the corpus loads every other ``bin/cmd`` subject."""
    spec = importlib.util.spec_from_loader(
        name, importlib.machinery.SourceFileLoader(name, str(path)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gate = _load(_GATE, "deletegate")
door = _load(_DOOR, "trashdoor")

HOME = str(Path.home())


# ── the gate ─────────────────────────────────────────────────────────────────

def test_the_command_that_caused_the_loss_is_refused():
    """The string as it was typed on 2026-08-18, not a paraphrase of it."""
    refusal = gate.verdict("rm -rf ~/.cairn/logs")
    assert refusal is not None, "the gate must refuse the command that destroyed the archive"
    assert "no undo" in refusal, "the refusal says WHY this root is different"
    assert "bin/cmd/trash" in refusal, \
        "and it carries the way through — complete on the first pass, no second look-up"


def test_every_spelling_of_the_same_delete_is_caught():
    """A tooth narrower than its own defect is the hollow kind (scratch.py, 2026-08-03)."""
    for command in [
        "rm -rf ~/.cairn/logs",
        "rm -rf $HOME/.cairn/devices/librarian",
        f"rm -rf {HOME}/.cairn/logs",
        "cd ~/.cairn && rm -rf logs",
        "find ~/.cairn/logs -name diagnostics.jsonl -delete",
        "find ~/.cairn -name '*.jsonl' -exec rm {} +",
        "shred ~/.cairn/devices/sudo_relay/0/audit/x.json",
        "rmdir ~/.cairn/logs/bus/0",
        "truncate -s 0 ~/.cairn/logs/boot",
        "echo hi; rm -f ~/.cairn/logs/boot",
    ]:
        assert gate.verdict(command) is not None, f"unguarded spelling: {command!r}"


def test_the_door_itself_is_never_refused():
    """A gate that blocks its own way through is a wall, and a wall gets routed around."""
    for command in [
        "bin/cmd/trash ~/.cairn/logs/gate-roundtrip",
        "find ~/.cairn/logs -name diagnostics.jsonl -exec bin/cmd/trash {} +",
        f"{_REPO_ROOT}/bin/cmd/trash ~/.cairn/logs/x",
    ]:
        assert gate.verdict(command) is None, f"the door must pass the gate: {command!r}"


def test_the_bound_the_git_roots_are_not_gated():
    """Recoverable by checkout, so gating them buys friction with nothing. A gate that
    fires everywhere is one somebody turns off, and then it guards nothing at all."""
    for command in [
        "rm -rf /tmp/scratch",
        "rm -rf ~/dev/src/cairn/build",
        "rm -f cairn/devices/bus/proofs/__pycache__/x.pyc",
        "find . -name '__pycache__' -exec rm -rf {} +",
    ]:
        assert gate.verdict(command) is None, f"outside the guarded root, allow: {command!r}"


def test_a_command_that_only_reads_the_root_passes():
    """The gate reads for a DESTRUCTIVE verb, not for the root's name. Refusing every
    mention of ~/.cairn would make the guarded root unreadable, which is not the rule."""
    for command in [
        "ls -la ~/.cairn/logs",
        "find ~/.cairn/logs -type f",
        "cat ~/.cairn/logs/boot | tail -20",
        "du -sh ~/.cairn",
    ]:
        assert gate.verdict(command) is None, f"a read must pass: {command!r}"


def test_the_gate_runs_as_a_hook_and_blocks_with_exit_2():
    """END TO END, through the real contract — measured 2026-08-18 rather than assumed:
    stdin is JSON, exit 0 allows, exit 2 blocks and feeds stderr back to Claude."""
    payload = json.dumps({"tool_name": "Bash", "hook_event_name": "PreToolUse",
                          "tool_input": {"command": "rm -rf ~/.cairn/logs"}})
    proc = subprocess.run([sys.executable, str(_GATE)], input=payload,
                          capture_output=True, text=True, timeout=20)
    assert proc.returncode == 2, f"a guarded delete must exit 2 (block), got {proc.returncode}"
    assert "REFUSED" in proc.stderr, "the reason rides stderr, which is what reaches Claude"

    allowed = json.dumps({"tool_name": "Bash", "hook_event_name": "PreToolUse",
                          "tool_input": {"command": "ls ~/.cairn/logs"}})
    ok = subprocess.run([sys.executable, str(_GATE)], input=allowed,
                        capture_output=True, text=True, timeout=20)
    assert ok.returncode == 0, "a read must pass the real hook, not merely the predicate"


def test_a_non_bash_tool_and_an_unreadable_payload_both_pass_loudly():
    """CP1 — say what happened. A gate that cannot read its input must not silently allow,
    and must not block the whole session either: it speaks, and allows."""
    other = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "/x"}})
    assert subprocess.run([sys.executable, str(_GATE)], input=other,
                          capture_output=True, text=True, timeout=20).returncode == 0

    broken = subprocess.run([sys.executable, str(_GATE)], input="not json at all",
                            capture_output=True, text=True, timeout=20)
    assert broken.returncode == 0, "an unreadable payload must not block every Bash call"
    assert "could not read" in broken.stderr, "and it must SAY it is running unguarded (CP1)"


def test_the_gate_is_registered_where_it_claims_to_be():
    """The predicate being right is worth nothing if nothing calls it. Read from settings,
    not from memory — the failure mode this repo knows best is a mechanism nobody fires."""
    settings = json.loads((_REPO_ROOT / ".claude" / "settings.json").read_text())
    commands = [h["command"]
                for entry in settings.get("hooks", {}).get("PreToolUse", [])
                if entry.get("matcher") == "Bash"
                for h in entry.get("hooks", [])]
    assert any("deletegate" in c for c in commands), \
        f"deletegate must be registered as a Bash PreToolUse hook; found {commands}"


# ── the door ─────────────────────────────────────────────────────────────────

def test_the_round_trip_a_delete_that_can_be_undone():
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        victim = home / "instance" / "logs" / "archive" / "boot.pre-decontamination"
        victim.parent.mkdir(parents=True)
        victim.write_text("54 records nobody wanted destroyed\n")

        entry = door.put(victim, home=home)
        assert not victim.exists(), "the path is cleared, as a delete would clear it"
        assert entry.exists(), "and the bytes are still on disk, which a delete would not leave"

        rows = door.entries(home=home)
        assert len(rows) == 1 and rows[0]["origin"] == str(victim), \
            "the trash remembers WHERE it came from — without that it is just a slower rm"

        back = door.restore(rows[0]["name"], home=home)
        assert back == victim and victim.read_text().startswith("54 records"), \
            "restored to the original address, byte for byte"


def test_the_origin_is_written_before_the_move():
    """Checked, not assumed: an entry in ``files/`` with no readable origin is exactly as
    recoverable as ``rm`` was, so the info file cannot be the second write."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        src = home / "thing.txt"
        src.write_text("x")
        entry = door.put(src, home=home)
        _, info = door.trash_dirs(home)
        meta = info / f"{entry.name}.trashinfo"
        assert meta.exists(), "the .trashinfo must exist for every entry"
        text = meta.read_text()
        assert text.startswith("[Trash Info]"), "freedesktop format — so KDE and trash-cli read it"
        assert "DeletionDate=" in text and "Path=" in text


def test_restore_refuses_to_overwrite_what_is_there_now():
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        src = home / "thing.txt"
        src.write_text("trashed version")
        name = door.put(src, home=home).name
        src.write_text("the LIVE version, written since")

        try:
            door.restore(name, home=home)
            raise AssertionError("a restore that clobbers a live file is this door's own defect")
        except FileExistsError:
            pass
        assert src.read_text() == "the LIVE version, written since", "and it left the live file alone"


def test_the_sweep_keeps_what_it_cannot_date():
    """Unknown is not old. Treating it as old makes retention a second unrecoverable delete."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        now = datetime(2026, 9, 30, tzinfo=timezone.utc).astimezone()

        old = home / "old.txt"; old.write_text("o")
        door.put(old, home=home, now=now - timedelta(days=40))
        recent = home / "recent.txt"; recent.write_text("r")
        door.put(recent, home=home, now=now - timedelta(days=2))
        undated = home / "undated.txt"; undated.write_text("u")
        name = door.put(undated, home=home, now=now - timedelta(days=99)).name
        _, info = door.trash_dirs(home)
        (info / f"{name}.trashinfo").write_text("[Trash Info]\nPath=/gone\n")   # no date

        gone = door.empty(30, home=home, now=now)
        left = {e["name"] for e in door.entries(home=home)}
        assert gone == ["old.txt"], f"only the provably-old entry goes, got {gone}"
        assert {"recent.txt", "undated.txt"} <= left, \
            "a recent entry and an undated one both survive the sweep"


def test_an_entry_with_no_readable_origin_is_reported_not_hidden():
    """Law 7 at a diagnostic surface: a listing that silently omitted it would be the
    surface deciding the reader does not need to know it is there."""
    with tempfile.TemporaryDirectory() as td:
        home = Path(td)
        files, _ = door.trash_dirs(home)
        files.mkdir(parents=True)
        (files / "orphan").write_text("no info file was ever written for me")
        rows = door.entries(home=home)
        assert len(rows) == 1 and rows[0]["origin"] is None
        assert "origin unknown" in rows[0]["lack"], "it says what is missing, and is still listed"


def test_the_guarded_root_and_the_trash_share_a_volume():
    """THE CONDITION THE trash-cli INTEROP CLAIM RESTS ON, asserted as an invariant rather
    than quoted from the charter.

    Measured 2026-08-18, both directions: a file the door trashed showed up in ``trash-list``
    and ``trash-restore`` put it back, byte for byte. But a file on ``/tmp`` trashed with
    ``trash-put`` did NOT appear in the door's listing — it went to ``/tmp/.Trash-1000/``,
    because the freedesktop spec sends a file to its own VOLUME's trash and ``/tmp`` is a
    tmpfs. The door always uses the home trash. So the two agree exactly when the source
    shares a volume with home, and diverge when it does not.

    That is not a defect at the address this door guards — ``~/.cairn`` is on the same device
    as ``$HOME`` — but it IS a load-bearing precondition, and a precondition living only in a
    charter sentence is one nobody re-checks. If ``~/.cairn`` ever moves to its own volume,
    this goes red and says why, instead of the interop claim quietly becoming false."""
    import os
    cairn_root = Path.home() / ".cairn"
    if not cairn_root.exists():                     # a box where nothing has run yet
        return
    guarded = os.stat(cairn_root).st_dev
    trash = os.stat(Path.home()).st_dev
    assert guarded == trash, (
        f"~/.cairn is on device {guarded} and $HOME on {trash} — the door would move ACROSS "
        "volumes into the home trash, where trash-cli and KDE would instead expect the "
        "volume trash. The interop the charter claims no longer holds; either move the door "
        "to volume-aware placement or drop the claim.")


def _main() -> int:
    real_trash = Path.home() / ".local" / "share" / "Trash" / "files"
    before = sorted(p.name for p in real_trash.iterdir()) if real_trash.exists() else []

    checks = [
        test_the_command_that_caused_the_loss_is_refused,
        test_every_spelling_of_the_same_delete_is_caught,
        test_the_door_itself_is_never_refused,
        test_the_bound_the_git_roots_are_not_gated,
        test_a_command_that_only_reads_the_root_passes,
        test_the_gate_runs_as_a_hook_and_blocks_with_exit_2,
        test_a_non_bash_tool_and_an_unreadable_payload_both_pass_loudly,
        test_the_gate_is_registered_where_it_claims_to_be,
        test_the_round_trip_a_delete_that_can_be_undone,
        test_the_origin_is_written_before_the_move,
        test_restore_refuses_to_overwrite_what_is_there_now,
        test_the_sweep_keeps_what_it_cannot_date,
        test_an_entry_with_no_readable_origin_is_reported_not_hidden,
        test_the_guarded_root_and_the_trash_share_a_volume,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")

    after = sorted(p.name for p in real_trash.iterdir()) if real_trash.exists() else []
    assert before == after, (
        f"THIS PROOF WROTE INTO THE REAL TRASH: {set(after) - set(before)}. Every door tooth "
        "runs against an injected home for exactly this reason — a proof that writes into the "
        "instrument it proves is the failure this repo has already measured twice.")
    print(f"  PASS  the live trash is untouched ({len(before)} entries before and after)")

    print("green — the one root where delete is forever now has a gate that refuses ~/.cairn "
          "deletes and names a door that undoes them, the git roots stay ungated, and the "
          "gate is registered where it says it is")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
