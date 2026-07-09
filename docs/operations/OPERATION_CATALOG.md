# Operation Catalog

This catalog expands the initial schema slice into the planned Lobster Buffet operation families. It is intentionally draft-level: only `command.describe` and `project.inspect` currently have input/output schemas.

The machine-readable catalog lives at `manifests/operation-catalog.v0.1.0.json`.

## Catalog Rules

- Operations must declare name, version, stability, implementation state, side effects, approval classes, adapter capabilities, and error codes.
- Planned operations may appear in the catalog before their JSON Schemas exist.
- The provider operation manifest remains limited to schema-backed operations.
- Mutating operations must preview, validate, and fail safely before writing.
- Private workspace facts belong in adapters, not shared operation definitions.

## Implementation States

- `planned`: cataloged but no input/output schema yet.
- `schema_defined`: input/output contract exists, but implementation is not complete.
- `implemented`: provider implementation and validation exist.
- `deprecated`: retained only for compatibility.

## Families

### Command

- `command.list`: list known operations and command aliases.
- `command.describe`: describe a known operation, including schemas, side effects, approvals, adapter needs, and errors.

### Project Lifecycle

- `project.inspect`: resolve context and report structured project state.
- `project.bootstrap`: create a standard project skeleton and lifecycle files.
- `project.adopt`: bind an existing project or channel to managed lifecycle metadata.
- `project.repair`: reconcile missing, stale, or inconsistent lifecycle/project files.
- `project.migrate`: move a project between lifecycle layouts or naming conventions.
- `project.archive`: mark a project archived without deleting data.

### Incident

- `incident.list`: list active, stale, or recently closed incidents.
- `incident.update`: append status, blockers, evidence, or next action.
- `incident.close`: close an incident with resolution and follow-up state.

### Alignment

- `alignment.scan`: compare current work against project goal, backlog, docs, and artifacts.

### Review

- `review.list`: list active review sessions, pending comments, and apply gates.
- `review.update`: record review comments, decisions, approvals, or blockers.

### Heartbeat

- `heartbeat.packet`: build compact periodic status across project, incident, review, and git state.
- `heartbeat.check`: decide whether a project or incident needs a visible progress heartbeat.

### Git Workflow

- `git.workflow.inspect`: inspect repository boundary, branch, dirty state, and ahead/behind state.
- `git.workflow.guard`: evaluate whether a requested git workflow step is allowed before mutation.

## Next Schema Candidates

The next schema work should focus on high-leverage read-only operations:

1. `command.list`
2. `git.workflow.inspect`
3. `alignment.scan`
4. `incident.list`

Mutating lifecycle operations should wait until the adapter contract and transport shape are clearer. A mutating provider without a firm gate model is just a footgun with a logo.
