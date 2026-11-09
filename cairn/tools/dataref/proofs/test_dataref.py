"""Proof: one address reads any stored value, and a Secret prints as stars.

Ticket 060d2146618c (outline 17.28). Measured 2026-11-09: the same .env line parse was written
three times (web_operator._env_value, ccfox env_value, CC0AC private.py), address.py's ROOTS had
no claude root and no #-item face, and nothing in cairn/ was a Secret. Every tooth reads a
scratch roots table; no live secret is read.

  1. cairn:, cairncommons:, instance:, claude: and file: each resolve to the right file under the
     scratch table, and cairn:/// and instance:/// equal address.resolve's repo/ and instance/.
  2. # walks env #KEY (export and quotes off), ini #section/key (a % is just a %), json #a/b/c
     (a list index too); no # gives the whole text.
  3. a Secret's str, repr, f-string, %-format, format(), .value and a logging call never show the
     value; .secret does; pickle.dumps and json.dumps raise.
  4. a Dataref re-reads after an atomic replace (new inode) and after an in-place edit, and not
     when nothing changed; a Secret keeps no value between reads.
  5. a missing file, a missing key, an unknown scheme, a relative file:, a db: address, a host, and
     a secret: address handed to plain Dataref each raise DatarefMiss naming the address, with
     no value from the file in the message, and no chained exception carrying one.
  6. web_operator.secret types the value it reads through a Secret, and _env_value is gone.

    python3 cairn/tools/dataref/proofs/test_dataref.py
"""
from __future__ import annotations

import io
import json
import logging
import os
import pickle
import secrets
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "060d2146618c": {
        "1": "tooth_1_each_scheme_names_its_root",
        "2": "tooth_2_the_hash_walks_inside_the_record",
        "3": "tooth_3_a_secret_never_shows_itself",
        "4": "tooth_4_a_file_is_reread_only_when_it_changed",
        "5": "tooth_5_a_miss_is_loud_and_names_the_address",
        "6": "tooth_6_web_operator_reads_through_a_secret",
    },
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:900]}", flush=True)
    if not ok:
        FAILURES.append(name)


class World:
    def __init__(self) -> None:
        self._d = tempfile.TemporaryDirectory(prefix="testing-060d2146618c-")
        base = Path(self._d.name)
        self.roots = {k: base / k for k in ("repo", "commons", "instance", "claude")}
        for p in self.roots.values():
            p.mkdir()
        self.value = "s3cr3t-" + secrets.token_hex(8)
        self.env = self.roots["instance"] / "devices" / "alpha" / "0" / ".env"
        self.env.parent.mkdir(parents=True)
        self.env.write_text(f"# mine\nOTHER=x\nexport TOKEN = '{self.value}'\nPCT=100%sure\n")
        (self.roots["repo"] / "conf").mkdir()
        (self.roots["repo"] / "conf" / "a.ini").write_text("[web]\nport = 12345\npct = 50%off\n")
        (self.roots["commons"] / "c.json").write_text(json.dumps({"a": {"b": {"c": "deep"}, "l": ["zero", "one"]}}))
        (self.roots["claude"] / "settings.json").write_text(json.dumps({"model": "opus"}))
        self.raw = base / "raw.env"
        self.raw.write_text("RAW=raw-value\n")
        self.plain = self.roots["repo"] / "notes.txt"
        self.plain.write_text("whole text\n")


def tooth_1(w: World) -> None:
    from cairn.tools.base import address
    from cairn.tools.dataref import ref
    got = {
        "cairn": ref("cairn:///conf/a.ini#web/port", roots=w.roots).value,
        "cairncommons": ref("cairncommons:///c.json#a/b/c", roots=w.roots).value,
        "instance": ref("instance:///devices/alpha/0/.env#OTHER", roots=w.roots).value,
        "claude": ref("claude:///settings.json#model", roots=w.roots).value,
        "file": ref(f"file://{w.raw}#RAW", roots=w.roots).value,
    }
    want = {"cairn": "12345", "cairncommons": "deep", "instance": "x", "claude": "opus", "file": "raw-value"}
    faces = (ref("cairn:///conf/a.ini", roots=w.roots).path == address.resolve("repo/conf/a.ini", w.roots)
             and ref("instance:///devices/alpha/0/.env", roots=w.roots).path
             == address.resolve("instance/devices/alpha/0/.env", w.roots))
    check(PROVES["060d2146618c"]["1"], got == want and faces, f"got={got} faces_equal={faces}")


def tooth_2(w: World) -> None:
    from cairn.tools.dataref import ref, Secret
    tok = Secret("secret:instance:///devices/alpha/0/.env#TOKEN", roots=w.roots).secret
    got = {
        "env_export_quotes": tok == w.value,
        "env_percent": ref("instance:///devices/alpha/0/.env#PCT", roots=w.roots).value == "100%sure",
        "ini_percent": ref("cairn:///conf/a.ini#web/pct", roots=w.roots).value == "50%off",
        "json_path": ref("cairncommons:///c.json#a/b/c", roots=w.roots).value == "deep",
        "json_index": ref("cairncommons:///c.json#a/l/1", roots=w.roots).value == "one",
        "whole_text": ref("cairn:///notes.txt", roots=w.roots).value == "whole text\n",
    }
    check(PROVES["060d2146618c"]["2"], all(got.values()), f"{got}")


