# OpenClaw Dynamic Wrapper

Status: Draft v0.1 wrapper slice.

## Purpose

The OpenClaw wrapper exposes selected Lobster Buffet CLI-core operations as
OpenClaw dynamic tools without duplicating operation logic.

The wrapper is intentionally thin:

- register OpenClaw tool metadata;
- translate tool arguments into CLI-core arguments;
- return compact JSON tool results;
- preserve operation-plan, side-effect, approval, adapter capability, and
  privacy metadata produced by the CLI core.

## Wrapper Location

- `wrappers/openclaw/openclaw.plugin.json`
- `wrappers/openclaw/index.js`
- `wrappers/openclaw/test.js`

## Initial Tools

- `lobster_buffet_command_list`
- `lobster_buffet_command_describe`
- `lobster_buffet_operation_plan`
- `lobster_buffet_project_inspect`
- `lobster_buffet_project_lifecycle`

These tools cover the current schema-backed executable CLI surface. The wrapper
does not implement business logic directly; it shells out to:

```bash
python3 -m lobster_buffet.cli ...
```

## Configuration

Supported plugin configuration:

- `projectRoot`: optional local path to the Lobster Buffet repo/package root.
- `python`: optional Python executable name or path.
- `defaultAdapterFixture`: optional adapter fixture path relative to
  `projectRoot`.
- `defaultAdapterConfig`: optional adapter config path relative to
  `projectRoot`.

`project.inspect` uses a caller-supplied `adapter_config`, then
`defaultAdapterConfig`, then a caller-supplied `adapter_fixture`, then
`defaultAdapterFixture`. Adapter config may point at a fixture backend or a
command backend. The fixture path remains a development/test escape hatch;
real local deployments should prefer adapter config.

## Boundary

The wrapper must not contain private workspace data, Discord channel maps,
local absolute paths, secrets, tokens, personal memory, or remote credentials.

The wrapper may expose packageable metadata and synthetic fixture-backed
results. Real local data must flow through local adapters once adapter loading
exists.

Lifecycle wrapper calls generate preview lifecycle plans by default. In apply
mode, they pass through the CLI core and local adapter config. Wrapper
regression coverage exercises command-backed approved apply, missing approval,
dirty git, and stale approval cases so blocked command-backed adapters cannot
quietly mutate.

CLI conformance separately covers command transport failures such as invalid
JSON, nonzero exit, timeout, and missing required capabilities.
