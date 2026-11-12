"""Proof for system_word — a system word folds, free text never does, and every door agrees.

Ticket e3cf75c6dc8f (system-words-fold-case-when-akien-types-them), ruled 2026-09-07:
*"everywhere we're talking a status word, or a command word, or any similar 'system word' it
should be case insensitive if there's any chance of it coming from me."*

Teeth a hollow build could not pass — three families:

  - UNIT. ``fold``/``is_word``/``canon``/``pick``/``fold_head``/``fold_flags`` return exactly
    what their docstrings say; a non-string never raises; ``fold_head`` leaves everything
    past ``n`` as the SAME OBJECT; ``fold_flags`` leaves a positional path alone.
  - BEHAVIOURAL, DRIVEN NOT READ. Each entry point in the census is DRIVEN with its system
    words uppercased and must behave as its lowercase form — the real ``bin/cairn`` by
    subprocess on both dispatch paths, the codemother launcher, and every python main by
    import. A grep for a call to ``fold`` would pass a seam that calls it and then compares
    the unfolded token anyway; only driving the door finds that.
  - WRONG INTENT. Free text after the folded verbs reaches its consumer BYTE-IDENTICAL, at the
    dispatcher and at the review door; the stored ``workflow_and_state`` of a ticket never
    changes case because a compare folded. Clause 7 (the lowercase marker at the ruling
    intake) retired with the intake's code (ticket 640a7a48e1c5, outline Q#43).

Run bare against the tree BEFORE the seams move, the behavioural teeth are red and the unit
teeth green — that ordering is recorded in the ticket's history as the proof's own proof.

    python3 cairn/tools/system_word/proofs/test_system_word.py     # exit 0 = green
"""

from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# THE SUBJECT IS BOUND AT CALL TIME, NOT AT IMPORT. A proof that binds its subject at
# import prints NO teeth when the subject is missing — the hollow reading calls that UNRAN
# and cannot tell it from a proof that never ran (ticket c5b6b128a376). So an absent module
# binds stand-ins that red every tooth leaning on it, by name, and the rest still print.
try:
    from cairn.tools.system_word import canon, fold, fold_flags, fold_head, is_word, pick  # noqa: E402
except ImportError as _exc:  # noqa: E402
    _SUBJECT_ABSENT = f"cairn.tools.system_word is not importable: {_exc}"

    def _missing(*_args, **_kwargs):
        raise AssertionError(_SUBJECT_ABSENT)

    canon = fold = fold_flags = fold_head = is_word = pick = _missing

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402

_DISPATCHER = _REPO_ROOT / "bin" / "cairn"

# Ticket e3cf75c6dc8f's falsifier numbers nine clauses; each names the one tooth that
# drives it (proof_coverage reads this out of the AST — memory: proves-keys-follow-the-
# falsifier-markers). Clause (1) names two paths; the device path is the deeper one.
PROVES = {
    "e3cf75c6dc8f": {
        "1": "test_the_real_harbor_master_takes_uppercase_show_map_open",
        "2": "test_operator_inbox_takes_uppercase_show_artifact_and_summary_flag",
        "3": "test_skill_block_takes_uppercase_contract_and_folds_the_review_prefix",
        # clause 4 (the learning block's approve/disprove verb) retired with that verb,
        # ticket e5a8e8059296 (outline 5.10.8); the fold it measured stands in clause 3's review tooth.
        "5": "test_ground_loop_takes_uppercase_help_and_status_word",
        "6": "test_base_device_show_and_shim_verb_fold",
        "9": "test_bin_cairn_the_file_and_cairn_the_command_are_untouched",
        # The build touched more files than the nine clauses name; each of those is a
        # writes_to the hollow reading reverts, and each names the tooth that reds when it
        # is. proof_coverage.lacks reads only the clause keys; hollow.py reads every value.
        "orient_chart_librarian": "test_orient_chart_and_librarian_take_uppercase_verbs",
        "sudo_relay": "test_sudo_relay_takes_uppercase_status_flag",
        "harbor_master_filter": "test_the_real_harbor_master_takes_uppercase_show_map_open",
        "stage_targets": "test_stage_targets_fold_at_render_and_resolve",
        "codemother_launcher": "test_the_codemother_launcher_folds_its_subcommand",
        "dispatcher_legacy": "test_dispatcher_folds_the_legacy_verb_and_passes_args_verbatim",
        "dispatcher_device": "test_dispatcher_folds_the_device_and_verb_tokens_on_the_device_path",
        "charters": "test_the_three_charters_say_the_words_fold",
        "probe": "test_the_probe_is_armed_and_reads_no_bite_on_the_live_tree",
    },
}
_CODEMOTHER = _REPO_ROOT / "cairn" / "devices" / "codemother" / "0" / "bin" / "codemother"


