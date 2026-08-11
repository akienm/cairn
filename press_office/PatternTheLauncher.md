# Pattern — The self-starting launcher

### From parse to exec, nothing may abort — and a diagnostic that needs a second run has already failed

> **The move.** The entry point that starts your tooling also **brings up the floor that tooling
> stands on**, and hands the session a report of whatever it could not fix. It is *silent when
> everything works.* Its prime directive outranks its own checks: a broken preflight still
> delivers the tool to a broken machine, because the tool is what you rebuild the machine with.
> And because "reported" is not "fixed," a probe watches whether the same finding rides in launch
> after launch.

---

## 1. The measured failure

**An import that worked by accident.** The project's Python package imported successfully — from
the repository root, because the current directory happened to be there. From anywhere else it
did not. Worse, the packaging file carried a standing promise that an editable install *"stays
green at all times,"* and the host's package manager **refused that install outright** under a
policy that had been in force for years. The promise could not have been true on the machine
where it was written, and nothing said so.

**A launcher that carried the logic but not the why.** The predecessor system's launcher
contained a context-size toggle whose logic was correct and whose *intent* was written nowhere.
On first contact it was reverse-engineered **backwards** — the flag read as doing the opposite of
what it did. Real work was spent on that.

That failure has a general shape and it is the founding case for this entire project's naming
convention: **the intent and the why belong at the address, and their absence has a measurable
cost.**

**A finding that named a cause it had not measured.** The preflight's venv-creation check
asserted that a failure was *"usually the missing ensurepip package."* The actual error was a
missing parent directory. A confident wrong cause is worse than silence, because the reader stops
looking.

**And the failure this pattern's probe exists for.** A diagnostic that reports the same unfixable
thing every launch stops being read. *"The tool is invisible when it works"* degrades quietly
into *"the tool is ignored."* No proof can catch that, because nothing is broken — a human simply
learned to scroll past.

---

## 2. The pattern

### 2.1 The prime directive: nothing may abort

**From parse to exec, nothing may abort.** Always reach the tool, so it can help rebuild a broken
box.

The consequences are structural, not aspirational:

- The floor script is **sourced**, so it sets no shell error flag — that would leak into the
  caller's shell and let one failed probe kill a launch.
- **Every function returns a code; none exit.**
- **The prime directive outranks the floor.** A broken preflight still delivers the tool.

This is the inversion that makes the pattern work. Ordinary preflight logic says *"verify the
environment, then run."* This says **"run regardless; report what you could not fix."** For a tool
whose job is fixing environments, refusing to start on a bad environment is precisely backwards.

### 2.2 The report rides into the session, and is complete on the first pass

What could not be fixed is appended to the session's own context, and written to a log.

**Each finding carries what a fixer needs on the *first* report** — the probe that ran, the
measured output, and a repair. Not a summary, not a pointer to "run with verbose." A diagnostic
that forces a second run to gather more **has failed at its job**, and re-running to gather more
is the defect this rule names.

And the other half, which is what keeps it readable:

> **Silent when the floor is up.** The tool is invisible when it works and speaks only when there
> is something to fix.

A preflight that prints a reassuring green wall every launch is a preflight nobody reads on the
day it matters.

### 2.3 A finding never names a cause it did not measure

The corrected form: **the measured output leads; candidate causes follow it, named as
candidates.** A hint is allowed to guess. A finding is not allowed to assert.

This is the same discipline as the rest of the system — an unmeasured claim is labelled a
hypothesis — applied at the one surface where a wrong guess costs someone an hour of chasing the
wrong thing.

### 2.4 Clean floor over convenient floor

The floor builds an isolated environment in instance space, never in the repository. **A thing
that would need to be excluded from version control is a thing in the wrong place** — that is the
general tell, and a virtual environment is machine-specific compiled bytes, which is runtime
state.

Borrowing the host's already-installed packages was considered and **refused**, even though it
would make an offline rescue cheaper. Two reasons, and the first is the important one:

- It makes the floor's contents **a function of what the box happens to have** — which is the
  exact hypothesis that produced the original defect.
- Mixing two variants of the same driver package in one namespace is a known shadowing hazard.

**Verification is a real import, not a stamp.** A matching stamp over a broken environment is a
lie. The stamp gates only the expensive rebuild. Warm verification costs about **90 ms**; a cold
build costs about **6 s**, once.

### 2.5 The launcher's own settings live in code, with their why

A launch is reproducible because its contract is a file, not someone's shell history. The
context-size switch is the worked example, and it is instructive because **the default is a
safety property rather than a preference:**

The tool cannot trigger its own context compaction. At the largest context size, a session
balloons past the point where the human would be notified *before* he is notified. So defaulting
to the smaller size makes stewardship **a system property rather than something to remember** —
and the flag always overrides it, so the capability is never taken away.

Precedence is stated explicitly: **command line > environment > file default > unconstrained.**

Two details worth stealing:

- **The disable variable must be *unset*, not set to zero.** Setting it to zero is a no-op that
  looks like it worked — the failure mode where the fix and the non-fix are indistinguishable.
- **The documented behaviour and the measured behaviour differ**, and the file says so, with the
  measurement and with instructions for what to change *if it ever bites* — and explicitly not
  before. Measure; do not pre-engineer.

### 2.6 The probe watches the half no proof can reach

The repair half is provable. **The reporting half is a bet on a human-and-model loop**, and it
gets a probe instead.

