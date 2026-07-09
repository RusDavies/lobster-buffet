# Architecture

## Overview

Lobster Buffet is a shared provider for OpenClaw process operations. It should expose deterministic operations through a transport that OpenClaw instances can call while keeping instance-specific facts in local adapters.

## Proposed Layers

1. Operation schemas
   - Names, descriptions, inputs, outputs, side effects, approval gates, and error states.
2. Provider implementation
   - Deterministic command/tool logic.
3. Local adapters
   - Channel mapping, project roots, Git/GitHub conventions, visible-message surfaces, secrets, and local policy.
4. Distribution
   - Lobster Portage or related package release path.
5. Optional policy and hardening gates
   - Redshield Warden for policy, approval, and side-effect review.
   - Redshield Armor for hardening, security validation, and release checks.
6. LLM orchestration
   - Interpret user intent, choose operation, resolve ambiguity, and communicate results.

## Candidate Transports

- OpenClaw dynamic tool provider.
- MCP-style provider.
- Local CLI invoked by OpenClaw agents.
- Hybrid: CLI core with provider wrappers.

## Initial Operations

The draft catalog is maintained in `docs/operations/OPERATION_CATALOG.md` and `manifests/operation-catalog.v0.1.0.json`.

- `command.list`
- `command.describe`
- `project.inspect`
- `project.bootstrap`
- `project.adopt`
- `project.repair`
- `project.migrate`
- `project.archive`
- `incident.list`
- `incident.update`
- `alignment.scan`

## Local Adapter Boundary

Adapters own local/private facts:

- Discord guild/channel ids.
- project root paths.
- repo provider/account configuration.
- secrets and credentials.
- user preferences.
- visible reply destinations.
- local command aliases.

Provider operations should accept scoped adapter results rather than reading private state directly unless explicitly configured to do so.

## Lobster Portage Touchpoint

Lobster Portage should remain the distribution and managed-file layer. Lobster Buffet should consume or share:

- managed/local-only boundary concepts.
- overlay composition model.
- manifest validation style.
- conservative doctor/diff/apply behavior.
- release and rollback discipline.

## Redshield Touchpoint

Lobster Buffet should make operation plans inspectable before execution. Plans should include enough metadata for adjacent Redshield tools to reason about policy and security without reading private workspace state directly:

- operation name and schema version
- normalized inputs after adapter resolution
- side effects and mutation scope
- approval requirements
- local adapter capabilities used
- files, remotes, channels, or external surfaces affected by category rather than by private identifier unless explicitly authorized
- expected verification steps

The default execution path should remain local-first and self-contained. Redshield integrations should wrap or gate provider operations when available, not become mandatory dependencies for the initial portable provider.
