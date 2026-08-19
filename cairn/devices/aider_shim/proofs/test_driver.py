#!/usr/bin/env python3
"""The driver's teeth: the shim stops being inert, and every bound is measured, not stated.

WHAT A HOLLOW BUILD WOULD LOOK LIKE HERE, because that is what the teeth are shaped
against. A driver that returned its brief unchanged — no Coder, no ask, no edit — would
satisfy every "it did not spend money" and "it did not commit" assertion perfectly, since
the empty set has no counterexamples. So the drive teeth below assert POSITIVELY: the file
content changed to what the injected reply asked for, the seen-log is non-empty, the ask
carries the ticket, and the hashes that moved are the ones aider says it moved. Then the
negatives (no commit, one ask, no network) mean something, because the drive is shown to
have HAPPENED.

THE MUTANT THAT MAKES THE CAP TOOTH REAL. "Exactly one ask" is satisfied by any drive that
never reflects, so a fixture that cannot provoke a reflection would pass with the cap
removed. The pair below drives the SAME reflection-provoking fixture twice — once at
max_reflections=0 and once at aider's own default of 3 — and asserts the count moves. The
cap is what holds the number down, and the second half is what proves it.

NO NETWORK, BY INJECTION AND NOT BY HOPE. Every drive here passes a `resolve` seam by name
(the venv is a different process, so a callable cannot cross; a dotted/file spec can). The
metered door is never reached, the host is never dialled, and that is why the netns-sealed
run and the bare run are identical by construction rather than by luck.

THIS PROOF DEPENDS ON THE BOX, AND SAYS SO AT ITS FIRST TOOTH. The venv under
~/.cairn/devices/aider_shim/0/ is where aider is importable with our surfaces standing —
instance-space, invisible to git. That is the host-seam shape this device already declares
for venv.verify(), and the honest handling is a LOUD precondition naming the fix
(`python -m cairn.devices.aider_shim.venv`) rather than a scatter of obscure reds. A seal
taken here expires when the box drifts; re-running is the answer, not trusting the seal.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.aider_shim import driver, venv  # noqa: E402
from cairn.devices.aider_shim.translate import Brief, Span  # noqa: E402

FAILURES = []
MODEL = "qwen3-coder:30b"


def check(name, fn):
    try:
        fn()
        print(f"  ok   {name}")
    except Exception:
        FAILURES.append(name)
        print(f"  FAIL {name}")
        traceback.print_exc()


# ------------------------------------------------------------------------- fixtures

GOOD_REPLY = (
    "calc.py\n```python\n<<<<<<< SEARCH\n    return a - b\n=======\n"
    "    return a + b\n>>>>>>> REPLACE\n```\n"
)
#: A SEARCH block that cannot match. aider answers a failed match by REFLECTING — one of
#: the two levers this proof has for provoking the loop the cap closes. It was the ONLY one
#: until 2026-08-18, when the driver began constructing the Coder with ``auto_test=True``
#: (piece 7 below); a failing test is now the second, and the two are not interchangeable —
#: see the section comment there for why a tooth that means the test path must use a reply
#: that APPLIES CLEANLY. ``auto_lint`` remains off by bound.
MISMATCH_REPLY = (
    "calc.py\n```python\n<<<<<<< SEARCH\n    return NOTHING_LIKE_THIS\n=======\n"
    "    return a + b\n>>>>>>> REPLACE\n```\n"
)

_SEAM_SRC = '''
REPLY = %r

def resolve(request, *, resolver=None, **_kw):
    """The injected door. No host, no metered path, no network — by construction."""
    return {"answer": {"text": REPLY, "role": "assistant"}, "hit": False,
            "canonical": "fixture", "cost": 0,
            "provenance": {"provider": "hex", "counters": {}}}
'''


#: A seam that answers a SEQUENCE. The reflection teeth need the apprentice to say two
#: different things inside ONE coder.run() — a first reply that leaves the piece's test
#: failing, then a second that fixes it — and the constant seam above cannot stage that.
#:
#: The counter is plain module state, and that is a MEASURED choice rather than a lucky
#: one. driver._DRIVE resolves a seam by exec'ing the file ONCE per drive and handing the
#: bound attribute to holder.hold(), so this module lives exactly as long as the venv
#: subprocess: state persists across calls within a drive and cannot leak into the next
#: one. The disk sidecar this fixture was hypothesized to need would have been a second
#: mechanism for a lifetime the process boundary already gives for free.
#:
#: Past the end of the list it REPEATS the last reply instead of raising. An IndexError
#: would report "the fixture ran out" as a crash, which reads as a broken proof; repeating
#: makes an over-reflecting drive show up as what it is — extra asks carrying nothing new.
_SEAM_MULTI_SRC = r'''
import json as _json

REPLIES = %r
TRANSCRIPT = %r
_n = [0]

def resolve(request, *, resolver=None, **_kw):
    """The injected door, answering a sequence and TRANSCRIBING what it was asked.

    The transcript is the only way the question 'did the second ask carry the test's
    failure text?' can be answered. The fence's ask log records ask_chars and never the
    payload, deliberately — a persistent record of every prompt is a different artifact
    with different costs. But the seam IS the apprentice's ear, so what reached it is
    exactly what a fixture may keep, for the life of one tmpdir.

    THIS sidecar is on disk because it has to cross a process boundary: the seam runs
    inside the venv subprocess and the tooth reading it does not. The reply counter above
    needs no such thing — it is consumed in the same process that increments it.
    """
    i = min(_n[0], len(REPLIES) - 1)
    _n[0] += 1
    with open(TRANSCRIPT, "a", encoding="utf-8") as fh:
        fh.write(_json.dumps({"n": _n[0], "messages": request.get("messages", []),
                              "model": request.get("model")}) + "\n")
    return {"answer": {"text": REPLIES[i], "role": "assistant"}, "hit": False,
            "canonical": "fixture", "cost": 0,
            "provenance": {"provider": "hex", "counters": {}}}
'''


def seam_file(where: Path, reply: str) -> str:
    p = Path(where) / "seam.py"
    p.write_text(_SEAM_SRC % reply, encoding="utf-8")
    return f"{p}:resolve"


def seam_file_multi(where: Path, replies: list, name: str = "seam_multi") -> str:
    """A seam file whose replies are handed out in order, transcribing every ask it takes.
    ``name`` keeps two seams in one tmpdir from overwriting each other."""
    p = Path(where) / f"{name}.py"
    p.write_text(_SEAM_MULTI_SRC % (list(replies), str(Path(where) / f"{name}.asks.jsonl")),
                 encoding="utf-8")
    return f"{p}:resolve"


def seam_asks(where: Path, name: str = "seam_multi") -> list:
    """What the multi-reply seam was actually asked, in order. Empty when it was never
    reached — which is itself readable, and different from 'asked once'."""
    p = Path(where) / f"{name}.asks.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def ask_text(ask: dict) -> str:
    """Every message of one ask, flattened. The failure text can land in any role's
    content depending on how aider frames a reflection, so a tooth that looked only at
    the last user message could go green for the wrong reason."""
    return "\n".join(str(m.get("content", "")) for m in ask.get("messages", []))


def a_repo(where: Path) -> Path:
    repo = Path(where) / "repo"
    repo.mkdir()
    (repo / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    git(repo, "init", "-q", ".")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return repo


def git(repo, *args) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"git {args} failed in {repo}: {r.stderr}")
    return r.stdout


def a_brief(repo: Path, *, test_cmd: str = "", ticket: str = "aider-builds-a-piece") -> Brief:
    """A hand-built Brief. The chain that would produce one is proved elsewhere; what this
    file is about is what happens to a brief once someone finally runs it."""
    return Brief(
        ticket=ticket, piece_index=0,
        spans=[Span(text="Change add() so it returns the sum.", kind="scaffold", key="fixture")],
        files=[str(repo / "calc.py")], read_only=[], skipped=[], test_cmd=test_cmd,
        chain={}, map_tokens=0,
    )


def driven(tmp, *, reply=GOOD_REPLY, test_cmd="", max_reflections=0, ticket="aider-builds-a-piece"):
    repo = a_repo(tmp)
    return repo, driver.drive_brief(
        a_brief(repo, test_cmd=test_cmd, ticket=ticket), repo=repo, model=MODEL,
        log_path=Path(tmp) / "asks.jsonl", drives_path=Path(tmp) / "drives.jsonl",
        seams={"resolve": seam_file(tmp, reply)}, max_reflections=max_reflections,
    )


# ================================================================ piece 1: transport

def test_the_venv_precondition_is_loud_and_names_its_fix():
    """FIRST, so box drift reads as one directive instead of a dozen obscure reds."""
    if not venv.python().exists():
        raise AssertionError(
            f"no venv at {venv.VENV} — this device's proofs drive the real aider inside "
            "it. Build it with: python3 -m cairn.devices.aider_shim.venv"
        )


def test_transport_round_trips_serializable_data():
    payload = {"a": [1, 2, {"b": None}], "c": "ünïcode", "d": True}
    got = venv.run_in_venv("emit(ARG)", payload)
    assert got == payload, got


def test_transport_survives_noise_on_stdout():
    """The marker, not the last line. A stray print must not become the result."""
    got = venv.run_in_venv(
        "print('chatter before')\nemit({'v': 1})\nprint('chatter after')\n")
    assert got == {"v": 1}, got


def test_transport_is_loud_when_the_script_raises():
    try:
        venv.run_in_venv("raise ValueError('DISTINCTIVE-MARKER-9174')")
    except venv.VenvRunFailed as failed:
        text = str(failed)
        for want in ("DISTINCTIVE-MARKER-9174", str(venv.python()), "returncode"):
            assert want in text, f"the diagnostic omits {want!r}:\n{text}"
        assert failed.returncode not in (0, None), failed.returncode
        return
    raise AssertionError("a raising script came back without a VenvRunFailed")


def test_transport_never_returns_none_for_a_failure():
    """Silence must not be indistinguishable from a script that legitimately emitted null."""
    try:
        venv.run_in_venv("pass")
    except venv.VenvRunFailed as failed:
        assert "emitted nothing" in str(failed), str(failed)
    else:
        raise AssertionError("a script that emitted nothing returned instead of raising")
    assert venv.run_in_venv("emit(None)") is None, "an emitted null must still be a value"


def test_the_path_order_is_the_arrangement():
    got = venv.run_in_venv("import sys\nemit(sys.path[:2])")
    assert got[0] == str(venv.AIDER_SRC), got
    assert got[1] == str(Path(driver.__file__).resolve().parents[3]), got


def test_the_import_arrangement_still_holds_through_the_verb():
    """The re-expression's falsifier: verify() runs on the verb now and must be unchanged."""
    out = venv.verify()
    assert out["ok"] is True, out
    assert out["aider_imports"] is True, out
    assert out["aider_detail"]["real_modules_loaded"] == [], out
    assert out["missing_required"] == [] and out["present_but_absent"] == [], out


