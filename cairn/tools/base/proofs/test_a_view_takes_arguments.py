"""A view takes arguments from the command line and the bus (ticket 35b92c5de7ef).

Akien, 2026-10-13: *"cairn inference_domain show/get calls --limit 20 --- show for me
(formatted), get for you (json)"*. Measured the same day: shim.py ``_resolve`` called
``device_views[name]()`` and device.py ``_handle_get``/``_handle_show`` called ``view_fn()``,
so a parameterised read could not be a view.

Teeth, one per falsifier clause (PROVES below), over an inline device whose view
``echo(limit=None)`` returns ``{'limit': limit}`` and whose view ``bare()`` takes none:
  (1) resolve get echo --limit 3 is exit 0 and its data is {'limit': '3'};
  (2) resolve show echo --limit 3 is exit 0 and its text is _render_view('echo', {'limit': '3'});
  (3) resolve get echo --bogus 1 is exit 2 and the text names bogus and limit;
  (4) resolve get bare --limit 1 is exit 2;
  (5) _handle_get with body args {'limit': '3'} is accepted with data {'limit': '3'}.
Hollow: today's shim.py and device.py red 1, 2, 3 and 5.

THE SHIM IS DRIVEN IN A SUBPROCESS PER COMMAND UNDER A SCRATCH HOME, as test_root_verbs.py
does: the instance root is read from HOME at import, so the snapshot a hot call writes lands
under the scratch, and a LIVE liveness record stops the start-the-loop check spawning anything.

    bin/cairn test cairn/tools/base/proofs/test_a_view_takes_arguments.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"35b92c5de7ef": {
    "1": "test_get_passes_the_args",
    "2": "test_show_renders_with_the_args",
    "3": "test_an_undeclared_key_is_refused",
    "4": "test_a_view_with_no_params_refuses_args",
    "5": "test_the_bus_get_passes_args",
}}

DEVICE_ID = "35b9-echo"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


# --- the fixture, built at call time so a reverted base reds the tooth, not the reader ---------

def _classes():
    from cairn.tools.base.device import BaseDevice
    from cairn.tools.base.shim import BaseShim

    class EchoDevice(BaseDevice):
        @property
        def device_id(self) -> str:
            return DEVICE_ID

        def intention(self) -> dict:
            return {"what": "fixture echo", "why": "proof"}

        def state(self) -> dict:
            return {"awake": True}

        def settings(self) -> dict:
            return {}

        def _echo(self, limit=None) -> dict:
            return {"limit": limit}

        def _bare(self) -> dict:
            return {"bare": True}

        def declared_views(self) -> dict:
            return {"echo": self._echo, "bare": self._bare}

    class EchoShim(BaseShim):
        @property
        def device_id(self) -> str:
            return DEVICE_ID

        def _start_device(self):
            return EchoDevice()

    return EchoDevice, EchoShim


def _drive(argv: list[str]) -> None:
    """Child: one command, its result as one line of JSON on stdout."""
    EchoDevice, EchoShim = _classes()
    if argv[0] == "--bus":
        out = EchoDevice()._handle_get({"body": json.loads(argv[1])})
    else:
        out = EchoShim().resolve(argv)
        out = {"exit": out["exit"], "text": out["text"], "data": out["data"]}
    print("RESULT " + json.dumps(out, default=str))


# --- the harness ------------------------------------------------------------------------------

def _scratch() -> Path:
    from cairn.tools.liveness.liveness import write_liveness
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("35b9-home-")
    lh = home / ".cairn" / "devices" / "cairn" / "0" / "machines" / "ground_loop"
    lh.mkdir(parents=True)
    write_liveness(datetime.now(timezone.utc).astimezone(), {"beats": 1, "subscribers": []}, os.getpid(), lh)
    return home


def _run(home: Path, *argv: str) -> dict:
    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(ROOT))
    r = subprocess.run([sys.executable, __file__, "--drive", *argv], env=env,
                       capture_output=True, text=True, timeout=120, cwd=str(ROOT))
    for line in r.stdout.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):])
    raise RuntimeError(f"child printed no result (rc={r.returncode}): {r.stderr.strip()[-400:]}")


# --- the teeth --------------------------------------------------------------------------------

def test_get_passes_the_args(home: Path) -> None:
    r = _run(home, "get", "echo", "--limit", "3")
    check("test_get_passes_the_args", r["exit"] == 0 and r["data"] == {"limit": "3"}, str(r)[:300])


def test_show_renders_with_the_args(home: Path) -> None:
    EchoDevice, _ = _classes()
    want = EchoDevice._render_view(None, "echo", {"limit": "3"})
    r = _run(home, "show", "echo", "--limit", "3")
    check("test_show_renders_with_the_args", r["exit"] == 0 and r["text"] == want, str(r)[:300])


def test_an_undeclared_key_is_refused(home: Path) -> None:
    r = _run(home, "get", "echo", "--bogus", "1")
    ok = r["exit"] == 2 and "bogus" in r["text"] and "limit" in r["text"]
    check("test_an_undeclared_key_is_refused", ok, str(r)[:300])


def test_a_view_with_no_params_refuses_args(home: Path) -> None:
    r = _run(home, "get", "bare", "--limit", "1")
    check("test_a_view_with_no_params_refuses_args", r["exit"] == 2, str(r)[:300])


def test_the_bus_get_passes_args(home: Path) -> None:
    r = _run(home, "--bus", json.dumps({"what": "echo", "args": {"limit": "3"}}))
    ok = r.get("accepted") is True and r.get("data") == {"limit": "3"}
    check("test_the_bus_get_passes_args", ok, str(r)[:300])


def main() -> int:
    home = _scratch()
    for tooth in (test_get_passes_the_args, test_show_renders_with_the_args,
                  test_an_undeclared_key_is_refused, test_a_view_with_no_params_refuses_args,
                  test_the_bus_get_passes_args):
        try:
            tooth(home)
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drive":
        _drive(sys.argv[2:])
        raise SystemExit(0)
    raise SystemExit(main())