The probe's question: *does a floor this seam reported but could not fix actually get fixed?* It
fires when at least five launches have reported something **and** some finding has survived at
least three separate launches — the same finding text recurring across different process ids
**is** the measurement.

Three reading rules, and the sharpest one is last:

| Signal | What it means |
|---|---|
| the same finding, many launches | reported and not fixed |
| the repair beginning twice for one cause | a repair that is not repairing |
| **the preflight bypassed** | **someone routed around the floor check** — it got broken enough to be in the way |

And the design detail that makes it honest: **the recorder is sourced outside the preflight
branch**, so the bypass hatch is recorded too. Recording only the launches that took the happy
path would make the probe blind to precisely its own failure mode.

**One bypass is a legitimate rescue** — that is what the hatch is for — so it rides as carried
data rather than as the firing predicate.

### 2.7 The last line is `exec`

The final log entry before the shell is replaced is the resolved command, rendered so it can be
pasted back and re-run.

Which gives a free invariant: **a boot log whose last entry is not `exec` is a defect with a
timestamp on it.**

---

## 3. How it is enforced

**Physics today:**

- The floor is measured **by importing from a directory that is not the repository root** — the
  exact condition that used to make the accident look like success.
- A broken preflight is measured **still reaching `exec`** with its report attached.
- A working preflight is measured adding **nothing** to the launch line.
- Non-vacuity is checked rather than assumed: pointed at an unrepairable path, the proof fails
  with exactly the four expected cases failing.
- The recorder's wiring is measured in four states — warm, cold, unfixable, and **logger
  entirely absent**. With the logger removed the launch is unchanged, which is the property that
  keeps the recorder from ever becoming load-bearing.
- The finding that once asserted an unmeasured cause has a **regression case pinning the
  corrected shape**.

**Still prose (tracked as debt):**

- The preflight covers the import root and the one verb. **Verifying the other host seams** — the
  database, the privileged-operation relay, the sandbox — is a later rung the shape accommodates
  and does not yet reach.
- This is a **host seam**: its implementation lives where version control cannot see it, so its
  seal *expires* as the machine drifts with nothing in the repository changing. That is a
  permanent property, not a bug to close.

---

## 4. What it costs

**Roughly 7 ms and eight log appends per launch**, measured: a warm launch went from 123 ms to
130 ms. A cold build of the floor from nothing takes 6.0 s, with every repair step recorded. An
unfixable floor costs 78 ms, records two unfixed findings, **and still reaches `exec`.**

**The bypass hatch is a real hole,** and it must be. `--no-preflight` exists so the floor check
can never be the reason a rescue fails — which means the check can always be skipped. The
mitigation is not to close it but to **record every use of it.**

**Never-fatal is harder to write than fail-fast.** No error flag, every function returning rather
than exiting, and a subtle trap discovered the hard way: the general-purpose command logger runs
its argument in a pipeline, therefore a subshell. Wrapping a state-mutating shell function in it
**silently discarded the findings list and left the report empty** — a logging tool erasing the
thing being logged. The rule that came out of it: real subprocesses get the wrapper; shell
functions that mutate state get a note at their decision points.

**The launcher stays lean on purpose.** None of the predecessor's terminal-multiplexer, wizard,
or credential machinery was carried over. It is added only if a measured need appears.

---

## 5. What would falsify this

- **A launch fails to reach the tool.** The prime directive broken; everything else is
  secondary.
- **A boot log's last entry is not `exec`.**
- **The preflight speaks when the floor is up.** Noise on the happy path is how a diagnostic
  becomes wallpaper.
- **A finding asserts a cause it did not measure.** The corrected failure, returning.
- **A finding forces a second run to gather more.** Complete-on-the-first-pass broken.
- **The recorder becomes load-bearing.** Remove it entirely and the launch must be unchanged.
- **The probe fires and nothing happens.** If the same finding rides in for a fourth, fifth, tenth
  launch after the probe has said so, then the reporting loop does not close, and *"invisible when
  it works"* has become *"ignored."* That is the falsifier for the whole reporting half.
- **A default moves without a measurement.** Defaults here are gates, and a gate moves on evidence
  or not at all.

---

## 6. What is built, and what is red

**Built.** The launcher and its floor script, with the never-fatal contract proved. **14 proof
cases**, including the import-from-elsewhere measurement and the broken-preflight-still-launches
measurement. The recorder in four measured states. The reported-but-unfixed probe, armed, with
its own proof. A dry-run mode that resolves and prints the launch without performing it.

**Red.**

- **Only two host seams of several are covered** by the preflight.
- **The seal expires with the machine.** Host seams cannot be pinned by version control; the
  recipe is replayable and the verification re-runnable, which is the best available and is not
  the same as green.
- **The probe's first live fire found the test suite, not the world.** It reported a floor unfixed
  through twelve launches — and the finding was the proof harness's *own fixture*, written twelve
  times because the harness inherited the environment and the floor script writes to a path an
  environment variable controls. The harness now owns its namespace, and the containment tooth is
  **structural** — every child goes through one environment function — because the first version
  grepped for one remembered fixture string and missed six records from a different fixture in the
  same file.

  That is the honest state: **the probe has fired once, and what it caught was us.**

---

*Pattern document, `press_office/PatternTheLauncher.md`. Part of the Cairn pattern series; the
spine is [`CairnArchitecture.md`](CairnArchitecture.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11.*