# ============================================================== piece 2: the real Coder

def test_the_drive_edits_through_the_real_coder():
    with tempfile.TemporaryDirectory() as tmp:
        repo, r = driven(Path(tmp))
        assert not r.error, f"{r.error}\n{r.traceback}"
        assert (repo / "calc.py").read_text() == "def add(a, b):\n    return a + b\n", \
            (repo / "calc.py").read_text()
        assert r.edit_format == "diff", r.edit_format
        assert len(r.allowed_asks) == 1, r.asks
        assert r.allowed_asks[0]["model"] == MODEL, r.asks


#: The reply that put the ROOT on trial. Two blocks: one edits the brief's file at its
#: repo-relative path, one CREATES a file the brief never named. A new file is the decisive
#: half — an existing file can be recovered by aider's fuzzy filename matching against the
#: in-chat files, so only a path with nothing to match against reads the root straight.
NESTED_REPLY = (
    "pkg/calc.py\n```python\n<<<<<<< SEARCH\n    return a - b\n=======\n"
    "    return a + b\n>>>>>>> REPLACE\n```\n"
    "stray.py\n```python\n<<<<<<< SEARCH\n=======\nVALUE = 7\n>>>>>>> REPLACE\n```\n"
)


def a_nested_repo(where: Path) -> Path:
    """The brief's only editable file sits one directory DOWN. That is the whole fixture:
    with a single file at the repo top, the common ancestor of the file list happens to BE
    the repo, and the defect this pair of teeth pins is invisible."""
    repo = Path(where) / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    # Not in the brief and not in aider's chat — the shape the first live drive hit, where
    # the stray path was an EXISTING file rather than a created one.
    (repo / "other.py").write_text("MARKER = 'before'\n", encoding="utf-8")
    git(repo, "init", "-q", ".")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return repo


