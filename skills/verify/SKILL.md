---
name: verify
description: Verify that a change really works before you claim completion
---

# Verify

Use this skill when the user wants confidence that a feature, fix, or refactor actually works.

## Goal
Turn vague “it should work” claims into concrete evidence.

## Workflow
1. Identify the exact behavior that must be proven.
2. Prefer existing tests first.
3. If coverage is missing, run the narrowest direct verification commands available.
4. If direct automation is not enough, describe the manual validation steps and gather concrete observable evidence.
5. When the proof is a CI run (for example on GitHub Actions), write the proof plan first: each scenario and its expected step result. The reviewer gets that plan with the diff before the first push, and the proof runs once, on the post-review commit. A proof run before review is rerun whenever the review changes the logic, and an unreviewed plan can miss a scenario.
6. Report only what was actually verified.

## Verification order
1. Existing tests
2. Typecheck / build
3. Narrow direct command checks
4. Manual or interactive validation

## Before running a repo's code on this machine
"Not elevated" protects only admin-ACL locations; user-writable paths such as `ProgramData` subfolders, `$env:TEMP` and `HKCU:` stay open. Before running a suite or script from the repo under test:
1. Fetch CI results for the same commit first (`gh run list --commit <sha>`, then download the artifacts). A disposable runner may already have the answer.
2. List every place the code can write: default `-Path`/`$LogPath` values, `ProgramData`, `$env:TEMP`, `HKLM:`/`HKCU:`, `Cert:\`, `Set-Content`/`Out-File`/`New-Item`, and any test `BeforeAll` that dot-sources a script before its `Mock`s. Exclude test files that run side-effecting code unmocked.
3. Snapshot those locations before the run and diff them after. Write "no host changes" only once that diff exists.
4. Put any hazard you find into every later sub-agent brief as a ban, not advice.

## Rules
- Do not say a change is complete without evidence.
- If a check fails, include the failure clearly.
- If no realistic verification path exists, say that explicitly instead of bluffing.
- Prefer concise evidence summaries over noisy logs.
- A checker never reuses a pattern (regex, parser, lookup table) from the code it checks: a shared bug passes both. Each check class must first flag a planted known-bad sample; a check that has never been seen to fail is not evidence.
- When a job already fails on the base, judge a change by the diff of its failing-test set against the base's set: download both result artifacts and report the tests added and removed, never the job's conclusion. "Fails as before" requires that diff, because a red job that was red before still hides any new breakage.
- A pull-request CI run is evidence only for the base it checked out. Before citing one, read its checkout line (`HEAD is now at <merge> Merge <head> into <base>`) and confirm `<base>` is the current target-branch head. A re-run replays the original merge commit. A close and reopen while mergeability is still `UNKNOWN` can still build the stale one, so first confirm that `refs/pull/<n>/merge` has the current head as a parent. Merging on a run against an older base is an exception: name it in the report together with its justification.

## Output
- What was verified
- Which commands/tests were run
- What passed
- What failed or remains unverified

