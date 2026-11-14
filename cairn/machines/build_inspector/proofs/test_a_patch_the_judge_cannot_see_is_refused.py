"""Proof (patch-in-the-asker tooth): a proof that patches a name the judge it asks reads in another process is refused.

Each tooth calls the NARROWEST thing that answers its question, ``unseen_patches.unseen_patches`` itself over a scratch repo (never the
whole build_inspector nest, never a CLI), so reverting an unrelated file reds nothing here (memory broad-tooth-manufactures-coverage).

  (1) a patch live across a judge the proof asks, which a reached file reads, is reported with proof, target, judge and chain, in every
      spelling: literal ask, a lambda alias, a call through transitions, an assignment under try/finally, a proof-local helper;
  (2) the asker-side negatives are silent: a module the judge does not reach, a patch with no ask in its scope, an attribute no reached file
      reads, an environment patch, a signature fake (the 0c2c ``env=`` shape), a patch of the seam itself; an unresolvable target is LISTED;
  (3) over the real tree: the pre-fix revisions of corrosion tooth 2, test_transitions and test_entry_gate_jurisdiction are reported, the
      0c2c draining fake is not, and none of the measured asker-side files is.

    python <this file>
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.machines.build_inspector import unseen_patches as U  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "03daad62ef1b": {
        "1": "a_patch_the_judge_reads_in_another_process_is_reported_with_its_target_judge_and_chain",
        "2": "the_asker_side_negatives_are_silent_and_an_unresolved_target_is_listed",
        "3": "over_the_real_tree_the_known_positives_report_and_the_0c2c_fake_and_the_asker_side_files_do_not",
    },
}

PRE_FIX = "d41cdc76c"       # main before 149b's corrosion fix, 3e08's tickets_root fix and the d3248 fix
RED3_PRE_FIX = "8d20852d6"  # main before fe0b6b541 (62a8ecb673a7, 02f0e9eee497, d2a76ee449ba: the fixture ticket store reaches the launched judges)

_M = U._MACHINE            # wherever the machine stands (cairn/machines/build_inspector, or codemother's machines after 93fa)

_FILES = {
    f"{_M}/__init__.py": "",
    f"{_M}/inspector.py": ("from cairn.lib import reader\nfrom cairn.lib import ledger\n\n\ndef j_reads():\n    return reader.ROOTS\n\n\n"
                           "def j_peeks():\n    return ledger.peek()\n\n\ndef lane():\n    return reader.ROOTS\n"),
    # a module the judges IMPORT, one of whose functions only the ASKER calls (enqueue) and one a judge calls (peek)
    "cairn/lib/ledger.py": "LEDGER = {}\n\n\ndef enqueue():\n    return LEDGER\n\n\ndef peek():\n    return LEDGER\n",
    f"{_M}/run_record.py": "def j_other():\n    return 1\n",
    "cairn/lib/__init__.py": "",
    "cairn/lib/reader.py": "ROOTS = {}\nUNUSED = 1\n\n\ndef get():\n    return ROOTS\n",
    "cairn/lib/other.py": "FLAG = 1\n",
    "cairn/lib/remote.py": "def _spawn(home, scratch, *, via_unit=True, env=None):\n    return 'unit'\n",
    "cairn/tools/__init__.py": "",
    "cairn/tools/base/__init__.py": "",
    "cairn/tools/base/transitions.py": (
        "def _judge(name):\n    return name\n\n\ndef emit():\n    return _judge('j_reads')\n\n\ndef plain():\n    return 1\n"),
}

_HEAD = "from unittest.mock import patch\nfrom cairn.tools.inspect_wire.inspect_wire import ask\n"

POSITIVES = {
    "literal ask": _HEAD + 'def t():\n    with patch("cairn.lib.reader.ROOTS", {}):\n        ask("j_reads")\n',
    "lambda alias": _HEAD + 'go = lambda *a: ask("j_reads", *a)\n\n\ndef t():\n    with patch("cairn.lib.reader.ROOTS", {}):\n        go(1)\n',
    "through transitions": ("from unittest.mock import patch\nimport cairn.tools.base.transitions as T\n\n\n"
                            'def t():\n    with patch("cairn.lib.reader.ROOTS", {}):\n        T.emit()\n'),
    "an assignment in a class's __enter__, used at a with-site (self._saved)": (
        _HEAD + "from cairn.lib import reader\n\n\nclass _Corpus:\n    def __init__(self, d):\n        self.d = d\n\n    def __enter__(self):\n"
        "        self._saved = reader.ROOTS\n        reader.ROOTS = self.d\n        return self\n\n    def __exit__(self, *a):\n"
        '        reader.ROOTS = self._saved\n\n\ndef t():\n    with _Corpus({}):\n        ask("j_reads")\n'),
    "the tuple swap, then a bare-name emit()": (
        "from cairn.tools.base.transitions import emit\nfrom cairn.lib import reader\n\n\ndef t(tickets):\n"
        "    saved, reader.ROOTS = reader.ROOTS, tickets\n    try:\n        emit()\n    finally:\n        reader.ROOTS = saved\n"),
    "assignment under try/finally": (_HEAD + "from cairn.lib import reader\n\n\ndef t():\n    saved = reader.ROOTS\n    reader.ROOTS = {}\n"
                                     '    try:\n        ask("j_reads")\n    finally:\n        reader.ROOTS = saved\n'),
    "proof-local helper": _HEAD + 'def _h():\n    return ask("j_reads")\n\n\ndef t():\n    with patch("cairn.lib.reader.ROOTS", {}):\n        _h()\n',
    # THE HANDED RULE IS NARROW: these three LOOK handed and are not (a broad rule here is the broad-tooth failure in a new place)
    "a launch handed a DIFFERENT value": (_HEAD + "from cairn.lib import reader\nfrom cairn.tools.inspect_wire.inspect_wire import launch\n\n\n"
                                          'def t(a, b):\n    reader.ROOTS = a\n    with launch(ticket_store=b):\n        ask("j_reads")\n'),
    "a launch BEFORE the patch": (_HEAD + "from cairn.lib import reader\nfrom cairn.tools.inspect_wire.inspect_wire import launch\n\n\n"
                                  'def t(a):\n    with launch(ticket_store=a):\n        pass\n    reader.ROOTS = a\n    ask("j_reads")\n'),
    "a launch carrying some other keyword": (_HEAD + "from cairn.lib import reader\nfrom cairn.tools.inspect_wire.inspect_wire import launch\n\n\n"
                                             'def t(a):\n    reader.ROOTS = a\n    with launch(berths=None, ticket_store=None):\n        ask("j_reads")\n'),
}

NEGATIVES = {
    "a module the judge does not reach": _HEAD + 'def t():\n    with patch("cairn.lib.other.FLAG", 2):\n        ask("j_reads")\n',
    "no ask in the patch's scope": (_HEAD + "from cairn.lib import reader\n\n\ndef t():\n    with patch(\"cairn.lib.reader.ROOTS\", {}):\n"
                                    '        reader.get()\n    ask("j_reads")\n'),
    "an attribute no reached file reads": _HEAD + 'def t():\n    with patch("cairn.lib.reader.UNUSED", 2):\n        ask("j_reads")\n',
    "an environment patch": ("import os\n" + _HEAD + 'def t():\n    with patch.dict(os.environ, {"X": "1"}):\n        ask("j_reads")\n'),
    "a signature fake (the 0c2c shape)": (_HEAD + "from cairn.lib import remote\n\n\ndef t():\n    def spawn(h, scratch, *, via_unit=True):\n"
                                          '        return "unit"\n    remote._spawn = spawn\n    try:\n        ask("j_reads")\n    finally:\n        remote._spawn = None\n'),
    "a patch of the seam itself": ("from cairn.tools.inspect_wire import inspect_wire as iw\n\n\ndef t():\n    iw.ask = lambda *a, **k: None\n    iw.ask('j_reads')\n"),
    # AN ASKER-SIDE READ IS NOT A JUDGE-SIDE ONE (3e08's LEDGER_PATH: enqueue_verdict runs in the asker's emit; the judges merely import
    # its module): the judge reaches the module that reads the name, but no function the judge calls does
    "a name only the asker's own function reads (the module is merely reached)": _HEAD + 'def t():\n    with patch("cairn.lib.ledger.LEDGER", {}):\n        ask("j_reads")\n',
    "a judge that reads nothing patched": _HEAD + 'def t():\n    with patch("cairn.lib.reader.ROOTS", {}):\n        ask("j_other")\n',
    # the 3e08 shape: the asker keeps its patch and hands the SAME binding to the launch at or after it
    "handed the same value to a launch at or after the patch": (
        _HEAD + "from cairn.lib import reader\nfrom cairn.tools.inspect_wire.inspect_wire import launch\n\n\n"
        'def t(tickets):\n    reader.ROOTS = tickets\n    with launch(berths=None, ticket_store=tickets):\n        ask("j_reads")\n'),
    "handed the same value to a launch already open on an ExitStack (the stones_pushed shape)": (
        _HEAD + "import contextlib\nfrom cairn.lib import reader\nfrom cairn.tools.inspect_wire.inspect_wire import launch\n\n\n"
        'def t(a):\n    world = contextlib.ExitStack()\n    world.enter_context(launch(ticket_store=a))\n    reader.ROOTS = a\n    ask("j_reads")\n'),
    "a restore in a finally is the patch undone, not a patch": (
        _HEAD + "from cairn.lib import reader\n\n\ndef t():\n    saved = reader.ROOTS\n    try:\n        pass\n    finally:\n"
        '        reader.ROOTS = saved\n    ask("j_reads")\n'),
    "tuple targets take the value at their own position": (
        _HEAD + "from cairn.lib import reader\nfrom cairn.tools.inspect_wire.inspect_wire import launch\n\n\n"
        'def t(a, b):\n    reader.ROOTS, reader.UNUSED = str(a), 1\n    with launch(ticket_store=a):\n        ask("j_reads")\n'),
    # a BACK-EDGE emit into the repair summons asks no judge (back-edges are never gated) and writes the fixme list in-process
    "an emit INTO FIXME (a back-edge, ungated, written in-process)": (
        "from cairn.tools.base.transitions import emit\nfrom cairn.lib import reader\n\n\ndef t(tickets):\n"
        '    saved, reader.ROOTS = reader.ROOTS, tickets\n    try:\n        emit("wf", "FIXME", ticket="x")\n    finally:\n        reader.ROOTS = saved\n'),
    "an __enter__ that hands the same value to a launch it keeps open (the fixed fe0b6b541 shape)": (
        _HEAD + "import contextlib\nfrom cairn.lib import reader\nfrom cairn.tools.inspect_wire.inspect_wire import launch\n\n\nclass _Corpus:\n"
        "    def __init__(self, d):\n        self.d = d\n\n    def __enter__(self):\n        self._saved = reader.ROOTS\n        reader.ROOTS = self.d\n"
        "        self._world = contextlib.ExitStack()\n        self._world.enter_context(launch(ticket_store=self.d))\n        return self\n\n"
        '    def __exit__(self, *a):\n        reader.ROOTS = self._saved\n        self._world.close()\n\n\ndef t():\n    with _Corpus({}):\n        ask("j_reads")\n'),
    "handed the same value, as str(), inside a with-patch": (
        _HEAD + "from cairn.tools.inspect_wire.inspect_wire import launch\n\n\n"
        'def t(tickets):\n    with patch("cairn.lib.reader.ROOTS", tickets):\n        with launch(ticket_store=str(tickets)):\n            ask("j_reads")\n'),
}


def _scratch_repo() -> Path:
    root = Path(str(scratch_dir("unseen_patches_")))
    for rel, text in _FILES.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8", newline="\n")
    return root


def a_patch_the_judge_reads_in_another_process_is_reported_with_its_target_judge_and_chain() -> None:
    root = _scratch_repo()
    try:
        U.clear_cache()
        for name, src in POSITIVES.items():
            got = U.unseen_patches(src, root, proof=name)["findings"]
            assert len(got) == 1, f"{name}: expected one finding, got {got}"
            f = got[0]
            assert f["target"] == "cairn.lib.reader.ROOTS" and f["proof"] == name, f"{name}: {f}"
            assert f["judge"].endswith("j_reads") or f["judge"].startswith("via transitions"), f"{name}: the judge is not named: {f}"
            assert f["chain"] and f["chain"][-1] == "cairn/lib/reader.py" and f["read_by"], f"{name}: no chain to the reader: {f}"
        # and the SAME module, read by a function a judge DOES call, is reported: the answer-side rule is a call-graph read, not a blanket skip
        peek = U.unseen_patches(_HEAD + 'def t():\n    with patch("cairn.lib.ledger.LEDGER", {}):\n        ask("j_peeks")\n', root, proof="peek")["findings"]
        assert len(peek) == 1 and peek[0]["target"] == "cairn.lib.ledger.LEDGER", f"a judge that calls the reading function was not reported: {peek}"
    finally:
        U.clear_cache()
        shutil.rmtree(root, ignore_errors=True)


def the_asker_side_negatives_are_silent_and_an_unresolved_target_is_listed() -> None:
    root = _scratch_repo()
    try:
        U.clear_cache()
        for name, src in NEGATIVES.items():
            got = U.unseen_patches(src, root, proof=name)
            assert got["findings"] == [], f"{name}: a false red: {got['findings']}"
        unresolved = _HEAD + 'def t():\n    with patch.object(mystery, "ROOTS", {}):\n        ask("j_reads")\n'
        got = U.unseen_patches(unresolved, root, proof="unresolved")
        assert got["findings"] == [] and [u["target"] for u in got["unresolved"]] == ["mystery.ROOTS"], got
    finally:
        U.clear_cache()
        shutil.rmtree(root, ignore_errors=True)


def _at(sha: str, rel: str) -> str:
    got = subprocess.run(["git", "-C", str(REPO), "show", f"{sha}:{rel}"], capture_output=True, text=True, encoding="utf-8")
    assert got.returncode == 0, f"git show {sha}:{rel} failed ({got.stderr.strip()[:120]}): this checkout lacks the pre-fix object, so the tooth cannot read it"
    return got.stdout


def over_the_real_tree_the_known_positives_report_and_the_0c2c_fake_and_the_asker_side_files_do_not() -> None:
    U.clear_cache()
    positives = ("cairn/machines/corrosion/proofs/test_corrosion_sieve.py", "cairn/tools/base/proofs/test_transitions.py",
                 "cairn/tools/base/proofs/test_entry_gate_jurisdiction.py")
    for rel in positives:
        got = U.unseen_patches(_at(PRE_FIX, rel), REPO, proof=rel)["findings"]
        assert got, f"{rel} at {PRE_FIX} patches a name its judge reads in another process and was not reported"
        assert all(f["chain"] and f["read_by"] for f in got), got
    # THE EXACT CLASS THE TOOTH EXISTS FOR, measured red on Linux and silent on the first build of this tooth (akiendelllinux): 62a8ecb673a7,
    # 02f0e9eee497, d2a76ee449ba. Two shapes: an assignment inside a class's __enter__ used at a `with Class(...)` site (test_fixme, test_emission_gate),
    # and the tuple swap `saved, X.attr = X.attr, new` followed by a bare-name emit(...) (test_every_watching_class_can_fixme).
    for rel in ("cairn/tools/base/proofs/test_fixme.py", "cairn/tools/base/proofs/test_emission_gate.py",
                "cairn/tools/base/proofs/test_every_watching_class_can_fixme.py"):
        got = U.unseen_patches(_at(RED3_PRE_FIX, rel), REPO, proof=rel)["findings"]
        assert got, f"{rel} at {RED3_PRE_FIX} was red for exactly this class and the tooth was silent on it"
        assert all(f["target"].endswith("ticket_file._TICKETS") for f in got), got
    fake = "cairn/tools/bus_client/proofs/test_a_draining_bus_is_used_not_raced.py"
    flagged = U.unseen_patches(_at(PRE_FIX, fake), REPO, proof=fake)["findings"]
    assert flagged == [], f"the 0c2c env= fake is a signature mismatch, not a patch the judge reads: {flagged}"
    asker_side = ("cairn/devices/inferenceproxy/proofs/test_the_domain_answers_for_its_migration.py",
                  "cairn/tools/base/proofs/test_the_crossing_asks_the_inspector_over_the_bus.py",
                  "cairn/tools/base/proofs/test_the_ticket_is_three_files.py",
                  "cairn/devices/inferenceproxy/proofs/test_resolve_verb.py", "cairn/devices/inferenceproxy/proofs/test_bus_infer.py",
                  "skills/chart/proofs/test_the_verbs_exit_nonzero_on_a_failed_drain.py")
    for rel in asker_side:
        got = U.unseen_patches((REPO / rel).read_text(encoding="utf-8"), REPO, proof=rel)["findings"]
        assert got == [], f"{rel} patches only in its own process and was reported: {got}"


TEETH = [a_patch_the_judge_reads_in_another_process_is_reported_with_its_target_judge_and_chain,
         the_asker_side_negatives_are_silent_and_an_unresolved_target_is_listed,
         over_the_real_tree_the_known_positives_report_and_the_0c2c_fake_and_the_asker_side_files_do_not]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:500]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