#: The shape the FIRST LIVE DRIVE actually took: the brief named venv.py, the apprentice
#: emitted an edit to driver.py — a file that already existed and was in nobody's list.
PREEXISTING_REPLY = (
    "other.py\n```python\n<<<<<<< SEARCH\nMARKER = 'before'\n=======\n"
    "MARKER = 'after'\n>>>>>>> REPLACE\n```\n"
)


def driven_nested(tmp, reply=NESTED_REPLY):
    repo = a_nested_repo(Path(tmp))
    b = a_brief(repo)
    b.files = [str(repo / "pkg" / "calc.py")]
    return repo, driver.drive_brief(
        b, repo=repo, model=MODEL, log_path=Path(tmp) / "asks.jsonl",
        drives_path=Path(tmp) / "drives.jsonl",
        seams={"resolve": seam_file(Path(tmp), reply)}, max_reflections=0,
    )


def test_aiders_root_is_the_REPO_not_the_ancestor_of_the_file_list():
    """THE MEASURED FAILURE OF 2026-08-17, made into a tooth.

    With ``use_git=False`` aider has no repo to ask, so ``Coder.__init__`` sets
    ``self.root = utils.find_common_root(self.abs_fnames)`` (base_coder.py:476, read by
    AST) — the common ANCESTOR of the editable files. There is no ``root`` constructor
    argument. While the brief handed aider nine files spanning ``cairn/``, that ancestor
    WAS the repo and nobody noticed; the first drive with a piece-scoped list had ONE
    editable file, the ancestor collapsed to that file's directory, and the apprentice's
    edit landed at a path nested one level deeper than it named — a new file, while the
    file it was asked to edit was never touched.

    The kill: ``stray.py`` is resolved against the root. Pinned, it lands at the repo top.
    Unpinned, it lands under ``pkg/`` — so BOTH halves are asserted, because "the file
    exists" alone stays green in a world where it exists in the wrong place too."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, r = driven_nested(tmp)
        assert not r.error, f"{r.error}\n{r.traceback}"
        assert (repo / "stray.py").exists(), \
            f"the created file is not at the repo top; tree: {sorted(p.relative_to(repo) for p in repo.rglob('*.py'))}"
        assert not (repo / "pkg" / "stray.py").exists(), \
            "the root collapsed to the editable file's directory — the pin is not holding"
        assert (repo / "pkg" / "calc.py").read_text() == "def add(a, b):\n    return a + b\n", \
            (repo / "pkg" / "calc.py").read_text()


def test_the_record_WITNESSES_an_edit_the_brief_never_named():
    """A record that images only the brief's files cannot witness a write outside them: every
    imaged hash stays equal, so ``hashes_moved`` reports nothing moved while a file was
    created. That is blindness in the one direction a record of truth may not have it
    (Law 7) — and it is how the 2026-08-17 misplacement went unreported by everything
    except aider's own edit list. Pinning the root makes the case rare, not impossible.

    ``before`` says ``{"exists": False}`` rather than an image taken after the drive:
    imaging now would record the drive's own output as the state before it, and
    ``survival`` would then read a created file as ``untouched``."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, r = driven_nested(tmp)
        assert not r.error, f"{r.error}\n{r.traceback}"
        assert "stray.py" not in r.files, r.files          # never in the brief
        assert "stray.py" in r.aider_reported_edited, r.aider_reported_edited
        assert "stray.py" in r.hashes_moved, r.hashes_moved
        assert driver.survival(asdict(r), root=repo)["stray.py"] == "survived", \
            driver.survival(asdict(r), root=repo)
        # AND THE BEFORE-STATE IS `unimaged`, NOT `{"exists": False}`. It said the latter
        # until the first live drive, whose stray path was an existing file — so the record
        # asserted a file's absence that nobody had measured, which is the same defect one
        # layer in. `exists: False` would be right for THIS fixture and wrong in the wild,
        # and a tooth that green-lights a claim only its fixture makes true is the
        # fixture agreeing with the reader instead of the writer.
        assert r.before.get("stray.py") == {"unimaged": True}, r.before