# ── unit teeth ─────────────────────────────────────────────────────────────────

def test_fold_strips_and_casefolds_and_never_raises():
    assert fold("  RuLeD ") == "ruled"
    assert fold("SHOW") == "show"
    assert fold(7) == "7", "a non-string folds through str(), it does not raise"
    assert fold(None) == "none"
    assert fold("Straße") == fold("STRASSE"), "casefold, not lower"


def test_is_word_compares_as_system_words():
    assert is_word("SHOW", "show", "get") is True
    assert is_word(" get ", "show", "get") is True
    assert is_word("shown", "show", "get") is False
    assert is_word("", "show") is False


def test_canon_returns_the_tables_own_spelling():
    assert canon("MAP", {"map": 1, "fleet": 2}) == "map"
    assert canon("Fleet", ["map", "fleet"]) == "fleet"
    assert canon("nope", {"map": 1}) is None
    assert canon("BUILDME", ("THINKME", "BUILDME")) == "BUILDME", (
        "the table's spelling comes back, whatever case the table keeps")


def test_pick_is_a_folded_lookup():
    f = object()
    assert pick("MAP", {"map": f}) is f
    assert pick("nope", {"map": f}) is None
    assert pick("Map ", {"map": f}) is f


def test_fold_flags_folds_only_dash_tokens():
    assert fold_flags(["--SEAL", "Proofs/X.py"]) == ["--seal", "Proofs/X.py"]
    assert fold_flags(["-Q", "-", "His Words"]) == ["-q", "-", "His Words"]
    assert fold_flags([]) == []


def test_fold_head_folds_n_and_passes_the_rest_as_the_same_objects():
    words = "His Words, Verbatim — Every Byte"
    out = fold_head(["Review", "ABC", words], 2)
    assert out == ["review", "abc", words]
    assert out[2] is words, "beyond n the very object rides through, not a copy"
    assert fold_head(["X"], 5) == ["x"], "n past the end folds what exists"
    assert fold_head(["X", "Y"], 0) == ["X", "Y"], "n=0 folds nothing"


# ── bash seams, driven by subprocess ───────────────────────────────────────────

def _stub(dir_: str, name: str, body: str) -> None:
    path = os.path.join(dir_, name)
    with open(path, "w") as f:
        f.write("#!/usr/bin/env bash\n" + body + "\n")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _cairn(*args: str, **env: str) -> subprocess.CompletedProcess:
    return subprocess.run([*bash_script_argv(_DISPATCHER), *args], capture_output=True, text=True,
                          env={**os.environ, **env}, timeout=60)


def test_bin_cairn_the_file_and_cairn_the_command_are_untouched():
    """Clause (9): the folding landed INSIDE the dispatcher — the file is still bin/cairn,
    still executable, and ``cairn`` on PATH is that same file, not a wrapper beside it."""
    assert _DISPATCHER.is_file() and os.access(_DISPATCHER, os.X_OK), _DISPATCHER
    assert _DISPATCHER.name == "cairn" and _DISPATCHER.parent.name == "bin"
    found = subprocess.run(["bash", "-lc", "command -v cairn"], capture_output=True, text=True,
                           timeout=30).stdout.strip()
    # the name and the berth, not the inode: a hollow worktree's PATH still points at the
    # live checkout, and the clause is about what the command is CALLED and where it sits
    on_path = Path(found).resolve() if found else None
    assert on_path is not None and on_path.name == "cairn" and on_path.parent.name == "bin", (
        f"the command on PATH must still be a bin/cairn: {found!r}")
    head = _DISPATCHER.read_text(encoding="utf-8").splitlines()[0]
    assert head.startswith("#!"), f"still a script with a shebang, not a compiled stand-in: {head!r}"


