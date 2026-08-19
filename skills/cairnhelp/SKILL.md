---
name: cairnhelp
description: List all Cairn skills with their names and one-line descriptions — the discovery surface for "what can I ask you to do?"
---

# /cairnhelp — what's available

Print every installed Cairn skill with its name and description.
No arguments needed. Read-only — writes nothing, gates nothing, crosses nothing.

## Do this

Read the SKILL.md frontmatter (the `name:` and `description:` fields) from every
skill directory in both roots:

- `~/dev/src/cairn/skills/*/SKILL.md`
- `~/.claude/skills/*/SKILL.md`

Deduplicate by name (same skill installed in both roots counts once).
Print them sorted by name, one per line:

    /name — description

Group by purpose if it helps readability:

- **Workflow** — the steps of getting work done: idea → intent → sorted → chart → sail → commit → saveslate
- **Research** — tellmeabout, moreabout, whatslefttodo
- **Quality** — challenge, design
- **Capture** — note, idea
- **This** — cairnhelp

That's it. No analysis, no recommendations, no routing. The list IS the output.