def test_a_stray_edit_to_an_EXISTING_file_is_not_recorded_as_a_file_that_was_absent():
    """THE LIVE FIRE'S OWN FINDING, four hours after the tooth above was sealed.

    First real drive: the brief named ``venv.py``, the apprentice emitted an edit to
    ``driver.py``. The record witnessed it — that much worked — but wrote the before-state
    as ``{"exists": False}``, and ``driver.py`` had existed all along. The record had been
    taught to see out-of-bounds writes and, in the same act, to lie about them.

    ``unimaged`` is the honest answer and the reason it is a SENTINEL rather than a late
    image: a before-image not taken before is not a before-image. ``survival`` then still
    answers ``survived`` (does the world hold what the drive left? — decidable) and refuses
    ``reverted`` (was it what it used to be? — not decidable), which is the whole of what
    the sentinel buys."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, r = driven_nested(tmp, reply=PREEXISTING_REPLY)
        assert not r.error, f"{r.error}\n{r.traceback}"
        assert (repo / "other.py").read_text() == "MARKER = 'after'\n", \
            (repo / "other.py").read_text()
        assert "other.py" not in r.files, r.files
        assert r.before.get("other.py") == {"unimaged": True}, \
            f"the record claims to know a state it never measured: {r.before}"
        assert r.after.get("other.py", {}).get("exists") is True, r.after
        assert "other.py" in r.hashes_moved, r.hashes_moved
        assert driver.survival(asdict(r), root=repo)["other.py"] == "survived", \
            driver.survival(asdict(r), root=repo)
        # And the one the sentinel exists to make unsayable: put the file back the way it
        # was, and the record must NOT claim it was reverted — it cannot know that.
        (repo / "other.py").write_text("MARKER = 'before'\n", encoding="utf-8")
        assert driver.survival(asdict(r), root=repo)["other.py"] == "unknown_before", \
            driver.survival(asdict(r), root=repo)


def test_construction_alone_makes_no_ask():
    """Constructing must be separable from asking, or 'one ask per drive' means nothing."""
    got = venv.run_in_venv(r'''
from pathlib import Path
from cairn.devices.aider_shim import holder
from cairn.devices.aider_shim.fence import SeenLog
def tripwire(*a, **k):
    raise AssertionError("the door was reached during CONSTRUCTION")
log = SeenLog(record_path=None)
holder.hold(ticket="proof", log=log, resolve=tripwire)
import aider.models as M
from aider.coders import Coder
from aider.io import InputOutput
from cairn.devices.aider_shim.interceptor import _model_info
M.model_info_manager.local_model_metadata[ARG["model"]] = _model_info(ARG["model"], None)
p = Path(ARG["file"]); p.write_text("x = 1\n")
coder = Coder.create(main_model=M.Model(ARG["model"]),
                     io=InputOutput(pretty=False, yes=True, fancy_input=False),
                     fnames=[str(p)], read_only_fnames=[], edit_format="diff",
                     map_tokens=0, auto_commits=False, dirty_commits=False, auto_lint=False,
                     auto_test=False, use_git=False, stream=False,
                     suggest_shell_commands=False, detect_urls=False, analytics=None)
emit({"asks": log.entries, "map_tokens": coder.repo_map is not None,
      "repo": coder.repo is not None, "fnames": sorted(coder.abs_fnames),
      "auto_commits": coder.auto_commits})
''', {"model": MODEL, "file": str(Path(tempfile.mkdtemp()) / "x.py")})
    assert got["asks"] == [], got["asks"]


def test_every_bound_is_a_constructor_argument():
    """Read the bounds back OFF THE INSTANCE — a bound checked after the run is a bound
    the run already violated."""
    tmpdir = Path(tempfile.mkdtemp())
    f = tmpdir / "x.py"
    got = venv.run_in_venv(r'''
from pathlib import Path
from cairn.devices.aider_shim import holder
from cairn.devices.aider_shim.fence import SeenLog
holder.hold(ticket="proof", log=SeenLog(record_path=None),
            resolve=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no ask expected")))
import aider.models as M
from aider.coders import Coder
from aider.io import InputOutput
from cairn.devices.aider_shim.interceptor import _model_info
M.model_info_manager.local_model_metadata[ARG["model"]] = _model_info(ARG["model"], None)
p = Path(ARG["file"]); p.write_text("x = 1\n")
coder = Coder.create(main_model=M.Model(ARG["model"]),
                     io=InputOutput(pretty=False, yes=True, fancy_input=False),
                     fnames=[str(p)], read_only_fnames=[], edit_format="diff",
                     map_tokens=0, auto_commits=False, dirty_commits=False, auto_lint=False,
                     auto_test=False, use_git=False, stream=False,
                     suggest_shell_commands=False, detect_urls=False, analytics=None)
emit({"auto_commits": bool(coder.auto_commits), "repo_is_none": coder.repo is None,
      "repo_map_is_none": coder.repo_map is None, "auto_lint": bool(coder.auto_lint),
      "auto_test": bool(coder.auto_test), "stream": bool(coder.stream),
      "fnames": sorted(str(Path(x).resolve()) for x in coder.abs_fnames),
      "edit_format": coder.edit_format})
''', {"model": MODEL, "file": str(f)})
    assert got["auto_commits"] is False, got
    assert got["repo_is_none"] is True, got            # use_git=False
    assert got["repo_map_is_none"] is True, got        # map_tokens=0
    assert got["auto_lint"] is False and got["auto_test"] is False, got
    assert got["stream"] is False, got
    assert got["fnames"] == [str(f.resolve())], got    # confined to the brief
    assert got["edit_format"] == "diff", got
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_model_construction_reaches_no_network():
    """THE MEASURED SURPRISE OF THIS BUILD, made into a tooth.

    aider's ModelInfoManager falls through to a bare ``requests.get`` against
    raw.githubusercontent.com whenever its 24h cache is cold. On this box the cache was 19
    hours old, so the first measurement came back clean — a green that would have flipped
    to red overnight with nothing in git changing. Both halves run here: seeded (the
    driver's arrangement) must reach nothing, unseeded must reach something. If the second
    half ever stops reaching, this tooth has gone vacuous and says so.
    """
    script = r'''
import tempfile
from pathlib import Path
from cairn.devices.aider_shim import holder
from cairn.devices.aider_shim.fence import SeenLog
holder.hold(ticket="proof", log=SeenLog(record_path=None), resolve=lambda *a, **k: None)
import requests
reached = []
def tripwire(url, *a, **k):
    reached.append(str(url))
    raise AssertionError("network reached")
requests.get = tripwire
import aider.models as M
from cairn.devices.aider_shim.interceptor import _model_info
mim = M.model_info_manager
cold = Path(tempfile.mkdtemp())
mim.cache_dir = cold; mim.cache_file = cold / "cache.json"
mim.content = None; mim._cache_loaded = False
if ARG["seed"]:
    mim.local_model_metadata[ARG["model"]] = _model_info(ARG["model"], None)
err = ""
try:
    info = dict(M.Model(ARG["model"]).info)
except BaseException as bad:
    info = None; err = "%s: %s" % (type(bad).__name__, bad)
emit({"reached": reached, "info": info, "err": err})
'''
    seeded = venv.run_in_venv(script, {"model": MODEL, "seed": True})
    assert seeded["reached"] == [], \
        f"the driver's arrangement reached the network unfenced: {seeded['reached']}"
    assert seeded["info"], seeded
    cold = venv.run_in_venv(script, {"model": MODEL, "seed": False})
    assert cold["reached"], \
        ("unseeded construction reached nothing — the tooth above is now vacuous, because "
         "the thing it claims to prevent no longer happens. Re-read aider's "
         "ModelInfoManager before deleting either half.")


#: The seam that makes the network question answerable THROUGH THE DRIVER instead of
#: through a re-staging of what the driver does. It runs inside the venv before
#: ``aider.models`` is imported, which is the one window in which both levers work: HOME
#: decides where ModelInfoManager will look for its cache (``Path.home()`` reads the
#: environment at call time, and the manager is constructed at aider-import), and the
#: ``requests.get`` patch is what turns a reach into a file on disk.
_COLD_SEAM_SRC = '''
import os, requests
os.environ["HOME"] = %r          # a cold cache: nothing for the manager to find
RECORD = %r
REPLY = %r

def _tripwire(url, *a, **k):
    with open(RECORD, "a") as fh:
        fh.write(str(url) + "\\n")
    raise AssertionError("network reached: " + str(url))

requests.get = _tripwire

def resolve(request, *, resolver=None, **_kw):
    return {"answer": {"text": REPLY, "role": "assistant"}, "hit": False,
            "canonical": "fixture", "cost": 0,
            "provenance": {"provider": "hex", "counters": {}}}
'''


def test_the_driver_itself_reaches_no_network_with_a_cold_cache():
    """THE ONE ABOVE MEASURES THE ARRANGEMENT; THIS ONE MEASURES THE DRIVER.

    Written because the first version did not bite: deleting the driver's seeding line left
    every tooth green, since the network tooth re-staged the seeding itself instead of
    exercising the code that is supposed to do it. A fixture that agrees with the reader
    rather than the writer cannot fail — so this drives the real ``drive_brief`` with the
    cache pointed somewhere empty, and asks the world (a file the tripwire writes) whether
    anything dialled.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        repo = a_repo(tmp)
        cold_home = tmp / "cold-home"
        cold_home.mkdir()
        record = tmp / "reached.txt"
        seam = tmp / "cold_seam.py"
        seam.write_text(_COLD_SEAM_SRC % (str(cold_home), str(record), GOOD_REPLY),
                        encoding="utf-8")
        r = driver.drive_brief(a_brief(repo), repo=repo, model=MODEL,
                               log_path=tmp / "asks.jsonl", drives_path=tmp / "drives.jsonl",
                               seams={"resolve": f"{seam}:resolve"})
        assert not r.error, f"{r.error}\n{r.traceback}"
        assert (repo / "calc.py").read_text().endswith("a + b\n"), \
            "the drive did nothing, so 'it reached no network' is vacuous"
        assert not record.exists(), \
            ("the driver reached the network unfenced with a cold model-info cache:\n"
             + record.read_text())


def test_the_driven_repo_gains_no_commit():
    with tempfile.TemporaryDirectory() as tmp:
        repo = a_repo(Path(tmp))
        before = git(repo, "log", "--oneline")
        r = driver.drive_brief(a_brief(repo), repo=repo, model=MODEL,
                               log_path=Path(tmp) / "asks.jsonl",
                               drives_path=Path(tmp) / "drives.jsonl",
                               seams={"resolve": seam_file(Path(tmp), GOOD_REPLY)})
        assert not r.error, r.error
        assert (repo / "calc.py").read_text().endswith("a + b\n"), "the drive did nothing"
        assert git(repo, "log", "--oneline") == before, "the apprentice committed"
        assert "calc.py" in git(repo, "status", "--porcelain"), \
            "the edit is not showing as an uncommitted change — did it happen at all?"


# ================================================================== piece 3: the cap

def test_the_cap_holds_the_ask_to_one():
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven(Path(tmp), reply=MISMATCH_REPLY, max_reflections=0)
        assert len(r.allowed_asks) == 1, r.asks
        assert r.num_reflections == 0, r.num_reflections
        rows = [json.loads(x) for x in
                (Path(tmp) / "asks.jsonl").read_text().splitlines() if x.strip()]
        allowed = [r for r in rows if r["verdict"] == "allowed"]
        assert len(allowed) == 1, rows    # read from the LOG, not from the return value


def test_the_cap_is_what_holds_it_not_the_fixture():
    """The mutant. Same fixture, aider's own default cap — the count must move."""
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven(Path(tmp), reply=MISMATCH_REPLY, max_reflections=3)
        assert len(r.allowed_asks) > 1, \
            ("the reflection-provoking fixture provoked nothing even at max_reflections=3 — "
             f"so the cap tooth above proves nothing. asks={r.asks}")


# ============================================================= piece 4: the ticket stamp

def test_an_undirected_drive_records_to_the_fence_s_own_store():
    """THE ARRANGEMENT NO OTHER TOOTH EXERCISES: a drive that names no log path.

    Every other tooth here passes ``log_path=<tmp>/asks.jsonl``, so all of them passed
    while the default meant an in-memory log that died with the venv process — stamped
    correctly, written nowhere, and the offload probe's population empty through any
    number of real drives. Caught by the first live fire, which is the only thing that
    could have caught it. Two assertions, because the default has two ways to be wrong:
    the resolution can stop happening, and it can resolve somewhere that is not the store
    the probe reads.
    """
    from cairn.devices.aider_shim import fence

    assert driver.DEFAULT_ASKS == fence.DEFAULT_RECORD, \
        ("the driver's undirected drives and the fence's own store have drifted apart — "
         f"{driver.DEFAULT_ASKS} vs {fence.DEFAULT_RECORD}. Two spellings of one path is "
         "how a store quietly becomes two, and the probe reads the fence's.")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        repo = a_repo(tmp)
        stand_in = tmp / "default-asks.jsonl"        # never instance-space, from a proof
        was = driver.DEFAULT_ASKS
        driver.DEFAULT_ASKS = stand_in
        try:
            driver.drive_brief(a_brief(repo), repo=repo, model=MODEL,
                               drives_path=tmp / "drives.jsonl",
                               seams={"resolve": seam_file(tmp, GOOD_REPLY)})
        finally:
            driver.DEFAULT_ASKS = was
        assert stand_in.exists(), \
            ("a drive with no log_path wrote no ask log at all — the asks live and die "
             "inside the venv process, so nothing downstream can ever count them")
        rows = [json.loads(x) for x in stand_in.read_text().splitlines() if x.strip()]
        assert rows and all(r.get("ticket") == "aider-builds-a-piece" for r in rows), rows


def test_every_recorded_ask_names_the_ticket():
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven(Path(tmp), ticket="a-distinctive-ticket-id")
        rows = [json.loads(x) for x in
                (Path(tmp) / "asks.jsonl").read_text().splitlines() if x.strip()]
        assert rows, "no ask was recorded at all — the stamp claim would be vacuous"
        for row in rows:
            assert row.get("ticket") == "a-distinctive-ticket-id", row
        assert all(a.get("ticket") == "a-distinctive-ticket-id" for a in r.asks), r.asks


# ============================================================ piece 5: the drive record

def test_the_record_answers_survival_from_itself():
    with tempfile.TemporaryDirectory() as tmp:
        repo, r = driven(Path(tmp))
        row = driver.drives(Path(tmp) / "drives.jsonl")[-1]
        assert driver.survival(row, root=repo) == {"calc.py": "survived"}, \
            driver.survival(row, root=repo)
        (repo / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
        assert driver.survival(row, root=repo) == {"calc.py": "reverted"}, \
            driver.survival(row, root=repo)
        (repo / "calc.py").write_text("something else entirely\n", encoding="utf-8")
        assert driver.survival(row, root=repo) == {"calc.py": "changed_again"}, \
            driver.survival(row, root=repo)


def test_untouched_is_not_reverted():
    """The distinction the before-image exists for: a piece that did nothing must not
    report as a piece whose work was thrown away."""
    row = {"before": {"a.py": {"exists": True, "sha256": "x", "bytes": 1}},
           "after": {"a.py": {"exists": True, "sha256": "x", "bytes": 1}}}
    assert driver.survival(row, root="/nowhere") == {"a.py": "untouched"}


def test_hashes_moved_agrees_with_what_aider_reported():
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven(Path(tmp))
        assert r.hashes_moved == ["calc.py"], r.hashes_moved
        assert r.aider_reported_edited == ["calc.py"], r.aider_reported_edited


# ============================================================== piece 6: the test command

def test_a_passing_test_cmd_is_carried():
    out = driver.run_test("printf PASSMARK-4471", cwd=Path(tempfile.mkdtemp()))
    assert out["ran"] is True and out["returncode"] == 0 and out["passed"] is True, out
    assert "PASSMARK-4471" in out["stdout"], out


def test_a_failing_test_cmd_keeps_its_own_output():
    out = driver.run_test("printf FAILMARK-8823 >&2; exit 3", cwd=Path(tempfile.mkdtemp()))
    assert out["ran"] is True and out["returncode"] == 3 and out["passed"] is False, out
    assert "FAILMARK-8823" in out["stderr"], \
        "the failing output did not survive — a generic failure is exactly what Law 7 forbids"


def test_an_empty_test_cmd_is_not_run_and_not_passed():
    out = driver.run_test("", cwd=Path(tempfile.mkdtemp()))
    assert out["ran"] is False, out
    assert "passed" not in out, "an unrun test must not carry a verdict at all"


def test_the_test_result_rides_the_drive():
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven(Path(tmp), test_cmd="python3 -c \"import calc; assert calc.add(1,2)==3\"")
        assert r.test["ran"] is True, r.test
        assert r.test["passed"] is True, r.test


# ====================================================== piece 7: the reflection loop
#
# WHAT THESE TEETH ARE FOR, and why they are not a check on the constructor. Flipping
# auto_test and asserting the Coder received True is the hollow build this section exists
# to refuse: it was MEASURED that the device's existing bounds tooth
# (test_every_bound_is_a_constructor_argument) writes its own Coder.create call with
# auto_test=False as a literal and asserts it back off its own instance, so it stays green
# through this entire change and says nothing about what driver.py constructs. A tooth
# that cannot go red when the thing it names breaks is a fixture agreeing with its reader.
#
# So every tooth below drives the REAL driver.drive_brief and reads the outcome off the
# drive's own record: the reflection count, the ask log, and what the apprentice's ear
# actually heard.


FAIL_MARK = "TESTFAILMARK-5518"

#: A reply that APPLIES CLEANLY AND STILL FAILS THE TEST. This pair, not MISMATCH_REPLY, is
#: what makes the section honest — and the difference was MEASURED, not reasoned. Written
#: first against MISMATCH_REPLY, test_a_failing_test_reaches_the_apprentice went GREEN
#: against the unchanged driver: aider reflects on a failed SEARCH match all by itself, so
#: the tooth was watching the mismatch path and would have called it the test path. A reply
#: that lands its edit removes that other source of reflection entirely, leaving auto_test
#: as the only thing that can produce a second ask.
APPLIES_BUT_FAILS = (
    "calc.py\n```python\n<<<<<<< SEARCH\n    return a - b\n=======\n"
    "    return a * b\n>>>>>>> REPLACE\n```\n"
)
#: The follow-up, searching for what APPLIES_BUT_FAILS actually left behind.
FIX_AFTER_FAIL = (
    "calc.py\n```python\n<<<<<<< SEARCH\n    return a * b\n=======\n"
    "    return a + b\n>>>>>>> REPLACE\n```\n"
)


def a_gated_test(repo: Path) -> str:
    """A test command that FAILS LOUDLY until add() returns a sum — the lever the whole
    section turns on. It fails on the pre-edit repo, passes once the good reply lands, and
    prints a marker no other part of this file emits, so 'the failure text reached the
    apprentice' is a substring question rather than a judgement call."""
    (repo / "check.py").write_text(
        "import sys\n"
        "if 'a + b' in open('calc.py').read():\n"
        "    print('check ok')\n"
        "    sys.exit(0)\n"
        "sys.stderr.write(%r ': add() still subtracts, the piece is not done\\n')\n"
        "sys.exit(3)\n" % FAIL_MARK,
        encoding="utf-8")
    return "python3 check.py"


def driven_multi(tmp, *, replies, max_reflections=1, gated=True, name="seam_multi"):
    """A drive whose apprentice answers a SEQUENCE, against a test that gates on the edit."""
    tmp = Path(tmp)
    repo = a_repo(tmp)
    test_cmd = a_gated_test(repo) if gated else ""
    return repo, driver.drive_brief(
        a_brief(repo, test_cmd=test_cmd), repo=repo, model=MODEL,
        log_path=tmp / "asks.jsonl", drives_path=tmp / "drives.jsonl",
        seams={"resolve": seam_file_multi(tmp, replies, name=name)},
        max_reflections=max_reflections,
    )


def test_a_failing_test_reaches_the_apprentice():
    """THE VOYAGE'S CENTRAL CLAIM. A first reply that leaves the test failing must earn a
    SECOND ask — and the count is read off the drive, not off the constructor."""
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven_multi(tmp, replies=[APPLIES_BUT_FAILS, FIX_AFTER_FAIL], max_reflections=1)
        assert not r.error, r.error
        assert r.num_reflections >= 1, (
            "the drive reflected zero times against a test that FAILED — the apprentice was "
            f"never told. num_reflections={r.num_reflections}, test={r.test}, asks={r.asks}")
        assert len(r.allowed_asks) >= 2, (
            "one ask against a failing test means the loop did not close: aider answered, "
            f"the test ran, and nothing went back. asks={r.asks}")


def test_the_second_ask_carries_the_tests_own_failure():
    """A LOOP THAT CLOSES CARRYING NOTHING IS NOT A LOOP. The mechanism can report firing
    while the apprentice is simply asked again with no new information — which is the exact
    shape the ticket's watch stops early and loudly on."""
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven_multi(tmp, replies=[APPLIES_BUT_FAILS, FIX_AFTER_FAIL], max_reflections=1)
        asks = seam_asks(tmp)
        assert len(asks) >= 2, f"the seam was asked {len(asks)} time(s); expected >= 2"
        first, second = ask_text(asks[0]), ask_text(asks[1])
        assert FAIL_MARK not in first, (
            "the failure marker was in the FIRST ask — the test cannot have failed yet, so "
            "this tooth would pass without any reflection happening at all")
        assert FAIL_MARK in second, (
            "the second ask does not carry the test's own output. The apprentice was asked "
            "again and told nothing, which is a spent call rather than a correction. "
            f"second ask was {len(second)} chars")


def test_the_cap_still_holds_against_a_failing_test():
    """THE BOUND CONSTRAIN DREW. This voyage may not raise the number of asks any existing
    caller spends on the metered host, and every existing caller takes the default."""
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven_multi(tmp, replies=[APPLIES_BUT_FAILS, FIX_AFTER_FAIL], max_reflections=0)
        assert r.num_reflections == 0, r.num_reflections
        assert len(r.allowed_asks) == 1, (
            "a default-configured drive spent more than one ask — reflection escaped the "
            f"cap and every current caller just got more expensive. asks={r.asks}")
        rows = [json.loads(x) for x in
                (Path(tmp) / "asks.jsonl").read_text().splitlines() if x.strip()]
        allowed = [r for r in rows if r["verdict"] == "allowed"]
        assert len(allowed) == 1, rows     # from the LOG, not the return value


def test_the_default_max_reflections_is_still_zero():
    """The cap tooth above is only worth its assertion while the DEFAULT is the thing being
    capped. A default that drifted upward would leave that tooth measuring an argument
    nobody passes."""
    import inspect
    for fn in (driver.drive, driver.drive_brief):
        sig = inspect.signature(fn)
        assert sig.parameters["max_reflections"].default == 0, (fn.__name__, sig)


def test_the_arrangement_carries_the_briefs_own_test_command():
    """READ OFF THE DRIVE, NOT OFF A HAND-WRITTEN COPY. The gap survey measured was that the
    venv payload had no test_cmd field at all, so the Coder could not have been told the
    command whatever the constructor said. This asserts the command CROSSED — by its
    effect: the test ran inside aider's process, which is the only way a mismatch reply can
    provoke a reflection carrying the marker."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, r = driven_multi(tmp, replies=[APPLIES_BUT_FAILS, FIX_AFTER_FAIL], max_reflections=1)
        assert r.test.get("ran") is True, (
            "the PARENT's run_test did not run — the record's authority is missing and "
            f"nothing here can be about the second run. test={r.test}")
        assert FAIL_MARK in "\n".join(ask_text(a) for a in seam_asks(tmp)), (
            "no ask carries the marker, so aider never ran the command itself: the payload "
            "carried no test_cmd, or auto_test is off, or both")


def test_a_passing_test_provokes_no_reflection():
    """THE COMMON CASE, asserted so the loop cannot fire on success. A well-scoped piece
    whose first reply works must still cost exactly one ask."""
    with tempfile.TemporaryDirectory() as tmp:
        _, r = driven_multi(tmp, replies=[GOOD_REPLY, MISMATCH_REPLY], max_reflections=1)
        assert not r.error, r.error
        assert r.test.get("passed") is True, (
            f"the gated test did not pass after the good reply — the fixture is wrong, not "
            f"the driver. test={r.test}")
        assert len(r.allowed_asks) == 1, (
            f"a drive whose test PASSED still spent a second ask. asks={r.asks}")
        assert r.num_reflections == 0, r.num_reflections


def test_a_brief_with_no_editable_file_is_refused():
    b = Brief(ticket="t", piece_index=0, spans=[], files=[], read_only=[], skipped=[])
    try:
        driver.drive_brief(b, drives_path=None)
    except driver.DriveRefused:
        return
    raise AssertionError("a briefless drive was attempted — that is a spent model call")


def test_a_drive_that_reached_no_model_is_not_read_as_a_drive_that_made_no_edit():
    """THE MEASURED PAYLOAD OF A SILENT DRIVE, REPLAYED. On 2026-08-17 a drive ran 121s
    and came back with `asks: []`, `aider_reported_edited: []`, an empty `response_tail`,
    `num_reflections: 0` and `error: ""` — a clean, unremarkable success on its face, and
    the model had never been reached at all. That record is indistinguishable from a drive
    where the apprentice was asked and delivered nothing, and the two call for opposite
    next moves: fix the setup, or judge the apprentice. Misreading one as the other is
    what cost this device its first voyage.

    WHY THIS REPLAYS THE VENV RESULT INSTEAD OF DRIVING THE REAL AIDER, said plainly rather
    than hidden: no fixture arrangement found so far makes the real aider go quiet. Pointing
    it at a repo that holds none of the brief's files was TRIED here first — it asks anyway
    (measured, this box, 2026-08-17). So the thing under test is `drive_brief`'s own reading
    of a result it did get, and the result is the one that actually came back, pinned field
    for field. The real-aider path is exercised by every other tooth in this file.
    """
    silent = {"asks": [], "aider_reported_edited": [], "response_tail": "",
              "num_reflections": 0, "edit_format": "diff", "error": "", "traceback": ""}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        repo = a_repo(tmp)
        (tmp / "elsewhere").mkdir()
        elsewhere = a_repo(tmp / "elsewhere")   # where the brief's ABSOLUTE paths point
        drives = tmp / "drives.jsonl"
        was = driver.run_in_venv
        driver.run_in_venv = lambda *a, **k: dict(silent)
        try:
            driver.drive_brief(a_brief(elsewhere), repo=repo, model=MODEL,
                               log_path=tmp / "asks.jsonl", drives_path=drives)
        except driver.DriveRefused as red:
            said = str(red)
        else:
            raise AssertionError(
                "a drive that reached no model returned as an ordinary result — the caller "
                "has no way to tell it from an apprentice that produced nothing")
        finally:
            driver.run_in_venv = was

        assert "reached no model" in said.lower(), said
        # The two counts are MEASUREMENTS, and they must disagree — the file exists, and it
        # is not in the tree aider was pointed at. A message that only said "zero asks"
        # would leave the next mind exactly where the silent record left the last one.
        assert "1 exist on disk" in said and "0 are inside" in said, said
        assert str(repo) in said, said

        rows = driver.drives(drives)
        assert rows, ("the refusal ate the evidence — the drive record was never written, "
                      "so the only account of the silent drive is a raised exception")
        assert rows[-1]["asks"] == [] and "reached no model" in rows[-1]["error"].lower(), \
            rows[-1]


def test_an_ask_that_died_is_not_an_apprentice_that_declined():
    """THE SECOND WAY AN EMPTY EDIT LIST LIES, and the one the first check got wrong.

    Measured 2026-08-17: the ask WAS sent, hex answered without token counters, the door
    raised, and aider swallowed it at `base_coder.py:1506` and returned a clean result. The
    fence now writes the failed row before raising, so the count is no longer zero — and a
    check that only asked 'were there zero asks' would have called this a normal drive and
    handed the empty edit list up as evidence about the model. Only an ALLOWED ask means
    the apprentice was heard from, and that is what the driver reads.
    """
    died = {"asks": [{"at": "2026-08-17T21:18:45+00:00", "model": MODEL,
                      "verdict": "failed", "provider": "", "ticket": "aider-builds-a-piece",
                      "ask_chars": 299167, "num_ctx": 81920, "prompt_eval_count": None,
                      "detail": "HostUnmetered: the host reported no token counters"}],
            "aider_reported_edited": [], "response_tail": "", "num_reflections": 0,
            "edit_format": "diff", "error": "", "traceback": ""}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        repo = a_repo(tmp)
        drives = tmp / "drives.jsonl"
        was = driver.run_in_venv
        driver.run_in_venv = lambda *a, **k: json.loads(json.dumps(died))
        try:
            driver.drive_brief(a_brief(repo), repo=repo, model=MODEL,
                               log_path=tmp / "asks.jsonl", drives_path=drives)
        except driver.DriveRefused as red:
            said = str(red)
        else:
            raise AssertionError(
                "a drive whose only ask died came back as an ordinary result — the empty "
                "edit list is now standing in as evidence about the apprentice")
        finally:
            driver.run_in_venv = was

        assert "no ask survived" in said.lower(), said
        # The dispositions ride the message VERBATIM. A count alone would send the next
        # mind back to a JSONL file to find out what actually went wrong.
        assert "failed" in said and "no token counters" in said, said

        rows = driver.drives(drives)
        assert rows and "no ask survived" in rows[-1]["error"].lower(), \
            f"the refusal ate the evidence: {rows[-1] if rows else None}"


# ------------------------------------------------------------------------------ runner

def _main():
    print(__doc__.splitlines()[0])
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            check(name, fn)
    if FAILURES:
        print(f"\nRED — {len(FAILURES)} failure(s): {', '.join(FAILURES)}")
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
