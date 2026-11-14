"""A proof run through the tester on Linux cannot write the repo checkout (ticket 3dec3ede2616).

The tester seal's why is "a proof's writes reach only scratch and the swap". The Windows seal
(56b61c10bdbe) already denies a subject a write to the checkout by integrity level. Measured
2026-11-14: Linux's ``NoIsolation.wrap`` binds / writable (``--dev-bind / /``), so a subject could
write the checkout it ran from. This proof holds Linux to the same boundary.

  1. a stand-in proof run under the tester CLI that writes a fresh-token file under the checkout
     gets OSError EROFS, and no file naming the token exists in the checkout afterwards;
  2. the same stand-in can write its scratch dir and its swapped ~/.cairn (the seal does not
     only deny);
  3. a nested tester run inside a sealed run still runs, inherits the read-only checkout and the
     swap, and the swap holds the nested stand-in's write, not the checkout;
  4. the seal check reports the checkout bind: with the bind in place the instance seal names the
     checkout read-only, and with it withheld (bare) or reported writable (inherited) the seal
     reads BREACHED, never sealed.

THE CHECKOUT HERE is the one this proof runs from (``REPO``): it is the tester's own checkout, and
the seal binds it read-only for every subject. The stand-ins live in scratch, not in the checkout,
because writing them there would itself be the write this proof forbids.

Nested bwrap is refused on this host (measured 2026-11-14: "No permissions to create a new
namespace" from inside a bwrap), so a nested run INHERITS the outer binds and cannot lay its own.
Each tooth works both ways: run bare it starts the seal, run under the tester it inherits it.

Linux with bwrap only. Elsewhere every tooth prints NOTRUN, naming the platform.

    bin/cairn test cairn/devices/tester/proofs/test_a_linux_tester_run_cannot_write_the_checkout.py
"""
from __future__ import annotations

import errno
import os
import subprocess
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"3dec3ede2616": {
    "1": "test_a_stand_in_writing_the_checkout_meets_erofs_and_leaves_nothing",
    "2": "test_the_stand_in_still_writes_its_scratch_and_its_swap",
    "3": "test_a_nested_run_inherits_the_read_only_checkout_and_the_swap",
    "4": "test_the_instance_seal_names_the_checkout_and_breaches_without_it",
}}

PROOF_TIMEOUT_S = 300

# A stand-in proof: argv-free, its targets baked in. It prints a tooth line per check the way the
# tester's parser reads them, and exits 1 on the first check that fails, saying which.
_STAND_IN = '''\
import errno, os, sys, tempfile
from pathlib import Path
checkout, token = {checkout!r}, {token!r}
def fail(why):
    print("FAIL " + why)
    raise SystemExit(1)
target = Path(checkout) / token
try:
    target.write_text("written from inside the seal")
except OSError as e:
    if e.errno != errno.EROFS:
        fail(f"a checkout write raised errno {{e.errno}}, not EROFS")
else:
    fail(f"a checkout write LANDED at {{target}}")
print("  ok    test_the_checkout_is_read_only")
scratch = Path(tempfile.gettempdir()) / token
scratch.write_text("scratch write")
print("  ok    test_scratch_is_writable")
swap = Path.home() / ".cairn" / token
swap.write_text("swap write")
print("  ok    test_the_swap_is_writable")
print("SWAP_TOKEN " + str(swap))
'''

# The outer stand-in for clause 3: it runs the tester CLI over the inner one from inside its own
# sealed run, and reads the inner's swap write from its own view of ~/.cairn.
_NESTED = '''\
import subprocess, sys
from pathlib import Path
repo, inner, token = {repo!r}, {inner!r}, {token!r}
done = subprocess.run([sys.executable, "-m", "cairn.devices.tester.cli", "--timeout", "120", inner],
                      cwd=repo, capture_output=True, text=True, timeout=280,
                      env={{**__import__("os").environ, "PYTHONPATH": repo}})
if done.returncode != 0 or "1 green" not in done.stdout:
    print("FAIL the nested run was not green: rc=%s %s %s" % (done.returncode, done.stdout[-1500:], done.stderr[-600:]))
    raise SystemExit(1)
print("  ok    test_the_nested_run_is_green")
if not (Path.home() / ".cairn" / token).exists():
    print("FAIL the nested stand-in's swap write is not in this run's ~/.cairn")
    raise SystemExit(1)
print("  ok    test_the_nested_write_is_in_the_inherited_swap")
'''


def _linux_with_bwrap() -> str | None:
    """None when this box can run the teeth, else why not."""
    if not sys.platform.startswith("linux"):
        return f"needs Linux with bwrap; this is {sys.platform}"
    from cairn.devices.tester.isolation import bwrap_available
    ok, why = bwrap_available()
    return None if ok else f"needs bwrap: {why}"