def tooth_3(w: World) -> None:
    from cairn.tools.dataref import ref, Secret
    s = ref("secret:instance:///devices/alpha/0/.env#TOKEN", roots=w.roots)
    buf = io.StringIO()
    log = logging.getLogger("testing-060d2146618c")
    h = logging.StreamHandler(buf)
    log.addHandler(h)
    log.setLevel(logging.INFO)
    log.info("token is %s", s)
    log.info("token %r", s)
    log.removeHandler(h)
    shown = [str(s), repr(s), f"{s}", f"{s!r}", f"{s:>40}", "%s" % s, "%r" % (s,), format(s), s.value,
             buf.getvalue()]
    leaked = [x for x in shown if w.value in x]
    starred = all("**********" in x for x in shown)
    raises = {}
    for name, f in (("pickle", lambda: pickle.dumps(s)), ("json", lambda: json.dumps(s)),
                    ("json_in_dict", lambda: json.dumps({"t": s}))):
        try:
            f()
            raises[name] = False
        except Exception:  # noqa: BLE001
            raises[name] = True
    ok = (isinstance(s, Secret) and not leaked and starred and s.secret == w.value and all(raises.values()))
    check(PROVES["060d2146618c"]["3"], ok,
          f"is_secret={isinstance(s, Secret)} leaked={len(leaked)} starred={starred} "
          f"secret_ok={s.secret == w.value} raises={raises}")


def tooth_4(w: World) -> None:
    from cairn.tools.dataref import ref
    d = ref("cairn:///conf/a.ini#web/port", roots=w.roots)
    p = d.path
    first = d.value
    _ = d.value
    unchanged_reads = d.reads
    tmp = p.with_name("a.ini.tmp")                     # atomic replace: new inode, same size
    tmp.write_text("[web]\nport = 54321\npct = 50%off\n")
    st = p.stat()
    os.utime(tmp, ns=(st.st_atime_ns, st.st_mtime_ns))  # same mtime too: only the inode tells
    tmp.replace(p)
    after_replace = d.value
    with open(p, "a") as f:                            # in place: same inode, new size
        f.write("extra = 1\n")
    p.write_text(p.read_text().replace("54321", "11111"))
    after_edit = d.value
    s = ref("secret:instance:///devices/alpha/0/.env#TOKEN", roots=w.roots)
    _ = s.secret
    kept = [k for k, v in vars(s).items() if isinstance(v, str) and w.value in v]
    ok = (first == "12345" and unchanged_reads == 1 and after_replace == "54321"
          and after_edit == "11111" and d.reads == 3 and not kept)
    check(PROVES["060d2146618c"]["4"], ok,
          f"first={first} reads_while_unchanged={unchanged_reads} after_replace={after_replace} "
          f"after_edit={after_edit} reads={d.reads} secret_kept={kept}")


def tooth_5(w: World) -> None:
    from cairn.tools.dataref import ref, Dataref, DatarefMiss
    cases = {
        "missing file": "instance:///devices/alpha/0/nope.env#OTHER",
        "missing key": "secret:instance:///devices/alpha/0/.env#NOPE",
        "unknown scheme": "gopher:///x#y",
        "relative file": "file:raw.env#RAW",
        "db": "db:///cairn/t/row#token",
        "host": "cairn://akiendell/devices/alpha/0/.env#OTHER",
        "missing ini section": "cairn:///conf/a.ini#nope/port",
        "missing json step": "cairncommons:///c.json#a/zz",
    }
    bad = {}
    for name, addr in cases.items():
        try:
            r = ref(addr, roots=w.roots)
            _ = r.secret if hasattr(r, "secret") else r.value
            bad[name] = "did not raise"
        except DatarefMiss as e:
            msg = str(e)
            chained = e.__cause__ or (None if e.__suppress_context__ else e.__context__)
            if addr not in msg or w.value in msg or chained is not None:
                bad[name] = f"message={msg!r} chained={chained!r}"
        except Exception as e:  # noqa: BLE001
            bad[name] = f"raised {type(e).__name__}, not DatarefMiss"
    try:
        Dataref("secret:instance:///devices/alpha/0/.env#TOKEN", roots=w.roots).value
        bad["secret via Dataref"] = "did not raise"
    except DatarefMiss as e:
        if w.value in str(e):
            bad["secret via Dataref"] = "leaked"
    check(PROVES["060d2146618c"]["5"], not bad, f"{bad}")


def tooth_6(w: World) -> None:
    from cairn.machines.web_operator.web_operator import WebOperator
    from cairn.tools.dataref import dataref as dr
    seen: list[str] = []
    real = dr.Secret.secret

    def spy(self):
        seen.append(self.address)
        return real.fget(self)
    dr.Secret.secret = property(spy)
    try:
        op = WebOperator("alpha", 0, roots=w.roots)
        typed: list[str] = []
        op.type = lambda css, text, n=0: typed.append(text)
        op.secret("#pw", "TOKEN")
    finally:
        dr.Secret.secret = real
    gone = not hasattr(WebOperator, "_env_value")
    ok = typed == [w.value] and seen == ["secret:instance:///devices/alpha/0/.env#TOKEN"] and gone
    check(PROVES["060d2146618c"]["6"], ok,
          f"typed_right={typed == [w.value]} read_through_secret={seen} env_value_gone={gone}")


def main() -> int:
    teeth = (tooth_1, tooth_2, tooth_3, tooth_4, tooth_5, tooth_6)
    w = World()
    for t in teeth:
        try:
            t(w)
        except Exception as exc:  # noqa: BLE001
            msg = f"{type(exc).__name__}: {exc}"
            check(PROVES["060d2146618c"][t.__name__.split("_")[1]], False,
                  msg.replace(w.value, "<THE VALUE LEAKED>"))
    w._d.cleanup()
    print(f"{6 - len(FAILURES)} passed, {len(FAILURES)} failed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
