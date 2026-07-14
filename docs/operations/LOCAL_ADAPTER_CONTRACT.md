# Local Adapter Contract

Status: Draft v0.1 contract.

## Purpose

Local adapters let Lobster Buffet run portable process operations without
committing private workspace facts to shared provider artifacts.

The shared provider defines operation schemas, manifests, side effects,
approval gates, and adapter capability names. Each target OpenClaw instance
supplies local adapter configuration and implementation for private facts such
as channel maps, project roots, remotes, secrets, local policy, and visible
message surfaces.

## Adapter API Shape

Adapter API: `lobster-buffet.local-adapter.v0`

The canonical capability list is machine-readable:

- `manifests/local-adapter-capabilities.v0.1.0.json`
- `schemas/local-adapter-capabilities.v0.1.0.json`

Operations should request capabilities by name. If the local adapter cannot
provide a required capability, the operation must fail with
`adapter.capability_missing`.

## Ownership Boundary

Shared Lobster Buffet artifacts may contain:

- capability names
- side-effect categories
- approval classes
- schema refs
- opaque reference fields
- redacted summaries
- fixture data that does not identify a private workspace

Local adapters own:

- Discord guild/channel IDs and channel maps
- project root paths
- repo account, remote, and provider configuration
- secrets, tokens, signing keys, and credential labels
- personal memory and user-specific preferences
- visible-message destinations and delivery receipts
- local approval policy and exception state

## Disclosure Policies

Each adapter capability declares one disclosure policy:

- `category_only`: shared output may describe the kind of target only.
- `opaque_ref`: shared output may include a local opaque reference.
- `redacted_summary`: shared output may include sanitized summary fields.
- `local_only`: result is usable only inside the local instance unless
  separately summarized.
- `explicit_disclosure_required`: raw or identifying values require explicit
  local authorization before they appear in shared output.

Shared operation results must not include raw secrets, private channel IDs,
hostnames, personal memory, customer data, or unrelated local paths unless the
adapter explicitly authorizes that disclosure for the current surface.

## Required Result Envelope

Adapter calls should return a structured envelope:

```json
{
  "ok": true,
  "capability": "project.resolve",
  "result": {},
  "warnings": [],
  "private_data": {
    "contains_private_values": false,
    "private_refs_only": true,
    "disclosure_policy": "opaque_ref"
  }
}
```

Failures should use stable error codes:

```json
{
  "ok": false,
  "capability": "project.resolve",
  "error": {
    "code": "adapter.ambiguous_context",
    "message": "Project context could not be resolved unambiguously.",
    "retryable": false,
    "details": {}
  }
}
```

`details` must follow the capability disclosure policy.

## Capability Groups

### Project

- `project.resolve`: map a caller context to an opaque project reference.

### Filesystem

- `filesystem.read_project_metadata`: read approved project metadata and return
  summaries.
- `filesystem.write_project_files`: write approved project files after preview
  and gates.

### Git

- `git.inspect_status`: inspect repo boundary, branch, dirty state, and
  ahead/behind state.
- `git.write_branch`: create branches, stage files, commit, or merge after
  gates.

### Incident

- `incident.read_state`: read local incident state.
- `incident.write_state`: append incident updates and closures.

### Review

- `review.read_state`: read local review-session state.
- `review.write_state`: record comments, decisions, approvals, or blockers.

### Heartbeat

- `heartbeat.read_state`: read project/incident heartbeat state.

### Channel And Remote

- `channel.resolve`: resolve caller surface/channel labels to opaque local refs.
- `remote.resolve`: resolve repository remote metadata without exposing
  credentials.

### Visible Message And Approval

- `visible_message.preview`: prepare visible output without sending.
- `visible_message.send`: send visible output only when local policy allows it.
- `approval.request`: ask for human approval when required.

### Secrets

- `secret.read`: read a named local secret only with explicit authorization.

## Operation Gate Expectations

Before a mutating operation executes, the adapter contract expects:

1. Operation plan generated.
2. Warden/Armor gates consulted when configured.
3. Local approval policy checked.
4. Adapter capability availability checked.
5. Preview produced for writes or visible sends.
6. Verification steps recorded.

Read-only operations may execute after capability checks but must still respect
disclosure policies.

## First Conformance Target

The first read-only adapter fixture should support `project.inspect` with:

- `project.resolve`
- `filesystem.read_project_metadata`
- `git.inspect_status`

It should prove that `project.inspect` can return useful state without exposing
raw private channel IDs, local absolute paths, secrets, or unrelated memory.

The current synthetic fixture is:

- `fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json`
- `schemas/local-adapter-fixture.v0.1.0.json`

The first lifecycle write conformance target validates apply-mode fixtures with:

- `project.resolve`
- `git.inspect_status`
- `approval.request`
- `filesystem.write_project_files`
- `git.write_branch`
- lifecycle apply receipts matching `schemas/lifecycle-apply-receipt.v0.1.0.json`

The conformance script is:

```bash
python3 scripts/check_lifecycle_write_conformance.py
```

For a single adapter fixture:

```bash
python3 scripts/check_lifecycle_write_conformance.py \
  --adapter-fixture fixtures/adapters/synthetic-lifecycle-apply-approved.v0.1.0.json \
  --expect-status applied \
  --expect-mutates true
```

## Adapter Config Loading

The adapter loader supports two backend kinds:

- `fixture`: load a checked-in or local fixture file.
- `command`: invoke a local command with a JSON request on stdin and read a
  local adapter fixture envelope from stdout.

- `schemas/local-adapter-config.v0.1.0.json`
- `schemas/local-adapter-invocation.v0.1.0.json`
- `fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json`
- `fixtures/adapters/synthetic-command-adapter-config.v0.1.0.json`
- `fixtures/adapters/synthetic-command-lifecycle-apply-config.v0.1.0.json`
- `fixtures/adapters/synthetic-command-lifecycle-apply-approval-missing-config.v0.1.0.json`
- `fixtures/adapters/synthetic-command-lifecycle-apply-dirty-git-config.v0.1.0.json`
- `fixtures/adapters/synthetic-command-lifecycle-apply-stale-approval-config.v0.1.0.json`

The CLI accepts:

```bash
python3 -m lobster_buffet.cli project inspect --adapter-config fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json
```

If `--adapter-config` is omitted, the CLI also checks
`LOBSTER_BUFFET_ADAPTER_CONFIG`.

`--adapter-fixture` remains available as an explicit test/development override.
When both are provided, the fixture override wins.

Command-backed adapters receive:

```json
{
  "schema": "lobster-buffet.local-adapter-invocation.v0.1.0",
  "adapter_api": "lobster-buffet.local-adapter.v0",
  "operation": "project.inspect",
  "requested_capabilities": ["project.resolve"]
}
```

They must return the same capability envelope shape used by fixture-backed
adapters. The synthetic command adapter is:

```bash
python3 scripts/synthetic_local_adapter_command.py fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json
```

Command-backed lifecycle apply is covered by:

```bash
python3 -m lobster_buffet.cli project archive \
  --project-name synthetic-project \
  --mode apply \
  --adapter-config fixtures/adapters/synthetic-command-lifecycle-apply-config.v0.1.0.json
```

The conformance suite also runs command-backed negative apply cases for missing
approval, dirty git state, and stale approval scope. Those cases must stop
before write execution and return `mutates: false`.

Shared example adapter config must not contain private workspace paths, channel
IDs, secrets, tokens, or remote credentials. Real local deployments may point at
local-only config files, but shared operation outputs must still obey the
capability disclosure policies.
