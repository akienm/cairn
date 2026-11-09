"""cairn/tools/dataref/dataref.py — one address for any stored value, and a Secret that prints as stars.

Outline 17.28; ticket 060d2146618c. Akien 2026-11-09, on CC0AC-Weather's ``file:secrets.env#KEY``:
"it looks like the perfect way to do file pointers for everything", and then "a class. it's
__str__ would return ********** but it's .secret would return the value fetched from the file."

THE ADDRESS. The scheme names the root, the path finds the record, and the part after ``#`` finds
the item inside it (17.28.1):

    cairn:///conf/a.ini#web/port              the repo
    cairncommons:///tickets/x.json#title      the commons repo beside it
    instance:///devices/cc/0/.env#githubtoken ~/.cairn
    claude:///settings.json#model             ~/.claude
    file:///etc/hosts                         a real path, for what no root holds
    secret:instance:///devices/cc/0/.env#KEY  any whole address, handed back as a Secret

The three Cairn roots ARE ``cairn.tools.base.address.ROOTS`` and resolve through its ``resolve``,
so there is still one root table and the rooted-token face (``instance/devices/...``) and this
one cannot drift: the proof pins them equal. ``claude`` is added here, derived from the home
directory the same way ``instance`` is, never configured. ``address.py`` never touches disk and
takes no position; this module reads, so it lives above it, not inside it.

THE ITEM. ``#key`` in an env file (``NAME=value``, ``export`` and quotes taken off), ``#section/key``
in an ini file (interpolation off: a % is just a %), ``#a/b/c`` into json (a list index is a
number). No ``#`` gives the whole text. The format comes from the suffix: ``.json``; ``.ini``,
``.cfg``, ``.conf``; anything else is env lines.

READ-ONLY (17.28.3). Nothing here writes. ``db:`` is read through db_domain's own client and a
host (``cairn://akiendell/...``) over the bus; neither is built yet, and both refuse loudly by
name rather than falling back to something that would read the wrong copy.

THE CACHE (17.28.4). A Dataref keeps its file's text and re-reads it only when the stat stamp
(inode, size, mtime_ns) moves; a stat reads no data, and an atomic replace gets a new inode where
timestamps are coarse. A same-size, same-mtime_ns rewrite in place goes unseen, and that is the
accepted edge. ``reads`` counts the real reads. HYPOTHESIS: the cache pays; the reads are what a
metric (17.27) will count to find out. A Secret keeps nothing between reads.

A MISS IS LOUD (17.28.5, Law 7). Every failure is a ``DatarefMiss`` naming the address and what
was missing, never a value: parser errors that quote the file's lines are replaced, never chained.
"""
from __future__ import annotations

import configparser
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from cairn.tools.base.address import ROOTS, resolve

MASK = "**********"
SECRET_PREFIX = "secret:"
CLAUDE = Path.home() / ".claude"
SCHEMES = {"cairn": "repo", "cairncommons": "commons", "instance": "instance", "claude": "claude"}
NOT_YET = {"db": "db: is read through db_domain's own client (outline 17.28.3), which is not built yet"}
INI = {".ini", ".cfg", ".conf"}
_DRIVE = re.compile(r"^/[A-Za-z]:")


class DatarefMiss(LookupError):
    """An address that does not resolve to a value. The message names the address, never a value."""

    def __init__(self, address: str, why: str) -> None:
        super().__init__(f"{address}: {why}")
        self.address = address


def _table(roots: dict[str, Path] | None) -> dict[str, Path]:
    return {**ROOTS, "claude": CLAUDE, **(roots or {})}


def _locate(inner: str, roots: dict[str, Path] | None, address: str) -> tuple[Path, list[str]]:
    """inner address -> (the file, the item's names). Touches no disk. A miss names ``address``,
    the address as its caller wrote it (``secret:`` and all)."""
    parts = urlsplit(inner)
    scheme = parts.scheme.lower()
    if scheme in NOT_YET:
        raise DatarefMiss(address, NOT_YET[scheme])
    if parts.netloc:
        raise DatarefMiss(address, f"names host {parts.netloc!r}; another box's copy is read over the bus "
                                   "(outline 17.28.1.2), which is not built yet")
    item = [n for n in parts.fragment.split("/") if n] if parts.fragment else []
    if scheme == "file":
        path = parts.path
        if _DRIVE.match(path):
            path = path[1:]
        if not Path(path).is_absolute():
            raise DatarefMiss(address, "a file: address is a whole path (file:///...); a relative one "
                                       "would mean something different in every working directory")
        return Path(path), item
    if scheme not in SCHEMES:
        raise DatarefMiss(address, f"scheme {scheme!r} is not one of {sorted([*SCHEMES, 'file'])}")
    return resolve(f"{SCHEMES[scheme]}/{parts.path.lstrip('/')}", _table(roots)), item


