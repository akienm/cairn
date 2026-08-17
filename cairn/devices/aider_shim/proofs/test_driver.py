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
#: A SEARCH block that cannot match. aider answers a failed match by REFLECTING — which is
#: the only lever this proof has for provoking the loop the cap closes, since auto_lint and
#: auto_test (the other two reflection sources) are OFF by bound.
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


def seam_file(where: Path, reply: str) -> str:
    p = Path(where) / "seam.py"
    p.write_text(_SEAM_SRC % reply, encoding="utf-8")
    return f"{p}:resolve"


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
        assert len(rows) == 1, rows       # read from the LOG, not from the return value


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


def test_a_brief_with_no_editable_file_is_refused():
    b = Brief(ticket="t", piece_index=0, spans=[], files=[], read_only=[], skipped=[])
    try:
        driver.drive_brief(b, drives_path=None)
    except driver.DriveRefused:
        return
    raise AssertionError("a briefless drive was attempted — that is a spent model call")


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