def test_dispatcher_folds_the_legacy_verb_and_passes_args_verbatim():
    with tempfile.TemporaryDirectory() as d:
        _stub(d, "echoer", 'for a in "$@"; do echo "arg:$a"; done')
        r = _cairn("ECHOER", "a", "B c", "--Flag", CAIRN_CMD_DIR=d)
        assert r.returncode == 0, f"uppercase legacy verb refused: {r.stderr!r}"
        assert r.stdout.splitlines() == ["arg:a", "arg:B c", "arg:--Flag"], (
            f"args after the verb must ride verbatim: {r.stdout!r}")


def test_dispatcher_folds_the_device_and_verb_tokens_on_the_device_path():
    with tempfile.TemporaryDirectory() as d:
        bin_dir = os.path.join(d, "fx_dev", "0", "bin")
        os.makedirs(bin_dir)
        _stub(bin_dir, "show", 'echo "show:$*"')
        _stub(bin_dir, "fx_dev", 'echo "self:$*"')
        r = _cairn("FX_DEV", "Show", "Map", "Open", CAIRN_INSTANCE_ROOT=d)
        assert r.returncode == 0, f"uppercase device/verb refused: {r.stderr!r}"
        assert r.stdout == "show:Map Open\n", (
            f"the verb resolves folded, the rest rides verbatim: {r.stdout!r}")
        # a non-verb first word goes onto the bus (script-else-bus, Q#27, ticket 41a70e789682):
        # a stub mouth stands in for bus_client and records what it was handed
        _stub(d, "mouth", f'printf "%s\\n" "$@" > "{d}/mouth.argv"')
        r2 = _cairn("Fx_Dev", "Not-A-Verb", "x", CAIRN_INSTANCE_ROOT=d,
                    CAIRN_BUS_MOUTH=os.path.join(d, "mouth"))
        said = open(os.path.join(d, "mouth.argv")).read().splitlines() \
            if os.path.exists(os.path.join(d, "mouth.argv")) else None
        assert said == ["fx_dev", "Not-A-Verb", "x"] and "self:" not in r2.stdout, (
            f"a non-verb first arg goes to the bus mouth, the device folded and the rest "
            f"verbatim: said={said!r} out={r2.stdout!r} err={r2.stderr[-300:]!r}")


def test_the_real_harbor_master_takes_uppercase_show_map_open():
    lo = _cairn("harbor_master", "show", "map", "open")
    up = _cairn("HARBOR_MASTER", "Show", "MAP", "Open")
    assert lo.returncode == up.returncode == 0, (up.stderr, lo.stderr)
    strip = lambda s: "\n".join(l for l in s.splitlines() if not l.startswith("Cached at:"))
    assert strip(up.stdout) == strip(lo.stdout), "the same view, whichever case he typed"


def test_the_codemother_launcher_folds_its_subcommand():
    r = subprocess.run([*bash_script_argv(_CODEMOTHER), "NO-SUCH-SUBCOMMAND-XYZ"],
                       capture_output=True, text=True, timeout=60)
    lo = subprocess.run([*bash_script_argv(_CODEMOTHER), "no-such-subcommand-xyz"],
                        capture_output=True, text=True, timeout=60)
    assert r.returncode == lo.returncode and r.stdout == lo.stdout, (r.stderr, lo.stderr)
    # show is a script in codemother's bin since ticket ed3d02b24675, reached through the
    # dispatcher (script-else-bus, ticket 41a70e789682), so the uppercase SHOW rides bin/cairn
    r = _cairn("codemother", "SHOW", "NOT-A-VIEW")
    # The show branch hands an unknown view to the base resolver (ticket b41b0c0fff0e), whose
    # refusal names the view it was given, folded, and the views that exist — the default arm
    # prints help and never says "no view".
    assert r.returncode == 2 and "no view 'not-a-view'" in r.stderr, (
        f"an uppercase SHOW must reach the show branch (the resolver's refusal), not the default: "
        f"rc={r.returncode} {r.stderr!r} {r.stdout[:80]!r}")


# ── python seams, driven by main() ─────────────────────────────────────────────

