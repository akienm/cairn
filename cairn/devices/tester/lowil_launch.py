"""Run a command at Low integrity with its home pointed at an instance swap (ticket 56b61c10bdbe).

The Windows half of the tester's instance seal. Linux binds a swap over ~/.cairn with bwrap;
Windows has no bind mount a user may make. So the subject runs at LOW integrity (S-1-16-4096),
and the kernel refuses its writes to every Medium object: the live ~/.cairn, the checkout, and
Medium %TEMP%. Its home, profile, LocalAppData and temp are pointed at a Low-labelled swap, so
the paths it computes land somewhere it may write.

MEASURED 2026-11-14 on akienyoga9i, non-admin: DuplicateTokenEx -> SetTokenInformation
(TokenIntegrityLevel, Low) -> CreateProcessAsUserW starts the child; the child is DENIED live
~/.cairn/logs, Medium %TEMP% and the repo root; it can WRITE an icacls-labelled Low dir and READ
the live root.

Run as a SCRIPT, not a module, because a subject's cwd need not hold the repo:

    python lowil_launch.py --swap <dir>/.cairn --cwd <dir> -- argv...

It runs inside the tester's job object (runs.run_owned), and its child stays in that job (no
breakaway flag), so the job's KILL_ON_JOB_CLOSE covers both. It waits for the child and exits
with the child's code. A launch that cannot be built exits LAUNCH_FAILED and writes one stderr
line starting with LAUNCH_FAILED_TAG, naming the Win32 error. The seal check reads that as
INDETERMINATE, never as a run.

TWO KINDS (orchestrator ruling C, 2026-11-14). ``--kind prevent`` (the default) runs the child
at Low, as above. ``--kind detect`` runs it at the CALLER's integrity with the same home and temp
redirect. It exists because MSYS bash cannot start at Low (measured: msys-2.0.dll's
NtCreateDirectoryObject gets 0xC0000022 and the process exits 0xC0000142), so a subject that
drives bash cannot be prevented, only witnessed. The tester's before/after manifest of the live
root is what witnesses it. The kind rides the child's env as CAIRN_TESTER_SEAL_KIND, so a nested
tester run knows which seal it inherited.

FAULT SEAM: CAIRN_TESTER_LOWIL_FAULT=1 makes the launch fail on purpose. It exists so that the
proof's tooth 4 can show the fallback is loud.
"""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys

LAUNCH_FAILED = 97
LAUNCH_FAILED_TAG = "LOWIL-LAUNCH-FAILED:"
FAULT_ENV = "CAIRN_TESTER_LOWIL_FAULT"
MARKER = "CAIRN_TESTER_INSTANCE_SEALED"
KIND_ENV = "CAIRN_TESTER_SEAL_KIND"
PREVENT, DETECT = "prevent", "detect"
LOW_SID = "S-1-16-4096"


def _fail(why: str) -> int:
    print(f"{LAUNCH_FAILED_TAG} {why}", file=sys.stderr, flush=True)
    return LAUNCH_FAILED


def child_env(swap: str, base: dict[str, str], kind: str = PREVENT) -> dict[str, str]:
    """The subject's env: the caller's, with every home-shaped variable pointed at the swap's
    parent (so ``Path.home() / '.cairn'`` IS the swap) and temp at a Low dir beside it."""
    home = os.path.dirname(os.path.abspath(swap))
    tmp = os.path.join(home, "tmp")
    env = dict(base)
    env.update({"HOME": home, "USERPROFILE": home, "LOCALAPPDATA": os.path.join(home, "AppData", "Local"),
                "TEMP": tmp, "TMP": tmp, "TMPDIR": tmp, MARKER: "1", KIND_ENV: kind})
    return env


def main(argv: list[str]) -> int:
    if "--" not in argv:
        return _fail("usage: lowil_launch.py --swap S --cwd C -- argv...")
    i = argv.index("--")
    opts, cmd = argv[:i], argv[i + 1:]
    kv = dict(zip(opts[0::2], opts[1::2]))
    swap, cwd = kv.get("--swap"), kv.get("--cwd") or os.getcwd()
    kind = kv.get("--kind", PREVENT)
    if not swap or not cmd:
        return _fail("a swap and a command are both required")
    if kind not in (PREVENT, DETECT):
        return _fail(f"--kind must be {PREVENT} or {DETECT}, got {kind!r}")
    if os.environ.get(FAULT_ENV) == "1":
        return _fail(f"{FAULT_ENV}=1 (the fault seam)")
    if sys.platform != "win32":
        return _fail(f"Low integrity is a Windows mechanism; this is {sys.platform}")
    env = child_env(swap, dict(os.environ), kind)
    for d in (env["TEMP"], env["LOCALAPPDATA"]):
        os.makedirs(d, exist_ok=True)
    exe = shutil.which(cmd[0]) or cmd[0]
    if kind == DETECT:
        # Same job, same handles, same redirect: only the token is the caller's.
        return subprocess.call([exe, *cmd[1:]], cwd=cwd, env=env)
    return _run_low([exe, *cmd[1:]], cwd, env)


