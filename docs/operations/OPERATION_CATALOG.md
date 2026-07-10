# Operation Catalog

This catalog expands the initial schema slice into the planned Lobster Buffet operation families. It is intentionally draft-level; read-only operations and safe lifecycle previews are being promoted before write-capable adapters exist.

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

The current lifecycle implementation is preview-only. It emits structured
approval-required plans and verification steps, but it does not perform
filesystem or git mutations. Apply-mode lifecycle execution requires
write-capable local adapters and an approval gate.

### Incident

- `incident.list`: list active, stale, or recently closed incidents.
- `incident.update`: append status, blockers, evidence, or next action.
- `incident.close`: close an incident with resolution and follow-up state.

`incident.list` is implemented as a read-only provider operation. It reads
local incident state through `incident.read_state`, returns counts plus
redacted incident summaries, and includes stale incidents marked for
resurfacing in the default active view.

`incident.update` and `incident.close` are schema-defined only. Their contracts
describe local incident-state writes as approval-gated operations with
state-conflict verification; they do not yet execute mutations through the CLI
core or OpenClaw wrapper.

### Alignment

- `alignment.scan`: compare current work against project goal, backlog, docs, and artifacts.

`alignment.scan` is implemented as a read-only provider operation. It reads
project metadata and git status through local adapter capabilities, returns an
aligned / drifting / blocked verdict, and reports compact evidence without
exposing local paths or private channel data.

### Review

- `review.list`: list active review sessions, pending comments, and apply gates.
- `review.update`: record review comments, decisions, approvals, or blockers.

`review.list` is implemented as a read-only provider operation. It reads local
review-session summaries through `review.read_state` and returns counts,
pending comment totals, and apply-gate status without exposing private review
storage. `review.update` remains planned until write-capable review gates are
explicit.

### Heartbeat

- `heartbeat.packet`: build compact periodic status across project, incident, review, and git state.
- `heartbeat.check`: decide whether a project or incident needs a visible progress heartbeat.

`heartbeat.packet` is implemented as a read-only provider operation. It
combines adapter-provided project, repository, incident, review, and heartbeat
state into a compact status packet. It does not send visible messages or make
scheduling decisions. `heartbeat.check` remains planned until those local
decision gates are explicit.

### Git Workflow

- `git.workflow.inspect`: inspect repository boundary, branch, dirty state, and ahead/behind state.
- `git.workflow.guard`: evaluate whether a requested git workflow step is allowed before mutation.

## Next Schema Candidates

The next schema work should focus on the remaining high-leverage read-only and state operations:

1. `heartbeat.check`
2. `git.workflow.guard`

Lifecycle apply mode should wait until the write-capable adapter and approval
gate are concrete. A mutating provider without a firm gate model is still just a
footgun with a logo.
