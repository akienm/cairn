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
    changes case because a compare folded. The lowercase ``ruled`` marker confirms and
    ``RULEDX`` still does not.

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

from cairn.tools.system_word import canon, fold, fold_flags, fold_head, is_word, pick  # noqa: E402

_DISPATCHER = _REPO_ROOT / "bin" / "cairn"
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
    return subprocess.run([str(_DISPATCHER), *args], capture_output=True, text=True,
                          env={**os.environ, **env}, timeout=60)


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
        r2 = _cairn("Fx_Dev", "Not-A-Verb", "x", CAIRN_INSTANCE_ROOT=d)
        assert r2.stdout == "self:Not-A-Verb x\n", (
            f"a non-verb first arg goes to the self-named launcher verbatim: {r2.stdout!r}")


def test_the_real_harbor_master_takes_uppercase_show_map_open():
    lo = _cairn("harbor_master", "show", "map", "open")
    up = _cairn("HARBOR_MASTER", "Show", "MAP", "Open")
    assert lo.returncode == up.returncode == 0, (up.stderr, lo.stderr)
    strip = lambda s: "\n".join(l for l in s.splitlines() if not l.startswith("Cached at:"))
    assert strip(up.stdout) == strip(lo.stdout), "the same view, whichever case he typed"


def test_the_real_ruling_list_takes_uppercase():
    lo = _cairn("ruling", "list")
    up = _cairn("RULING", "LIST")
    assert up.returncode == lo.returncode, (up.stderr, lo.stderr)
    assert up.stdout == lo.stdout