def _run_low(cmd: list[str], cwd: str, env: dict[str, str]) -> int:
    import ctypes.wintypes as W
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    k32.GetCurrentProcess.restype = W.HANDLE
    k32.GetStdHandle.restype = W.HANDLE
    k32.GetStdHandle.argtypes = [W.DWORD]
    k32.SetHandleInformation.argtypes = [W.HANDLE, W.DWORD, W.DWORD]
    k32.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    k32.GetExitCodeProcess.argtypes = [W.HANDLE, ctypes.POINTER(W.DWORD)]
    k32.CloseHandle.argtypes = [W.HANDLE]
    adv.GetLengthSid.restype = W.DWORD
    adv.GetLengthSid.argtypes = [ctypes.c_void_p]
    adv.OpenProcessToken.argtypes = [W.HANDLE, W.DWORD, ctypes.POINTER(W.HANDLE)]
    adv.DuplicateTokenEx.argtypes = [W.HANDLE, W.DWORD, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                     ctypes.POINTER(W.HANDLE)]
    adv.SetTokenInformation.argtypes = [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD]
    adv.ConvertStringSidToSidW.argtypes = [W.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)]

    class SID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", W.DWORD)]

    class TOKEN_MANDATORY_LABEL(ctypes.Structure):
        _fields_ = [("Label", SID_AND_ATTRIBUTES)]

    class STARTUPINFO(ctypes.Structure):
        _fields_ = [("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR),
                    ("lpTitle", W.LPWSTR), ("dwX", W.DWORD), ("dwY", W.DWORD), ("dwXSize", W.DWORD),
                    ("dwYSize", W.DWORD), ("dwXCountChars", W.DWORD), ("dwYCountChars", W.DWORD),
                    ("dwFillAttribute", W.DWORD), ("dwFlags", W.DWORD), ("wShowWindow", W.WORD),
                    ("cbReserved2", W.WORD), ("lpReserved2", ctypes.c_void_p),
                    ("hStdInput", W.HANDLE), ("hStdOutput", W.HANDLE), ("hStdError", W.HANDLE)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE), ("dwProcessId", W.DWORD),
                    ("dwThreadId", W.DWORD)]

    def err(step: str) -> int:
        return _fail(f"{step} failed, Win32 error {ctypes.get_last_error()}")

    TOKEN_ALL = 0xF01FF
    tok, dup, sid = W.HANDLE(), W.HANDLE(), ctypes.c_void_p()
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), TOKEN_ALL, ctypes.byref(tok)):
        return err("OpenProcessToken")
    if not adv.DuplicateTokenEx(tok, TOKEN_ALL, None, 2, 1, ctypes.byref(dup)):
        return err("DuplicateTokenEx")
    if not adv.ConvertStringSidToSidW(LOW_SID, ctypes.byref(sid)):
        return err("ConvertStringSidToSidW")
    tml = TOKEN_MANDATORY_LABEL(SID_AND_ATTRIBUTES(sid, 0x20))   # SE_GROUP_INTEGRITY
    if not adv.SetTokenInformation(dup, 25, ctypes.byref(tml), ctypes.sizeof(tml) + adv.GetLengthSid(sid)):
        return err("SetTokenInformation(TokenIntegrityLevel)")

    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    si.dwFlags = 0x100                                            # STARTF_USESTDHANDLES
    std = []
    for n in (-10, -11, -12):                                     # stdin, stdout, stderr
        h = k32.GetStdHandle(W.DWORD(n & 0xFFFFFFFF))
        if h and h != W.HANDLE(-1).value:
            k32.SetHandleInformation(h, 1, 1)                     # HANDLE_FLAG_INHERIT
        std.append(h)
    si.hStdInput, si.hStdOutput, si.hStdError = std
    block = "".join(f"{k}={v}\0" for k, v in sorted(env.items())) + "\0"
    pi = PROCESS_INFORMATION()
    flags = 0x00000400 | 0x08000000                               # UNICODE_ENVIRONMENT | NO_WINDOW
    if not adv.CreateProcessAsUserW(dup, None, ctypes.create_unicode_buffer(subprocess.list2cmdline(cmd)),
                                    None, None, True, flags, ctypes.create_unicode_buffer(block),
                                    cwd, ctypes.byref(si), ctypes.byref(pi)):
        return err("CreateProcessAsUserW")
    k32.WaitForSingleObject(pi.hProcess, 0xFFFFFFFF)
    code = W.DWORD()
    k32.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
    for h in (pi.hThread, pi.hProcess, dup, tok):
        k32.CloseHandle(h)
    return code.value


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