def _env(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip().removeprefix("export ").strip()] = v.strip().strip("'\"")
    return out


def _pick(address: str, path: Path, text: str, item: list[str]) -> str:
    if not item:
        return text
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            node = json.loads(text)
        except ValueError:
            raise DatarefMiss(address, "the file is not valid json") from None
        for i, name in enumerate(item):
            here = "/".join(item[:i + 1])
            if isinstance(node, dict) and name in node:
                node = node[name]
            elif isinstance(node, list) and name.isdigit() and int(name) < len(node):
                node = node[int(name)]
            else:
                raise DatarefMiss(address, f"no {here!r} in the json")
        return node if isinstance(node, str) else json.dumps(node)
    if suffix in INI:
        if len(item) != 2:
            raise DatarefMiss(address, "an ini item is #section/key")
        cp = configparser.ConfigParser(interpolation=None)
        try:
            cp.read_string(text)
        except configparser.Error:
            raise DatarefMiss(address, "the file is not a readable ini") from None
        if not cp.has_option(item[0], item[1]):
            raise DatarefMiss(address, f"no key {item[1]!r} in section {item[0]!r}")
        return cp.get(item[0], item[1])
    if len(item) != 1:
        raise DatarefMiss(address, "an env item is #KEY")
    values = _env(text)
    if item[0] not in values:
        raise DatarefMiss(address, f"no key {item[0]!r}")
    return values[item[0]]


def _read(address: str, path: Path) -> tuple[str, tuple[int, int, int]]:
    try:
        st = path.stat()
        return path.read_text(encoding="utf-8"), (st.st_ino, st.st_size, st.st_mtime_ns)
    except FileNotFoundError:
        raise DatarefMiss(address, f"no file at {path}") from None
    except (OSError, UnicodeDecodeError) as e:
        raise DatarefMiss(address, f"cannot read {path}: {type(e).__name__}") from None


class Dataref:
    """A read-only pointer to a stored value. ``str()`` and ``.value`` give the value."""

    def __init__(self, address: str, roots: dict[str, Path] | None = None) -> None:
        self.address = address
        self.reads = 0
        self._stamp: tuple[int, int, int] | None = None
        self._text: str | None = None
        if address.startswith(SECRET_PREFIX) and type(self) is Dataref:
            raise DatarefMiss(address, "is a secret: address; read it through Secret (or ref()), "
                                       "so it cannot print")
        self.path, self._item = _locate(self._inner(), roots, address)

    def _inner(self) -> str:
        return self.address

    def _fetch(self) -> str:
        try:
            st = self.path.stat()
            stamp = (st.st_ino, st.st_size, st.st_mtime_ns)
        except OSError:
            stamp = None
        if stamp is None or stamp != self._stamp or self._text is None:
            self._text, self._stamp = _read(self.address, self.path)
            self.reads += 1
        return _pick(self.address, self.path, self._text, self._item)

    @property
    def value(self) -> str:
        return self._fetch()

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.address!r})"


class Secret(Dataref):
    """A Dataref that cannot show itself: str, repr, format and .value are all stars.

    ``.secret`` reads the value at that moment and keeps nothing; every place a secret is unmasked
    is a ``.secret`` anyone can grep for. It cannot be pickled, and json.dumps refuses it because
    it is not a str.
    """

    def __init__(self, address: str, roots: dict[str, Path] | None = None) -> None:
        if not address.startswith(SECRET_PREFIX):
            address = SECRET_PREFIX + address
        super().__init__(address, roots)

    def _inner(self) -> str:
        return self.address[len(SECRET_PREFIX):]

    @property
    def secret(self) -> str:
        text, _ = _read(self.address, self.path)
        self.reads += 1
        return _pick(self.address, self.path, text, self._item)

    @property
    def value(self) -> str:
        return MASK

    def __str__(self) -> str:
        return MASK

    def __repr__(self) -> str:
        return f"Secret({self.address!r}: {MASK})"

    def __format__(self, spec: str) -> str:
        return format(MASK, spec)

    def __reduce_ex__(self, protocol):
        raise TypeError(f"a Secret is not pickled: {self.address}")

    def __getstate__(self):
        raise TypeError(f"a Secret is not pickled: {self.address}")


def ref(address: str, roots: dict[str, Path] | None = None) -> Dataref:
    """The one door: a ``secret:`` address is a Secret, anything else a Dataref."""
    return Secret(address, roots) if address.startswith(SECRET_PREFIX) else Dataref(address, roots)


__all__ = ["CLAUDE", "MASK", "Dataref", "DatarefMiss", "Secret", "ref"]