def test_the_codemother_launcher_folds_its_subcommand():
    r = subprocess.run([str(_CODEMOTHER), "NO-SUCH-SUBCOMMAND-XYZ"],
                       capture_output=True, text=True, timeout=60)
    lo = subprocess.run([str(_CODEMOTHER), "no-such-subcommand-xyz"],
                        capture_output=True, text=True, timeout=60)
    assert r.returncode == lo.returncode and r.stdout == lo.stdout, (r.stderr, lo.stderr)
    r = subprocess.run([str(_CODEMOTHER), "SHOW", "NOT-A-VIEW"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 1 and "usage: cairn codemother show" in r.stderr, (
        f"an uppercase SHOW must reach the show branch (its own usage), not the default: "
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
    from cairn.devices.cairn.machines.ground_loop.cli import main
    _same(main, ["help"], ["HELP"])
    rc, out, err = _drive(main, ["NO-SUCH-XYZ"])
    assert rc == 1 and "no-such-xyz" in err, (
        f"an unknown command is refused with the FOLDED word: {err!r}")


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


def test_learning_block_takes_uppercase_recordverdict_and_signal():
    from cairn.machines.learning_block.__main__ import main
    with tempfile.TemporaryDirectory() as d:
        env = {"CAIRN_LB_TRACE_ROOT": os.path.join(d, "traces"),
               "CAIRN_ROOTS_PARENT": d}
        _same(main, ["recordverdict"], ["RECORDVERDICT"], **env)
        # bare 'approve' with an explicit uppercase signal and words: nothing pending, so the
        # refusal must be about the TARGET/berth, never 'no signal' — proof the signal folded.
        rc, out, err = _drive(main, ["RECORDVERDICT", "APPROVE", "these are his words"], **env)
        assert rc == 2 and "no signal" not in err, err
        _same(main, ["dial", "sorted"], ["DIAL", "sorted"], **env)


def test_orient_chart_and_librarian_take_uppercase_verbs():
    from cairn.tools.orient import orient
    lo, up = _same(orient._main, ["git"], ["GIT"])
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

    from cairn.devices.librarian import live as lib_live
    calls = []
    orig = lib_live._loop
    lib_live._loop = lambda rest: calls.append(rest) or 0
    try:
        rc, *_ = _drive(lib_live._main, ["LOOP", "Once"])
    finally:
        lib_live._loop = orig
    assert rc == 0 and calls == [["Once"]]


def test_sudo_relay_takes_uppercase_status_flag():
    from cairn.devices.sudo_relay import daemon
    hits = []
    orig = daemon._print_status
    daemon._print_status = lambda: hits.append(1) or 0
    try:
        rc, *_ = _drive(daemon.main, ["--STATUS"])
    finally:
        daemon._print_status = orig
    assert rc == 0 and hits == [1], "--STATUS must reach the status branch, not run() the daemon"


def test_tester_cli_takes_uppercase_flags():
    from cairn.devices.tester.cli import main
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = _drive(main, ["--SEAL", "-Q", d])
    assert rc == 2 and "found no proofs" in err, (
        f"the flags parse folded and the run reaches discovery: rc={rc} {err!r}")


def test_ruling_cli_takes_uppercase_list():
    from cairn.machines.ruling.cli import main
    _same(main, ["list"], ["LIST"])


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


def test_harbor_master_filter_folds_open():
    from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
    fleet = {"open": [{"label": "PROVED", "id": "a"}, {"label": "BUILDME", "id": "b"}],
             "in_port": [], "findings": []}
    lo = HarborMasterDevice._filter_fleet(fleet, "open")
    up = HarborMasterDevice._filter_fleet(fleet, "OPEN")
    assert up == lo and [b["id"] for b in up["open"]] == ["b"], up


def test_stage_targets_fold_at_render_and_resolve():
    from cairn.tools.base.transitions import Workflow, render, resolve_target
    path = ("THINKME", "TICKETME", "BUILDME", "PROVEME", "PROVED")
    wf = Workflow(node_class="code-seam", version="v2", path=path, cursor=1,
                  objects=tuple(None for _ in path))
    assert resolve_target(wf, "proveme") == 3
    s = render(wf, "buildme")
    assert "[BUILDME" in s and "[buildme" not in s, (
        f"the stored string keeps the SYSTEM's case; folding is a compare: {s}")


# ── the marker, and wrong intent ───────────────────────────────────────────────

def test_lowercase_ruled_confirms_at_intake_and_ruledx_does_not():
    from cairn.machines.ruling import ruling
    hits = ruling.scan_for_ruling_markers("he ruled that the file dies", strong_only=True)
    assert any(h["match"].lower() == "ruled" for h in hits), hits
    assert not ruling.scan_for_ruling_markers("RULEDX is not the marker", strong_only=True)
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "CairnCommons", "decisions"))
        os.makedirs(os.path.join(d, "CairnCommons", "intentions-congruency-lab"))
        os.makedirs(os.path.join(d, "cairn", "cairn", "compiler_thing"))
        Path(d, "CairnCommons", "intentions-congruency-lab", "_model.json").write_text('{"old": 1}')
        Path(d, "cairn", "cairn", "compiler_thing", "compiler.py").write_text("# writes\n")
        packet = {
            "id": "2026-09-07-fixture-lowercase-marker",
            "kind": "ruling", "date": "2026-09-07",
            "ruled_by": "Akien", "recorded_by": "CC",
            "the_ruling_verbatim": ["a tool has users, not an owner", "ruled"],
            "now_the_spec_says": "The lab holds copies of every intention+why; there is no "
                                 "aggregate artifact.",
            "what_dies": ["CairnCommons/intentions-congruency-lab/_model.json"],
            "what_conforms": ["cairn/cairn/compiler_thing/compiler.py"],
        }
        marked = ruling.open_ruling(packet, d)
        record = json.loads(Path(marked).read_text(encoding="utf-8"))
        assert record["confirmed"] is True, record
        assert record["confirmation_verbatim"] == ["ruled"], (
            "the verbatim is stored AS HE TYPED IT — folding is a compare, never a rewrite")


def test_wrong_intent_free_text_lands_byte_identical():
    """The review words, the recordverdict words, and everything the dispatcher hands past
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
    assert fold_head(["recordverdict", "APPROVE", words], 2)[2] is words


def test_wrong_intent_a_stored_ticket_string_keeps_its_case():
    ticket = _REPO_ROOT.parent / "CairnCommons" / "tickets" / \
        "e3cf75c6dc8f-system-words-fold-case-when-akien-types-them.json"
    if not ticket.is_file():
        return
    wf = json.loads(ticket.read_text(encoding="utf-8"))["workflow_and_state"]
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
