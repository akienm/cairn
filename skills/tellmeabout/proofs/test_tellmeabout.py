"""Proof for skills/tellmeabout — Akien's dereference door. Teeth a hollow build
could not pass, asserted as INVARIANTS over the live stores (never snapshots —
a check that goes red the moment its condition is satisfied is the known trap):

  - VERBATIM OR NOTHING: a resolved finding's record is EQUAL to the store's own
    record, read independently of the resolver — a presentation that reworded,
    trimmed, or summarized anything fails equality. Same for a resolved ticket
    against json.load of its own file. (The finding under test is picked
    dynamically — whichever stands pending oldest — so the tooth holds whatever
    Akien has answered by the time it runs.)
  - A UNIQUE PREFIX RESOLVES: an id prefix unique across the whole trace store
    finds its one finding; the tooth computes uniqueness itself.
  - AMBIGUITY REFUSES BY LISTING: 'orient' (a name two rungs answer to — the
    measured precedent this discipline was founded on) refuses with >= 2 matches,
    every listed address a real file on disk, and both known rungs listed.
  - NOT-FOUND NAMES EVERY STORE: a nonsense token returns not_found with all six
    stores named, each carrying an address.
  - READ-ONLY IS MEASURED, NOT PROMISED: every store file's (path, mtime, size)
    is snapshotted before and after the full battery — one byte moved anywhere
    is a red. The snapshot-compare is the invariant; the values are free to be
    anything, they must only be UNCHANGED.
  - EXACTLY ONE SHAPE: every resolve returns exactly one of found / refused /
    not_found — never two keys, never zero.

    python3 skills/tellmeabout/proofs/test_tellmeabout.py     # exit 0 = green
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills.tellmeabout.tellmeabout import resolve, _stores_searched, COMMONS, LAB  # noqa: E402
from cairn.machines.learning_block import learning_block as lb  # noqa: E402

PASS, FAIL = 0, 0


def tooth(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def snapshot_stores() -> dict:
    """(path -> (mtime_ns, size)) over every file in every presented store."""
    snap = {}
    roots = [lb.trace_root(), COMMONS / "tickets", COMMONS / "troubles",
             COMMONS / "decisions", COMMONS / "ideas", LAB]
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file():
                st = p.stat()
                snap[str(p)] = (st.st_mtime_ns, st.st_size)
    return snap


def one_shape(got: dict) -> bool:
    return sum(k in got for k in ("found", "refused", "not_found")) == 1


def main() -> int:
    before = snapshot_stores()

    # ── verbatim-or-nothing over a pending finding, picked dynamically ──
    pend = lb.pending_findings()
    if pend:
        fid = pend[0]["id"]
        got = resolve(fid)
        tooth("pending finding resolves as found", one_shape(got) and "found" in got,
              json.dumps(got)[:200])
        if "found" in got:
            store_rec = next(
                (r for path in sorted(lb.trace_root().glob("*.jsonl"))
                 for r in lb.read_trace(path.stem)
                 if r.get("event") == "finding" and r.get("id") == fid), None)
            tooth("finding record EQUAL to the store's own record (verbatim tooth)",
                  got["found"]["record"] == store_rec)
            tooth("finding carries its waiting act (recordverdict named with the id)",
                  fid in got["found"]["waiting_on"]
                  and "recordverdict" in got["found"]["waiting_on"])
            tooth("finding carries its address (a real file)",
                  os.path.isfile(got["found"]["address"]))
    else:
        tooth("pending finding resolves as found", False,
              "no pending findings anywhere — cannot exercise the primary case")

    # ── a unique prefix resolves to its one finding ──
    all_ids = [r.get("id") for path in sorted(lb.trace_root().glob("*.jsonl"))
               for r in lb.read_trace(path.stem) if r.get("event") == "finding"]
    prefix = next((i[:8] for i in all_ids
                   if isinstance(i, str) and sum(1 for j in all_ids
                                                 if isinstance(j, str) and j.startswith(i[:8])) == 1),
                  None)
    if prefix:
        got = resolve(prefix)
        tooth("a unique 8-char prefix resolves", "found" in got and
              got["found"]["id"].startswith(prefix), json.dumps(got)[:200])
    else:
        tooth("a unique 8-char prefix resolves", False, "no unique prefix computable")

    # ── ambiguity refuses by listing ──
    got = resolve("orient")
    tooth("'orient' refuses (two rungs answer)", one_shape(got) and "refused" in got,
          json.dumps(got)[:200])
    if "refused" in got:
        addrs = [m["address"] for m in got["matches"]]
        tooth("refusal lists >= 2 matches, all real files",
              len(addrs) >= 2 and all(os.path.isfile(a) for a in addrs))
        tooth("both known rungs listed (tool and machine)",
              any("cairn/tools/orient/" in a for a in addrs)
              and any("machines/orient/" in a for a in addrs))

    # ── not-found names every store ──
    got = resolve("zzz-proof-token-that-names-nothing-zzz")
    tooth("nonsense token is not_found", one_shape(got) and "not_found" in got)
    if "not_found" in got:
        tooth("all six stores named in the search report",
              len(got["stores_searched"]) == len(_stores_searched()) == 6)

    # ── a ticket resolves verbatim (picked dynamically: unique stems only) ──
    ticket_stem = None
    for p in sorted((COMMONS / "tickets").glob("*.json")):
        if len([m for m in (resolve(p.stem).get("matches") or [None])]) <= 1 \
                and "found" in resolve(p.stem):
            ticket_stem = p.stem
            break
    if ticket_stem:
        got = resolve(ticket_stem)
        with open(COMMONS / "tickets" / f"{ticket_stem}.json", encoding="utf-8") as fh:
            tooth("ticket record EQUAL to json.load of its own file",
                  got["found"]["record"] == json.load(fh))
    else:
        tooth("ticket record EQUAL to json.load of its own file", False,
              "no unambiguous ticket stem found — store empty?")

    # ── every shape is exactly one shape ──
    battery = ["d4896172aa8c", "orient", "no-such", "", "tellmeabout"]
    tooth("every resolve returns exactly one of found/refused/not_found",
          all(one_shape(resolve(t)) for t in battery))

    # ── read-only, measured ──
    after = snapshot_stores()
    tooth("no store file changed under the whole battery (read-only measured)",
          before == after,
          f"{len(set(before) ^ set(after))} paths differ" if before != after else "")

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
