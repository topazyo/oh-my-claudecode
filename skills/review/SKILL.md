---
name: omc-review
description: Evaluate finished work for defects, risk, and simplification before it ships
---

# Review

Use this skill to evaluate work that already exists. Review never authors the
change it is judging.

This is the canonical review workflow. `ai-slop-cleaner` is an opt-in lane
within it.

## Goal
Find what is actually wrong, ranked by severity, with enough detail to act on.

## Workflow
1. Establish what changed and what it was meant to do.
2. Read the change against that intent.
3. Check correctness first, then risk, then simplification.
4. Verify each candidate finding before reporting it.
5. Report findings most-severe first.

## What to check
- **Correctness** — logic defects, edge cases, error paths, concurrency
- **Risk** — security boundaries, destructive operations, data integrity
- **Reuse** — existing utilities or patterns the change should have used
- **Simplification** — code that could be deleted or collapsed
- **Coverage** — behavior that ships untested

## Two axes, run apart

A substantial diff is reviewed as two parallel sub-agent passes, reported separately — never merged or cross-ranked, because a change can pass one axis and fail the other (standards-conforming but wrong behavior; faithful but convention-breaking):

- **Standards axis** — the diff against the repo's documented standards plus a judgement-call-only smell baseline; anything tooling already enforces is skipped. The standards set is discovered, not assumed: search the repo for standards documents (CLAUDE.md/AGENTS.md, `docs/standards/` volumes, `CONTRIBUTING.md`, `CODING_STANDARDS.md` or equivalents) and review against whatever exists — a standards file you didn't look for is a standard you didn't apply.
- **Intent axis** — the diff against what the work was meant to do — the task, spec, or ticket acceptance criteria: requirements missing or partial, behavior nobody asked for, each finding quoting its source line.

Keep each sub-agent brief under ~400 words and pointed at one axis. Aggregate without picking a single winner across axes — that reranking is what the separation exists to prevent; state each axis's verdict on its own. A small diff stays one pass.

## Multi-agent audits (fan-out + refutation)
When a review fans out to several sub-agents and then runs a refutation pass:
- **Never re-type a finding.** Extract each sub-agent's report verbatim from `subagents/agent-*.jsonl` (its hand-back message) by script, and build critic inputs and report rows from those files, not from memory.
- **Shard refutation by severity, not topic.** Critical/High and traced-only rows go to a re-executing shard on the strongest model. Medium/Low/Nit rows go to a re-read shard with an explicit cheaper `model`, and their status label matches that effort.
- **Launch the longest-running track first**, so its critic is not the critical path.
- **Bound every sub-agent command.** Every `ctx_execute` call that is not a full test suite passes `timeoutMs: 60000`; the parameter is `timeoutMs`, not `timeout`. Never pipe a heredoc into an interpreter: an empty one into `python -` hangs until the timeout.

## Rules
- Separate lanes: the reviewer must not be the author's same active context.
- Verify before reporting. A plausible-sounding finding that does not reproduce is noise.
- State severity honestly; do not pad the list to look thorough.
- "No findings" is a valid result when the work is sound.
- Advisory by default — review informs, it does not gate. Hard gates (release,
  security, destructive operations) stay separate and fail closed.

## Output
- Findings, most-severe first, each with file, line, and concrete failure scenario
- What was checked and found clean
- Anything that could not be assessed

## Deliverable conformance gate
Before calling a written review done:
1. At kickoff, copy every hard constraint of the requested deliverable into the checklist: exact headings, sentence caps, row schema, status definitions, final-reply format and write allowlist.
2. Keep a `Deviations` list and a `Write ledger` (every path written outside job tmp, and by whom) from the moment each happens. Copy both into the report.
3. Compute method and "every X" statements from ID sets at the end; never pre-write them in a skeleton.
4. Run a script that checks each constraint and every cited `path:line` and quote. Re-run it after every fix pass.

## Quality Gates

Before finalizing the review, check the existing merged OMC `qualityGates["omc-review"]` entries (project stage entries replace the user list; see `docs/quality-gates-configuration.md`). If there are no entries, do not call `omc quality-gates list`, spawn gate tasks, or add a Quality Gates section or gate records to the review output. If there is at least one entry, call `omc quality-gates list --stage omc-review --json` and show every validation error. For each available gate, spawn one independent Claude Code `Task` that loads the named skill from `resolvedPath`, reviews the same changes, and returns `VERDICT: PASS` or `VERDICT: BLOCK` plus findings. Use the configured model override when present; do not pass another reviewer's output to the gate. Reuse the same gate lane if the change is revised and reviewed again.

When gates are configured, record `{ gate, mode, verdict }` for each gate in a Quality Gates section of the review output. Unresolved skills are `gate_unavailable` with a visible warning, never PASS; they do not fail the review stage. A blocking `BLOCK` makes the overall result `REQUEST CHANGES`; advisory results are informational and never block.