def _drive(fn, argv, **env):
    out, err = io.StringIO(), io.StringIO()
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = fn(argv)
            except SystemExit as exc:
                rc = exc.code
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return rc, out.getvalue(), err.getvalue()


def _same(fn, lower, upper, **env):
    lo = _drive(fn, lower, **env)
    up = _drive(fn, upper, **env)
    assert up[0] == lo[0], f"{upper!r} exited {up[0]} where {lower!r} exited {lo[0]}: {up[2]!r}"
    assert up[1] == lo[1], f"{upper!r} printed differently from {lower!r}:\n{up[1]!r}\n{lo[1]!r}"
    return lo, up


def test_ground_loop_takes_uppercase_help_and_status_word():
    """THE COMMAND HE TYPES: the ground loop is the cairn device's, so it is driven as
    `cairn groundloop`, never by importing its cli (RULE 1)."""
    lo, up = _cairn("groundloop", "--help"), _cairn("groundloop", "--HELP")
    assert lo.returncode == up.returncode == 0 and up.stdout == lo.stdout, (up.stderr, lo.stderr)
    lo, up = _cairn("groundloop", "status"), _cairn("groundloop", "STATUS")
    assert up.returncode == lo.returncode and "unknown command" not in up.stderr, (
        f"STATUS must reach the status command: {up.stderr!r}")
    assert up.stdout.splitlines()[:1] == lo.stdout.splitlines()[:1], (up.stdout, lo.stdout)
    r = _cairn("groundloop", "NO-SUCH-XYZ")
    assert r.returncode == 1 and "no-such-xyz" in r.stderr, (
        f"an unknown command is refused with the FOLDED word: {r.stderr!r}")


def test_operator_inbox_takes_uppercase_show_artifact_and_summary_flag():
    from cairn.tools.operator_inbox.inbox import main
    # ``show artifact`` with no id is a usage refusal (rc 2 + the artifact usage line) —
    # reached only if both tokens folded; an unfolded 'ARTIFACT' is 'unknown target'.
    rc, out, err = _drive(main, ["SHOW", "ARTIFACT"])
    assert rc == 2 and "show artifact <id-prefix>" in err, (err, out)
    rc, out, err = _drive(main, ["SHOW", "INBOX", "--SUMMARY"])
    assert rc == 0, err
    lo = _drive(main, ["show", "inbox", "--summary"])
    assert out.splitlines()[:3] == lo[1].splitlines()[:3], "the summary view, either case"


class _ScratchBerths:
    """skill_block's berth root and reviewed log are module constants read from the
    environment at import; a proof that imported the module earlier cannot re-point them
    by env, so it re-points the constants themselves for the duration of one tooth."""

    def __init__(self, d: str):
        from cairn.machines.skill_block import skill_block as sb
        self.sb, self.d = sb, d
        self.saved = (sb._BERTHS, sb._REVIEWED_LOG)

    def __enter__(self):
        self.sb._BERTHS = Path(self.d) / "berths"
        self.sb._REVIEWED_LOG = Path(self.d) / "reviewed.jsonl"
        return self

    def __exit__(self, *exc):
        self.sb._BERTHS, self.sb._REVIEWED_LOG = self.saved

    def berth(self, skill: str, finding_id: str) -> None:
        p = self.sb._BERTHS / skill
        p.mkdir(parents=True, exist_ok=True)
        (p / f"{finding_id}.json").write_text(json.dumps({
            "finding_id": finding_id, "skill": skill, "title": "fixture",
            "when": "2026-09-07T00:00:00", "exit": "routed_forward", "bullets": []}))


def test_skill_block_takes_uppercase_contract_and_folds_the_review_prefix():
    from cairn.machines.skill_block.__main__ import main
    _same(main, ["contract", "sorted"], ["CONTRACT", "Sorted"])
    with tempfile.TemporaryDirectory() as d, _ScratchBerths(d) as sc:
        sc.berth("sorted", "abc123ff00")
        rc, out, err = _drive(main, ["REVIEW", "ABC123", "his words"])
        assert rc == 0 and "reviewed: abc123ff00" in out, (
            f"an uppercase id prefix must resolve the lowercase berth: rc={rc} {err!r}")


