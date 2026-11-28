---
name: sharded-plan-merge
description: Fan a review or audit out to parallel specialist agents and merge their returns by script into one plan or ledger — with a checked return contract, on-arrival validation, per-shard review and a pre-review integration gate. Use whenever several agents' outputs are combined mechanically.
triggers:
  - shard the findings across specialist agents
  - merge the agents' returns into one plan
  - fan out workstream planners
  - combine specialist ledgers
---

# Sharded plan merge

Use this when N parallel agents each plan or audit one shard and a script merges their returns into one deliverable (plan, ledger, report). Not for a single agent, and not for task execution (that is `team`).

Every rule below came from one 110-PR planning session where the merge was the most expensive and most error-prone step (`.omc/tmp/reflection-2026-11-28.md` in azure-arc-deployment-framework).

## Steps

1. **Write the return contract before spawning.** Every field the merge script will read gets a fenced block with fixed keys — not only the ledger. Cards, decisions, owner actions, dependencies: all fenced, all line-oriented (`key: value` or `|`-separated with a fixed column list).
   *Why:* only the ledger was checked last time; cards came back in five formats and needed five parsers and translation layers, which produced silent mis-parses the critic later found.
2. **Tag cross-shard IDs with the shard.** Decisions, owner actions and card keys are `SEC-D1`, `ARCH-D3`, `SEC-O2` — never bare `D1`.
   *Why:* five agents each invent `D1`; translating them by regex later skipped `D2.` (a lookahead bug) and left wrong IDs in the plan.
3. **Require completeness markers.** Every return lists its expected section headings and ends with `<!-- END -->`; it must not send a "highlights" message before the final report.
   *Why:* a report cut off mid-section passed an ID-coverage check; a highlights-first message was mistaken for the report.
4. **Read reports with the extractor, not by hand:**
   `python scripts/agent_report.py <agent-name> --expect "## A. LEDGER,## B. CARDS" --out <dir>`
   It globs `agent-*<name>-*.jsonl` (a named agent's file is `agent-a<name>-<hash>.jsonl`), takes the **last** text block (never the longest), exits 1 when a heading or the sentinel is missing, and splits sections into files under the Read limit.
   *Why:* idle notifications are ~4 KB previews; ad-hoc extraction broke three different ways.
5. **Validate each return on arrival and send failures back.** Run the contract check the moment a return lands; on any failure, `SendMessage` the exact errors to the author (it still has its context) and wait. Never parse around a deviation in the merge script.
6. **Review each shard while waiting for the others.** A critic (or a cheaper first pass) reviews each return as it arrives; card-level findings go back to the owning specialist, so fixes land in source text, not in a lead-override layer.
7. **Keep lead content as data.** Overrides, dependency edges, merge chains and owner decisions (`id, options, recommendation, status`) live in data files the builder reads. Ordering tables are rendered from the edge data, never hand-written. Owner acceptance is a status change plus a rebuild.
   *Why:* hand-written chains disagreed with generated edges; accepting decisions needed patch scripts over prose.
8. **Run the integration gate before any critic pass.**
   - every "after X lands / is green" reference resolves to a card whose approach produces it;
   - a file × PR matrix: a DELETE and any other card touching the same file need an ordering edge;
   - the dependency graph is acyclic and each honest-test → fix pair is ordered;
   - every check class flags a **planted known-bad sample** before its result counts, and no checker reuses a pattern from the builder.
   *Why:* the critic's BLOCKER last time was the plan contradicting itself; the scan copied the builder's broken regex and reported clean.
9. **Final critic covers seams and assembly only**, and its verdict carries its scope. A revision that introduces a new BLOCKER/MAJOR gets a full pass by a fresh critic. Report "ACCEPT" only with its scope.
10. **Fit the reader.** Declare a size budget (main-body KB, card count) before assembly and report actual against it; batch Low/Nit findings per file into hygiene items; push card detail into appendices. Every decision line in the final reply names its recommendation.

## Success criteria
- Every return passed the contract check on arrival (or was re-sent by its author).
- The merge script has one generic parser and no per-agent translation tables.
- The integration gate and the ledger check both pass, each having first failed on a planted sample.
- The final report quotes every review verdict with its scope.

## Pitfalls
- A green coverage count is not completeness: check headings and the sentinel.
- Concurrent `Read` of one large file by several agents can hang them; inline shards or give each agent its own file.
- Tokens in generated text (`[[key]]`) collide with code (`[[nan]]`); use a namespaced form such as `{{pr:key}}`.
- On Windows, print through `PYTHONIOENCODING=utf-8` or a non-UTF-8 console crashes on `→`/`—`.
