# Product Brief

## Summary

Lobster Buffet is a shared OpenClaw process-provider project. It exposes portable process operations as deterministic, tool-backed calls that multiple OpenClaw instances can use through local adapters.

It complements Lobster Portage rather than replacing it. Lobster Portage distributes reusable files, templates, manifests, patch bundles, and overlay composition. Lobster Buffet provides the callable operational layer for shared commands and workflows.

## Problem

OpenClaw instances accumulate useful procedures: project bootstrapping, existing-channel adoption, lifecycle state, command help, incident recovery, intent alignment, review sessions, heartbeat checks, and migration workflows.

Today many of those processes live as Markdown instructions inside one instance. That burns tokens, is hard to keep synchronized, and depends too much on the LLM remembering every step. Other OpenClaw instances cannot easily reuse those processes without copying local lore and private configuration.

## Goals

- Provide deterministic shared operations for portable OpenClaw process workflows.
- Keep LLMs focused on interpretation, ambiguity resolution, and final communication.
- Keep instance-specific data in local adapters and overlays.
- Support public open-source release once privacy, safety, and compatibility gates are met.
- Integrate cleanly with Lobster Portage as the package/distribution layer.
- Leave a clear integration point for Redshield policy and hardening projects without making them part of the provider core.

## Non-Goals

- Do not become a hosted service by default.
- Do not store private workspace data, secrets, credentials, personal memory, or Discord channel maps.
- Do not replace Lobster Portage's manifest, overlay, and package distribution responsibilities.
- Do not silently perform external/public actions without the local instance's approval rules.
- Do not require every OpenClaw instance to use Discord, GitHub, or the same filesystem layout.

## Users

- OpenClaw instance operators who want portable, reliable process automation.
- OpenClaw agents that need structured tool results instead of long prompt procedures.
- Maintainers who want reusable process packs without cloning a private workspace.

## Initial Operation Families

- Command catalog: list available commands and describe usage, side effects, and approval gates.
- Project lifecycle: bootstrap, adopt/bind, inspect, repair/reconcile, migrate, archive.
- Project context: map channel/session context to project state and outstanding approvals.
- Incident management: intake, classify, update, list active queues, resurface stale incidents, close.
- Intent alignment: compare project docs, backlog, artifacts, and current plan.
- Review sessions: collect comments, walk questions, manage apply gates.
- Heartbeat/status: batch periodic checks into structured packets.
- Git workflow guardrails: repo boundary, dirty state, branch, verification, commit/merge/push policy.

## Relationship To Lobster Portage

Lobster Portage already contains useful distribution concepts:

- managed vs local-only boundaries
- manifest-driven ownership
- local/private overlay composition
- source-workspace capture and promotion
- doctor/diff/install conservatism
- patch bundle release and rollback discipline

Lobster Buffet should reuse those concepts. The likely split is:

- Lobster Portage distributes provider code, schemas, templates, and release artifacts.
- Lobster Buffet defines and implements runtime-callable provider operations.
- Each target OpenClaw instance supplies local adapters for channels, projects, remotes, secrets, and user-facing surfaces.

## Relationship To Redshield

Lobster Buffet should expose operation schemas, operation plans, side-effect metadata, approval requirements, and structured results in a way that future Redshield projects can consume.

The intended split is:

- Redshield Warden can act as an adjacent policy and approval gate for operations before they execute.
- Redshield Armor can act as an adjacent hardening and security validation layer for provider code, schemas, adapters, and release artifacts.
- Lobster Buffet should not depend on either project for its core portable provider behavior.
- Redshield integrations should be optional, explicit, and driven by declared operation metadata rather than private workspace assumptions.

The commercial open-core strategy for this split is described in `docs/COMMERCIAL_STRATEGY.md`.

## Success Criteria

- A target OpenClaw instance can install or configure the provider without exposing private local data.
- An agent can call provider operations and receive compact structured results.
- Command help remains current as operations are added.
- Project lifecycle operations can inspect and repair existing state before changing it.
- Incident operations resurface stale work instead of burying it.
- Lobster Portage can distribute or reference the provider package cleanly.
- Redshield policy and hardening layers can inspect Buffet operation plans without requiring private adapter data.

## Risks

- Provider operations could become too powerful and mutate local instances unsafely.
- Shared schemas may accidentally encode one workspace's assumptions.
- Poor adapter boundaries could leak local data.
- A hosted-provider path would add operational and privacy obligations that are out of scope for the first version.
- Naming may be too whimsical for public infrastructure if the project matures.