def test_orient_chart_and_librarian_take_uppercase_verbs():
    from cairn.tools.orient import orient
    # the imports verb answers from one file; the git verb reads the commons beside the
    # repo, which a hollow worktree does not have (memory: hollow-worktree-has-no-commons-beside)
    lo, up = _same(orient._main, ["imports", __file__], ["IMPORTS", __file__])
    assert lo[0] == 0 and json.loads(up[1])

    from skills.chart import live as chart_live
    calls = []
    orig = chart_live._chain
    chart_live._chain = lambda rest: calls.append(rest) or 0
    try:
        rc, *_ = _drive(chart_live._main, ["CHAIN", "e3cf75c6dc8f"])
    finally:
        chart_live._chain = orig
    assert rc == 0 and calls == [["e3cf75c6dc8f"]], (
        "the folded verb reaches its branch and the rest rides verbatim")
    # The librarian's verbs are measured by the librarian (ticket c29a2d0dcebb, RULE 1).


def test_sudo_relay_takes_uppercase_status_flag():
    """Driven as `cairn sudorelay`, never by import (RULE 1). An unknown argument refuses
    with exit 2 and acquires nothing (ticket 8902708b6212), so --STATUS answering as --status
    does is the fold reaching the status branch."""
    lo, up = _cairn("sudorelay", "--status"), _cairn("sudorelay", "--STATUS")
    assert up.returncode == lo.returncode and up.returncode != 2, (up.returncode, up.stderr)
    assert up.stdout == lo.stdout and up.stderr == lo.stderr, (up, lo)


def test_base_device_show_and_shim_verb_fold():
    from cairn.tools.base.device import BaseDevice
    from cairn.tools.base.shim import BaseShim

    class _Fx(BaseDevice):
        device_id = "fx"

        def intention(self):
            return {}

        def state(self):
            return {}

        def settings(self):
            return {}

        def declared_views(self):
            return {"map": lambda: {"boats": 1}}

    dev = _Fx.__new__(_Fx)
    got = BaseDevice._handle_show(dev, {"body": {"what": "MAP"}})
    assert got.get("accepted") is True, got
    assert got["view"] == "map", "the view is echoed in the SYSTEM's spelling"
    got = BaseDevice._handle_get(dev, {"body": {"what": " Map "}})
    assert got.get("accepted") is True and got["data"] == {"boats": 1}, got

    class _VerbDevice:
        def __init__(self):
            self.handled = []

        def declared_verbs(self):
            return {"ping": self._ping}

        def _ping(self, envelope):
            self.handled.append(envelope)
            return "pong"

    class _Bus:
        def __init__(self):
            self.posted = []

        def post(self, **envelope):
            self.posted.append(envelope)
            return envelope

        def wire_delivery(self, *_):
            pass

        def read(self, **_):
            return []

    class _Shim(BaseShim):
        def __init__(self, bus=None):
            super().__init__(bus=bus)
            self._vd = _VerbDevice()
            self.set_diagnostic_receiver(None)

        @property
        def device_id(self):
            return "verb_device"

        def _start_device(self):
            return self._vd

    bus = _Bus()
    shim = _Shim(bus=bus)
    result = shim.deliver({"id": "e1", "sender": "akien", "addressee": "verb_device",
                           "verb": "PING", "body": {}})
    assert result == "pong", f"an uppercase verb must dispatch, not bounce: {result!r}"
    assert bus.posted == [], "nothing bounced"


def test_stage_targets_fold_at_render_and_resolve():
    from cairn.tools.base.transitions import Workflow, render, resolve_target
    path = ("THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED")
    wf = Workflow(node_class="code-seam", version="v2", path=path, cursor=1,
                  objects=tuple(None for _ in path))
    assert resolve_target(wf, "proveme") == 3
    s = render(wf, "buildme")
    assert "[BUILDME" in s and "[buildme" not in s, (
        f"the stored string keeps the SYSTEM's case; folding is a compare: {s}")


# ── the records the build wrote: charters, the clearance rung, the probe ──────

