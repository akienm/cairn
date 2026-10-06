"""Mail codemother cannot dispatch lands in the logs tree, not in her instance space (ticket
d10668f76c45, gap C of the 2026-10-05 re-plan).

CodeMotherShim._persist writes every verbless envelope (in practice: the replies to her own
requests) to ~/.cairn/devices/codemother/0/mail, and nothing ever reads or forgets them —
measured 2026-10-05: 3,666 files, 79MB, most of them the 689 refusals gap B traced. That is
exhaust, "what HAPPENED to it", which is what the logs tree is for (address.log_path: the trail
tree, forgotten past 30 days in one go). Kept in instance space it is copied into every tester
seal: the bare test_isolation measured a 203.7MB per-proof sandbox against its 150MB bound.

  1. UNHANDLED MAIL LANDS IN THE LOGS TREE: _persist writes under
     log_path('codemother', 0)/mail.
  2. NOTHING LANDS IN THE INSTANCE SPACE: after _persist, devices/codemother/0/mail does not
     exist.
  3. THE DEVICE SAYS WHERE ITS MAIL IS: CodeMotherDevice.state()['mail_dir'] names the logs address.
  4. THE LIVE INSTANCE KEEPS NO MAIL: the live ~/.cairn/devices/codemother/0/mail holds no
     files (the standing exhaust moved to the logs tree, where it ages out).

Teeth 1-3 run in a subprocess under a scratch HOME (the instance root is Path.home()/.cairn),
so the live instance is never written.

    python3 cairn/devices/codemother/proofs/test_unhandled_mail_lands_in_the_logs_tree.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"d10668f76c45": {
    "1": "test_unhandled_mail_lands_in_the_logs_tree",
    "2": "test_nothing_lands_in_the_instance_space",
    "3": "test_the_device_says_where_its_mail_is",
    "4": "test_the_live_instance_keeps_no_mail",
}}

_CALL = ("import json, sys; sys.path.insert(0, %r); "
         "from cairn.devices.codemother.shim import CodeMotherShim, CodeMotherDevice; "
         "r = CodeMotherShim._persist({'sender': 'cairn-proof-mail', 'body': {'testing': True}}); "
         "print(json.dumps({'path': r['path'], 'state': CodeMotherDevice.state(None)}))")

_RUN: dict = {}


def _run() -> dict:
    if not _RUN:
        home = scratch_dir("cairn-proof-codemother-mail-home-")
        env = dict(os.environ, HOME=str(home), PYTHONPATH=str(ROOT))
        r = subprocess.run([sys.executable, "-c", _CALL % str(ROOT)], env=env,
                           capture_output=True, text=True, timeout=60, cwd=str(ROOT))
        assert r.returncode == 0, r.stderr[-600:]
        _RUN.update(json.loads(r.stdout.strip().splitlines()[-1]), home=home)
    return _RUN


def test_unhandled_mail_lands_in_the_logs_tree():
    run = _run()
    want = run["home"] / ".cairn" / "logs" / "codemother" / "0" / "mail"
    assert Path(run["path"]).parent == want, f"persisted at {run['path']}, want under {want}"


def test_nothing_lands_in_the_instance_space():
    run = _run()
    legacy = run["home"] / ".cairn" / "devices" / "codemother" / "0" / "mail"
    assert not legacy.exists(), f"{legacy} exists: {list(legacy.iterdir())[:3]}"


def test_the_device_says_where_its_mail_is():
    run = _run()
    want = run["home"] / ".cairn" / "logs" / "codemother" / "0" / "mail"
    assert run["state"].get("mail_dir") == str(want), run["state"]


def test_the_live_instance_keeps_no_mail():
    live = Path.home() / ".cairn" / "devices" / "codemother" / "0" / "mail"
    files = [p for p in live.iterdir() if p.is_file()] if live.is_dir() else []
    assert not files, f"{live} still holds {len(files)} files"


def main() -> int:
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except Exception as exc:  # noqa: BLE001
                fails += 1
                print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not fails else 'RED'} — {4 - fails}/4")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
