# Lifecycle Apply-Mode Readiness Contract

Status: Draft v0.1 readiness contract.

## Purpose

Lifecycle apply-mode is intentionally blocked until write-capable local adapters
and approval gates are explicit. This contract defines the minimum readiness
shape required before `project.bootstrap`, `project.adopt`, `project.repair`,
`project.migrate`, or `project.archive` can move beyond preview-only output.

The CLI core now includes a fixture-backed apply-mode executor. The shared
provider validates readiness evidence and accepts adapter-reported write
results; actual filesystem writes, git writes, approval prompts, local paths,
branch names, and policy details remain owned by the local adapter.

## Required Readiness Evidence

Before a lifecycle operation may run in apply mode, the local adapter must
provide evidence for:

- operation plan generation;
- human or local-policy approval completion;
- write-capable filesystem adapter availability;
- write-capable git adapter availability;
- dirty-worktree guard result;
- preview artifact reviewed before write;
- post-write verification steps;
- rollback or recovery notes appropriate to the local instance.

The shared provider may name these evidence categories and validate their
presence. Local adapters own private paths, branch names, approver identities,
policy details, and any actual mutation.

## Apply-Mode Boundary

Buffet apply-mode must still:

- require `repo_mutation` approval for lifecycle writes;
- refuse execution if approval is missing, stale, or scoped to another plan;
- refuse execution if write-capable adapter capabilities are absent;
- refuse execution if git status is dirty unless the operation explicitly
  permits and records that state;
- return structured verification evidence after the adapter write path runs;
- avoid exposing private local paths or channel IDs in shared result fields.

## Current State

The repository includes a synthetic readiness fixture at
`fixtures/adapters/synthetic-lifecycle-apply-readiness.v0.1.0.json`, a schema
at `schemas/lifecycle-apply-readiness.v0.1.0.json`, and apply-mode fixtures for
approved, approval-missing, dirty-git, and stale-approval gate outcomes.

Those fixtures demonstrate the shape expected from a local instance. The apply
executor does not directly perform filesystem writes, git writes, approval
requests, or visible messages; it only validates the adapter evidence and
returns structured results.