def _stand_in(prefix: str, body: str) -> Path:
    proof = scratch_dir(prefix) / "stand_in" / "proofs" / "test_stand_in.py"
    proof.parent.mkdir(parents=True)
    proof.write_text(body, encoding="utf-8", newline="\n")
    return proof


def _run_cli(proof: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "cairn.devices.tester.cli", "--timeout", "240", str(proof)],
        cwd=REPO, capture_output=True, text=True, timeout=290,
        env={**os.environ, "PYTHONPATH": str(REPO)})


def _say(done: subprocess.CompletedProcess) -> str:
    return f"rc={done.returncode}\n{done.stdout[-2000:]}\n{done.stderr[-800:]}"


def test_a_stand_in_writing_the_checkout_meets_erofs_and_leaves_nothing():
    token = f"checkout-ro-probe-{uuid.uuid4().hex}"
    done = _run_cli(_stand_in("checkout-ro-1-", _STAND_IN.format(checkout=str(REPO), token=token)))
    leaked = REPO / token
    if leaked.exists():
        leaked.unlink()
        raise AssertionError(f"the stand-in's write landed in the checkout at {leaked}\n{_say(done)}")
    assert "test_the_checkout_is_read_only" in done.stdout and done.returncode == 0, _say(done)


def test_the_stand_in_still_writes_its_scratch_and_its_swap():
    token = f"checkout-ro-probe-{uuid.uuid4().hex}"
    done = _run_cli(_stand_in("checkout-ro-2-", _STAND_IN.format(checkout=str(REPO), token=token)))
    (REPO / token).unlink(missing_ok=True)
    assert "test_scratch_is_writable" in done.stdout, _say(done)
    assert "test_the_swap_is_writable" in done.stdout, _say(done)
    assert done.returncode == 0, _say(done)


def test_a_nested_run_inherits_the_read_only_checkout_and_the_swap():
    token = f"checkout-ro-probe-{uuid.uuid4().hex}"
    inner = _stand_in("checkout-ro-3i-", _STAND_IN.format(checkout=str(REPO), token=token))
    outer = _stand_in("checkout-ro-3o-", _NESTED.format(repo=str(REPO), inner=str(inner), token=token))
    done = _run_cli(outer)
    leaked = REPO / token
    if leaked.exists():
        leaked.unlink()
        raise AssertionError(f"the nested stand-in's write landed in the checkout\n{_say(done)}")
    assert "test_the_nested_write_is_in_the_inherited_swap" in done.stdout, _say(done)
    assert done.returncode == 0, _say(done)


def test_the_instance_seal_names_the_checkout_and_breaches_without_it():
    from cairn.devices.tester import isolation as I
    from cairn.tools.validation_store.validation_store import BREACHED
    cwd = str(Path(__file__).resolve().parent)
    roots = I.checkout_roots(cwd)
    assert str(REPO) in roots, f"the checkout {REPO} is not among the roots the seal binds: {roots}"
    if I.inside_an_instance_seal():
        swap = I._INSTANCE_ROOT
        held = I.check_instance_seal(I.NoIsolation(), swap, cwd)
        assert held.sealed and str(REPO) in held.detail and "read-only" in held.detail, held
        real = I._mount_options
        I._mount_options = lambda: {p: (o - {"ro"}) | {"rw"} for p, o in real().items()}
        try:
            open_ = I.check_instance_seal(I.NoIsolation(), swap, cwd)
        finally:
            I._mount_options = real
    else:
        swap = str(scratch_dir("checkout-ro-4-"))
        held = I.check_instance_seal(I.NoIsolation(), swap, cwd)
        assert held.verdict != BREACHED and str(REPO) in held.detail and "read-only" in held.detail, held
        real = I.instance_bind_flags
        I.instance_bind_flags = lambda swap_root, checkouts=(): real(swap_root, checkouts=())
        try:
            open_ = I.check_instance_seal(I.NoIsolation(), swap, cwd)
        finally:
            I.instance_bind_flags = real
    assert open_.verdict == BREACHED and str(REPO) in open_.detail, open_


TEETH = [test_a_stand_in_writing_the_checkout_meets_erofs_and_leaves_nothing,
         test_the_stand_in_still_writes_its_scratch_and_its_swap,
         test_a_nested_run_inherits_the_read_only_checkout_and_the_swap,
         test_the_instance_seal_names_the_checkout_and_breaches_without_it]


def main() -> int:
    why = _linux_with_bwrap()
    if why:
        for t in TEETH:
            print(f"NOTRUN {t.__name__} - {why}")
        return 0
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok    {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:1500]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
