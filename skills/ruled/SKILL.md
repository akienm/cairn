---
name: ruled
description: Akien's RULED marker fires the ruling door — /ruled <id> confirms, bare /ruled lists open unmarked, /ruled <no-match> refuses loudly.
---

# /ruled — his marker's front door

`/ruled <id>` confirms the named ruling packet, recording the invocation as
evidence. Bare `/ruled` lists open unmarked rulings. `/ruled <no-match>` refuses
loudly, naming the store searched.

The skill wraps `cairn/machines/ruling/ruling.py`'s existing `confirm`,
`open_rulings`, and `verify` functions. It creates no new intake, no new store,
and no new confirmation authority.

## Usage

    cairn ruled <id>         confirm the ruling; show verify result
    cairn ruled              list open unmarked rulings
    cairn ruled <no-match>   loud refusal naming the store

## Charter

`skills/ruled/intention+why.json`
