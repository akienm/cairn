"""The runnable aider: a venv in instance-space, and the three names deliberately absent.

WHY THIS IS A MODULE AND NOT A COMMAND SOMEBODY RAN ONCE. This is the only piece of the
device that changes the BOX rather than the repo, so it is the only piece whose failure is
not undone by `git checkout`. A one-off `pip install` leaves the box in a state no artifact
describes; this module states the set, builds it, and — the part that matters — carries a
re-runnable :func:`verify` that can go red later, when the venv has drifted and nothing in
git has changed. That is the host-seam shape: an `apply` recipe and a re-runnable check,
because the implementation lives where git cannot see it.

THE THREE ABSENCES ARE THE POINT, and they are Akien's ruling of 2026-08-16 (recorded at
CairnCommons/decisions/2026-08-16-the-shims-venv-omits-litellm-and-stubs-the-telemetry.json):
``litellm``, ``posthog`` and ``mixpanel`` are NOT installed. The shim pre-empts all three
at ``sys.modules`` before importing aider, so aider gets a Cairn-owned surface in each
case. Not installing them turns each fence from an interception into a physics (Law 4): if
the shim's install ordering ever failed — the one way interception can be bypassed —
``import litellm`` raises ImportError loudly instead of quietly loading a real provider
client and dialing out. His words, on the option that removed the dependency rather than
the option that matched upstream: *"Install, and leave litellm OUT"* and *"Stub them at
sys.modules like litellm"*.

THE REQUIRED SET IS MEASURED, AND THE MEASUREMENT WAS WRONG TWICE BEFORE IT WAS RIGHT.
It is the guard-aware import closure of ``aider.coders`` + ``aider.models`` + ``aider.io``
(62 aider modules). The first walk resolved relative imports in package ``__init__.py``
against the parent instead of the package, and missed every coder module. The second
counted imports wrapped in ``try: ... except ImportError:`` as required, which put ``babel``
in the set — a package that is not in aider's own requirements.txt, has a documented
fallback three lines below its import, and would have been installed for nothing. The
discrepancy was the tell: OUR measurement and UPSTREAM'S manifest disagreed, and rather
than pick one, opening base_coder.py settled it in a line. The number in the triage berth
(24) is that second walk's; berths are records of truth and are not edited to agree with
what came later, so the correction rides the verdict artifact instead.

REQUIRED-TO-IMPORT IS NOT REQUIRED-TO-WORK, and conflating them is how this list would go
wrong a third time. ``gitpython`` is guarded, so the closure says aider imports fine
without it — and this device edits a git repo for a living, so it is installed anyway,
under a stated functional reason rather than an import-graph one. ``babel`` is guarded AND
cosmetic (locale-code prettification with a fallback mapping), so it stays out.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

#: Instance-space. Law 6 and the three roots: no runtime state in class-space, ever.
VENV = Path.home() / ".cairn" / "devices" / "aider_shim" / "0" / "venv"

#: The held foreign program. NEVER pip-installed — `pip install -e` writes an egg-info
#: into the checkout, and constrain puts modifying ~/dev/src/aider out of bounds. The
#: holder puts it on sys.path instead, which touches nothing.
AIDER_SRC = Path.home() / "dev" / "src" / "aider"

#: Measured import-time closure of the Coder path, at aider HEAD 5dc9490bb, pinned to
#: aider's own requirements.txt so we are not inventing versions it was never tested at.
REQUIRED = (
    "diff-match-patch==20241021",
    "diskcache==5.6.3",
    "grep-ast==0.9.0",
    "importlib-resources==6.5.2",
    "json5==0.13.0",
    "oslex==0.1.3",
    "packaging==26.0",
    "pathspec==1.0.4",
    "pexpect==4.9.0",
    "pillow==12.1.1",
    "prompt-toolkit==3.0.52",
    "psutil==7.2.2",
    "pydub==0.25.1",
    "pygments==2.19.2",
    "pypandoc==1.17",
    "pyperclip==1.11.0",
    "pyyaml==6.0.3",
    "requests==2.32.5",
    "rich==14.3.3",
    "tqdm==4.67.3",
    "tree-sitter==0.25.2",
)

#: Guarded by try/except ImportError, so not needed to IMPORT aider — installed because
#: this device's whole job is producing diffs in a git repo. A functional reason, stated.
FUNCTIONAL = ("gitpython==3.1.46",)

#: CAIRN'S OWN RUNTIME, and it is a separate tuple on purpose. The venv is not "aider's
#: environment" — it is THIS DEVICE'S PROCESS, and the shim's completion() runs inside it,
#: which means everything Cairn imports on the way to the inference host must be here too.
#: The first live fire is what taught this: aider imported perfectly, the fence refused a
#: widened ask perfectly, and the real call died at `from cairn.devices.db_domain import
#: store` -> ModuleNotFoundError: psycopg2. A dependency closure measured over the FOREIGN
#: program answers what aider needs and is silent about what WE need in the same process.
#: Measured by the same guard-aware closure pointed at our own entry modules (holder,
#: interceptor, inference_domain.domain, inference_domain.host): 8 Cairn modules reached,
#: exactly one third-party root, no guarded ones. Version matches the host interpreter's.
CAIRN_RUNTIME = ("psycopg2-binary==2.9.12",)

#: Never installed. Each is answered by a Cairn-owned surface at sys.modules instead.
ABSENT = {
    "litellm": "the shim answers this surface; absent from disk so a failed interception "
               "raises ImportError instead of dialing a provider (Akien, 2026-08-16)",
    "posthog": "telemetry client that loads at aider import time; stubbed, and absent so "
               "the stub is not the only thing standing between it and the network",
    "mixpanel": "as posthog — aider/analytics.py imports both unconditionally",
    "openai": "arrives only through litellm, which is absent; if it ever appears here, "
              "something pulled a provider client in transitively and that is a finding",
}

#: Guarded AND cosmetic — locale prettification with a fallback mapping in base_coder.py.
DECLINED = {"babel": "guarded by try/except with a documented fallback; not in aider's "
                     "own requirements.txt either — our first closure was wrong, not aider"}


def python() -> Path:
    return VENV / "bin" / "python"


def build(*, upgrade: bool = False) -> dict:
    """Create the venv and install the stated set. Returns what it did, for the record."""
    VENV.parent.mkdir(parents=True, exist_ok=True)
    created = not python().exists()
    if created:
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    pkgs = list(REQUIRED) + list(FUNCTIONAL) + list(CAIRN_RUNTIME)
    cmd = [str(python()), "-m", "pip", "install", "--disable-pip-version-check", "-q"]
    if upgrade:
        cmd.append("--upgrade")
    subprocess.run(cmd + pkgs, check=True)
    return {"venv": str(VENV), "created": created, "installed": len(pkgs)}


def verify() -> dict:
    """RE-RUNNABLE, and it is the half that can go red without git changing.

    THIS IS DELIBERATELY NOT A SEALED PROOF, and the distinction is not bookkeeping: a
    sealed proof may never read instance-space, and every question here is a question ABOUT
    instance-space — what is installed in a venv under ~/.cairn. Putting this in ``proofs/``
    would either break that rule or force the check to assert something weaker that happens
    to be readable from class-space, which is how a check ends up measuring a proxy. It is
    the ``verify`` half of a host-seam instead: the implementation lives where git cannot
    see it, so its seal expires and the check is re-run rather than trusted.


    Three questions, all answered by running the venv's own interpreter rather than by
    reading a list we wrote: is every required package importable, is every ABSENT name
    genuinely not on disk, and does aider itself import once the shim's surfaces are in
    place. The middle one is the ruling's instrument — a transitive dependency could drag
    litellm or openai in at any future install, and nothing else in the system would
    notice.
    """
    if not python().exists():
        return {"ok": False, "why": f"no venv at {VENV} — run build() first"}

    probe = r"""
