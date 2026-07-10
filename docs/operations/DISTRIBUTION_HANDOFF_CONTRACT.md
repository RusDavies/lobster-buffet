# Distribution Handoff Contract

Status: Draft v0.1 Buffet-side contract.

## Purpose

This contract defines what Lobster Buffet exposes for distribution and
inspection by another project or tool. It deliberately does not define how
Lobster Portage packages, doctors, installs, releases, or rolls back artifacts.

Buffet owns the handoff contract. Portage owns the packaging mechanics.

## Machine-Readable Contract

- Handoff manifest: `manifests/distribution-handoff.v0.1.0.json`
- Handoff schema: `schemas/distribution-handoff.v0.1.0.json`
- Validator: `scripts/check_initial_operation_schemas.py`

## Packageable Artifacts

Buffet may expose:

- operation docs under `docs/operations/`
- JSON Schemas under `schemas/`
- provider, catalog, handoff, and compatibility manifests under `manifests/`
- synthetic fixtures under `fixtures/`
- validation scripts under `scripts/`

These artifacts must be valid without private workspace data.

## Local-Only Boundaries

Buffet must not package:

- local adapter configuration
- Discord guild/channel IDs or channel maps
- absolute local project paths
- secrets, tokens, signing keys, credentials, or tenant IDs
- personal memory or user-specific preferences
- customer documents or private runtime data
- Redshield enterprise policy packs or customer evidence
- Portage release, install, doctor, rollback, or distribution implementation

Shared artifacts may name capability categories and opaque references, but raw
local values stay local.

## Version Metadata

The handoff contract exposes:

- operation contract versions such as `command.describe@0.1.0`
- manifest versions such as `operation-catalog@0.1.0`
- adapter API version such as `lobster-buffet.local-adapter.v0`
- release compatibility policy version such as `release-compatibility@0.1.0`

Version updates should change related schemas, manifests, fixtures, and
validation together.

## Compatibility Guarantees

For the v0.x draft series:

- packageable artifacts validate without private adapter data;
- operation schemas declare side effects, approvals, capabilities, and errors;
- adapter capability names are stable enough for operation catalogs to refer to
  them;
- local-only boundaries remain explicit;
- mutating operations keep preview, gate, audit, and fail-safe expectations.

No public release, compliance posture, or production-readiness claim is implied
by this draft handoff contract.

## Portage-Inspectable Refs

Another tool may inspect:

- `manifests/provider-operations.v0.1.0.json`
- `manifests/operation-catalog.v0.1.0.json`
- `manifests/local-adapter-capabilities.v0.1.0.json`
- `manifests/distribution-handoff.v0.1.0.json`
- `manifests/release-compatibility.v0.1.0.json`
- `scripts/check_initial_operation_schemas.py`

That inspection should answer what Buffet exposes and what remains local-only.
It should not require Portage-specific implementation knowledge.