def test_the_three_charters_say_the_words_fold():
    """The build wrote three charters: system_word's own (new), bin's (the dispatcher folds
    its two tokens) and the ruling intake's (the marker folds). Two stand: the third left with
    the intake's code (ticket 640a7a48e1c5). A charter is a record of the design; a reverted one
    describes a dispatcher that compares bytes."""
    own = json.loads((_REPO_ROOT / "cairn/tools/system_word/intention+why.json").read_text("utf-8"))
    assert own["component"] == "system_word" and own["runtime_role"] == "tool", own.keys()
    assert own.get("gated_by") and own.get("falsifier"), "a charter carries its gate and its falsifier"
    bin_ = json.loads((_REPO_ROOT / "bin/intention+why.json").read_text("utf-8"))
    assert "the dispatcher folds the two tokens it resolves" in bin_["what"], (
        "bin's charter must say the dispatcher folds, since 2026-09-07")


def test_the_probe_is_armed_and_reads_no_bite_on_the_live_tree():
    """WATCHME(system-words-fold): the probe berths beside what it watches, is a frozen
    Probe with carry and enough, and its survey over the LIVE tree counts zero bites — an
    invariant, never a snapshot. Patience and enough are read against a fixture context."""
    from cairn.tools.base.probe import Probe
    from cairn.tools.system_word.probes import his_case_never_bites as probe
    assert isinstance(probe.PROBE, Probe) and probe.PROBE.to == "codemother"
    assert callable(probe.PROBE.carry) and callable(probe.PROBE.enough)
    s = probe.survey()
    assert s["entry_points"] == 8 and s["bites"] == 0 and s["bit"] == [], (
        "the probe drives its eight cheap entry points and none bites "
        "(two ruling drives left with the intake, ticket 640a7a48e1c5)")
    ctx = {"survey": s}
    assert probe.PROBE.trigger(None, ctx) is False, "no bite, no poke"
    assert probe.PROBE.enough(ctx) is False, "one clean survey is not fourteen"
    assert probe.PROBE.enough({"survey": s, "clean_streak": 14}) is True
    bitten = {"survey": {"entry_points": 1, "bites": 1, "bit": ["fx"]}, "previous_bites": ["fx"]}
    assert probe.PROBE.trigger(None, bitten) is True, "a bite seen twice pokes"
    carry = probe.PROBE.carry(bitten)
    assert carry["bit"] == ["fx"] and "clause (3)" in carry["against_falsifier"], carry


# ── wrong intent ───────────────────────────────────────────────

def test_wrong_intent_free_text_lands_byte_identical():
    """The review words, and everything the dispatcher hands past
    the verb are HIS BYTES. Any fold here is the wrong intent, ruled out in the ticket."""
    words = "Approve — THIS is Fine, Ship It ß"
    with tempfile.TemporaryDirectory() as d:
        _stub(d, "echoer", 'printf "%s\\n" "$@"')
        r = _cairn("Echoer", words, "Second ARG", CAIRN_CMD_DIR=d)
        assert r.stdout == f"{words}\nSecond ARG\n", r.stdout
    from cairn.machines.skill_block.__main__ import main as sb_main
    with tempfile.TemporaryDirectory() as d, _ScratchBerths(d) as sc:
        sc.berth("intent", "feed00")
        rc, out, err = _drive(sb_main, ["Review", "FEED", words])
        assert rc == 0, err
        recs = [json.loads(l) for l in sc.sb._REVIEWED_LOG.read_text().splitlines() if l]
        assert recs and recs[-1]["words"] == words, (
            f"his review words landed changed: {recs[-1]['words']!r}")
    assert fold_head(["review", "FEED", words], 2)[2] is words


def test_wrong_intent_a_stored_ticket_string_keeps_its_case():
    ticket = _REPO_ROOT.parent / "CairnCommons" / "tickets" / \
        "e3cf75c6dc8f-system-words-fold-case-when-akien-types-them.json"
    if not ticket.is_file():
        return
    from cairn.tools.base.ticket_file import read_ticket  # 284798998ab0: plan + state
    wf = read_ticket(ticket)["workflow_and_state"]
    assert wf.startswith("code-seam@v2: THINKME ->"), wf
    assert "buildme" not in wf and "proveme" not in wf, (
        "stage tokens on disk stay in the system's uppercase; nothing rewrote them")


def _main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — a proof reports every red (Law 7)
            failed += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
