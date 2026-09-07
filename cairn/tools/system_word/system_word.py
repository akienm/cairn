"""system_word — the case-fold for a SYSTEM WORD, living in exactly one place.

A system word is a token the system owns: a device name, a verb, a view name, a status
word, a signal, a stage token, a marker, a flag. Akien, 2026-09-07 (decision
``2026-09-07-system-words-are-case-insensitive-when-akien-types-them``): *"everywhere we're
talking a status word, or a command word, or any similar 'system word' it should be case
insensitive if there's any chance of it coming from me."* The one exception he named is the
``cairn`` command itself, which the shell resolves and which stays lowercase — that is the
file's name, not a word this module ever sees.

THE RULE IS ONE LINE AND THIS MODULE IS WHERE IT IS WRITTEN (Law 1). Before today every
seam compared his token by bytes — ``verb == "list"``, ``views.get(what)``, ``cmd not in
COMMANDS``, ``\\bRULED\\b`` — nineteen re-derivations of "these bytes are the word", and
the ruling machine's marker was the one that bit him: he typed ``ruled`` and the packet
landed unconfirmed. A seam now calls ``fold``/``is_word``/``pick`` and the rule cannot
drift per seam.

WHAT IS NEVER FOLDED, stated because it is the wrong-intent edge of the whole ticket: FREE
TEXT. His review words, a ruling's verbatim, a learn query, a codemother question, a
proof's argv after the verb — those are HIS BYTES and they land byte-identical. ``fold_head``
exists so a CLI folds exactly the ``n`` leading system words and hands the rest through
untouched; ``fold_flags`` folds only tokens that lead with ``-``. Nothing here walks a
sentence. A stored status token keeps the case it was stored with: folding is a COMPARE,
not a rewrite, so a ticket's ``[BUILDME]`` on disk never changes because he typed
``buildme``.

``casefold`` rather than ``lower`` because it is the compare Python defines for
case-insensitive matching (``ß`` == ``SS``); ``strip`` because a trailing space is the other
thing his fingers produce. A non-string token is rendered with ``str`` rather than raising:
a fold that crashes inside a dispatcher fails the whole command over an int.

IT HOLDS NO STATE and consults nothing (it is a tool, Law 6: users, not an owner).
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, TypeVar

_V = TypeVar("_V")


def fold(token: Any) -> str:
    """The canonical form of a system word: stripped, case-folded."""
    return str(token).strip().casefold()


def is_word(token: Any, *words: Any) -> bool:
    """Is ``token`` one of ``words``, compared as system words?"""
    key = fold(token)
    return any(fold(w) == key for w in words)


def canon(token: Any, table: Iterable[Any]) -> Any | None:
    """The entry of ``table`` that ``token`` names, in the TABLE's own spelling — or None.

    This is what a seam stores or echoes downstream: the system's spelling of the word,
    never his. A dict is iterated by key, so a verb table's key comes back."""
    key = fold(token)
    for entry in table:
        if fold(entry) == key:
            return entry
    return None


def pick(token: Any, table: Mapping[Any, _V]) -> _V | None:
    """``table[token]`` with the lookup folded — None when no key matches."""
    entry = canon(token, table)
    return None if entry is None else table[entry]


def fold_head(argv: Iterable[Any], n: int) -> list:
    """Fold the first ``n`` tokens of ``argv``; everything after rides through verbatim.

    ``n`` is the number of leading SYSTEM WORDS a CLI takes before free text begins:
    ``cairn review <id> "his words"`` is ``n=1`` at the review door. Tokens beyond ``n``
    are returned as the very objects passed in, not copies through ``str``."""
    out = list(argv)
    for i in range(min(max(n, 0), len(out))):
        out[i] = fold(out[i])
    return out


def fold_flags(argv: Iterable[Any]) -> list:
    """Fold only the tokens that lead with ``-`` (``--SEAL`` -> ``--seal``); the rest —
    positional paths, free text — ride through verbatim. For argparse doors."""
    out = list(argv)
    for i, tok in enumerate(out):
        if isinstance(tok, str) and tok.startswith("-") and tok != "-":
            out[i] = fold(tok)
    return out
