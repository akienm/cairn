---
name: ruled
description: RETIRED 2026-09-14 (ticket 9adc6fddf185) — rulings are questions in Akien's inbox now; every /ruled mode refuses and points at `cairn question`.
---

# /ruled — RETIRED

Akien, 2026-09-14: *"why are we still doing rulings? we replaced that with questions
that would show up in my inbox."* (ticket `9adc6fddf185`). A decision he has to make
is a **question bound to the ticket that needs it**, and his answer is the decision:

    cairn question open --ticket <id> "<question?>" --why "<what the build cannot settle without it>"
    cairn question answer <qid> "<his words>" --spawned none | --spawned "<q?>"
    cairn question list [<ticket>]

The ticket does not cross to BUILDME while a question on it stands open
(`the_ticket_has_every_answer_it_needs`). `CairnCommons/decisions/` stays a
read-only, citable record; nothing opens or confirms a ruling any more, so every
mode of this skill (`/ruled`, `/ruled <id>`, `cairn ruled`) exits 2 with the pointer
above. The directory stays so the retirement is readable at its own address.

## Charter

`skills/ruled/intention+why.json`
