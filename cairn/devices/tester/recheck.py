"""The tester rechecks its own seal troubles (ticket 17b087f2483f).

``cairn cleanup`` ends every voyage, and until this module it rechecked only the inspector's
finding troubles (ticket 95557c2ed44f). Measured 2026-11-18 at the akiendelllinux house: of 24
live troubles, 7 of 7 ``red-tickets-held-red-*`` named a proof that was sealed green with its
fingerprint matching, and 2 of 4 ``seal-red-*`` named a proof file that no longer existed. Both
kinds are the tester's (``validation_store``'s announce, ``red_tickets._hold``), so the tester
rechecks them; the clear is an EMISSION and the trouble device's drain folds it (Law 6). The
tester never writes the trouble store.

THE PROOF IS RECOVERED FROM THE IDENTITY ALONE. The live records carry no detail, so each proof
file under ``proof_roots`` is indexed by the identity its trouble would carry: the seal key
``seal_trouble_identity(proof)`` and the held key, the trouble slug of
``red_tickets:held:red:<rel>`` (``red_keys`` writes ``red:<rel>::<tooth>``). A held identity
carries a tooth after the path, so it matches by prefix; the longest prefix wins.

THE PREDICATE IS THE STORE'S OWN DOOR. A trouble clears when no proof file matches (the proof is
gone) or ``validation_store.standing(proof)["proven"]`` is True (sealed green, fingerprint
matching). Anything else stands and is reported; an identity of neither kind is ``unknown``."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SLUG = re.compile(r"[^a-z0-9-]+")
SEAL, HELD = "seal-red-", "red-tickets-held-red-"


def _slug(s: str) -> str:
    """The trouble store's addressing rule (``TroubleDevice.identity_of``), so an index key and
    a stored identity compare as the store compares them."""
    return _SLUG.sub("-", s.strip().lower()).strip("-")


def _rel(p: Path) -> str:
    """Repo-relative inside the repo, absolute outside it — ``seal_trouble_identity``'s rule."""
    full = p.resolve()
    try:
        return full.relative_to(_REPO).as_posix()
    except ValueError:
        return str(full)


def _index(proof_roots) -> tuple[dict, list]:
    from cairn.tools.validation_store.validation_store import seal_trouble_identity
    seal, held = {}, []
    for root in proof_roots:
        for p in Path(root).rglob("*.py"):
            if p.parent.name != "proofs" or ".git" in p.parts:
                continue
            seal[seal_trouble_identity(p)] = p
            held.append((_slug(f"red_tickets:held:red:{_rel(p)}"), p))
    held.sort(key=lambda kp: -len(kp[0]))
    return seal, held


def _proof_for(identity: str, seal: dict, held: list):
    if identity.startswith(SEAL):
        return True, seal.get(identity)
    if identity.startswith(HELD):
        for key, p in held:
            if identity == key or identity.startswith(key + "-"):
                return True, p
        return True, None
    return False, None


def recheck(identities, *, proof_roots=None, raiser=None) -> dict:
    """Clear each named seal trouble whose proof is proven or gone; report the rest."""
    from cairn.tools.validation_store.validation_store import standing
    seal, held = _index(proof_roots or [_REPO])
    cleared, still, unknown = [], [], []
    for identity in sorted({_slug(i) for i in identities if i}):
        mine, proof = _proof_for(identity, seal, held)
        if not mine:
            unknown.append(identity)
            continue
        if proof is None:
            why = "no proof file under the recheck's roots carries this identity: the proof is gone"
        elif standing(str(proof)).get("proven"):
            why = f"{_rel(proof)} is sealed green and its fingerprint matches (validation_store.standing)"
        else:
            still.append(identity)
            continue
        if raiser is None:
            from cairn.tools.base.diagnostic import ModuleRaiser
            raiser = ModuleRaiser("tester")
        raiser.clear_trouble(identity, by="cc", what_changed=f"cairn cleanup recheck: {why}")
        cleared.append(identity)
    return {"cleared": cleared, "standing": still, "unknown": unknown}


def main(argv: list[str]) -> int:
    print(json.dumps(recheck(argv), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