import importlib, importlib.util, json, sys
required = json.loads(sys.argv[1]); absent = json.loads(sys.argv[2])
missing = [m for m in required if importlib.util.find_spec(m) is None]
present = [m for m in absent if importlib.util.find_spec(m) is not None]
print(json.dumps({"missing_required": missing, "present_but_absent": present}))
"""
    # import names, not distribution names — the two differ for half this set
    import_names = ["diff_match_patch", "diskcache", "grep_ast", "importlib_resources",
                    "json5", "oslex", "packaging", "pathspec", "pexpect", "PIL",
                    "prompt_toolkit", "psutil", "pydub", "pygments", "pypandoc",
                    "pyperclip", "yaml", "requests", "rich", "tqdm", "tree_sitter", "git",
                    "psycopg2"]
    r = subprocess.run([str(python()), "-c", probe, json.dumps(import_names),
                        json.dumps(sorted(ABSENT))], capture_output=True, text=True)
    if r.returncode != 0:
        return {"ok": False, "why": "the venv's interpreter failed", "stderr": r.stderr}
    out = json.loads(r.stdout)

    held = _import_aider_in_venv()
    out["aider_imports"] = held["ok"]
    out["aider_detail"] = held["detail"]
    out["ok"] = (not out["missing_required"] and not out["present_but_absent"]
                 and held["ok"])
    return out


def _import_aider_in_venv() -> dict:
    """Import aider inside the venv with the shim's surfaces installed first.

    THIS IS THE WHOLE ARRANGEMENT, EXERCISED. If it passes, the held program loaded with
    zero real provider clients and zero telemetry clients in the process — which is the
    device's central claim, measured rather than asserted.
    """
    script = r"""
import json, sys
sys.path.insert(0, %r)   # cairn, for the shim
sys.path.insert(0, %r)   # the held foreign program, NOT pip-installed
from cairn.devices.aider_shim import holder
holder.hold()
import aider.coders, aider.models, aider.io
real = [n for n in ("litellm", "posthog", "mixpanel", "openai")
        if n in sys.modules and not getattr(sys.modules[n], "_cairn_surface", False)]
print(json.dumps({"ok": not real, "real_modules_loaded": real,
                  "coders": len(aider.coders.__all__) if hasattr(aider.coders, "__all__") else -1}))
""" % (str(Path(__file__).resolve().parents[3]), str(AIDER_SRC))
    r = subprocess.run([str(python()), "-c", script], capture_output=True, text=True)
    if r.returncode != 0:
        return {"ok": False, "detail": (r.stderr or "").strip()[-1500:]}
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "detail": f"unparseable: {r.stdout!r} {r.stderr!r}"}
    if d["real_modules_loaded"]:
        return {"ok": False,
                "detail": f"REAL modules loaded in-process: {d['real_modules_loaded']} — "
                          "a surface was bypassed"}
    return {"ok": True, "detail": d}


if __name__ == "__main__":
    if "--verify" in sys.argv:
        print(json.dumps(verify(), indent=2))
    else:
        print(json.dumps(build(upgrade="--upgrade" in sys.argv), indent=2))
        print(json.dumps(verify(), indent=2))
