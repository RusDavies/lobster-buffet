# Lobster Buffet

Lobster Buffet is a pre-alpha provider layer for portable OpenClaw process
operations. It turns project lifecycle checks, incident/status summaries,
review state, intent alignment, and related workflow operations into
deterministic CLI and wrapper calls.

The core idea is simple: reusable operation logic belongs in public provider
code, while each OpenClaw instance keeps private workspace facts in local
adapters.

## Status

This repository is public, but the API is not stable yet. The current codebase
proves the CLI core, schema-backed operation catalog, OpenClaw wrapper, and MCP
wrapper skeleton. The MCP wrapper is still marked `skeleton`, not
`packageable`.

## Start Here

- `docs/PRODUCT_BRIEF.md` - product framing, users, goals, and non-goals.
- `docs/ARCHITECTURE.md` - provider/adapters/tooling shape.
- `docs/REQUIREMENTS.md` - functional, security, privacy, and operational requirements.
- `docs/operations/OPERATION_CATALOG.md` - supported operation families.
- `docs/operations/LOCAL_ADAPTER_CONTRACT.md` - local/private boundary contract.
- `ROADMAP.md` - public roadmap.

## Run Checks

```bash
python3 scripts/check_initial_operation_schemas.py
python3 scripts/check_cli_core.py
python3 scripts/check_mcp_wrapper_packageability.py
python3 scripts/check_command_adapter_failure_conformance.py
python3 scripts/check_lifecycle_write_conformance.py
node wrappers/openclaw/test.js
node wrappers/mcp/test.js
```

## Local Adapter Boundary

Shared artifacts must not contain private workspace state, Discord channel maps,
secrets, local paths, personal memory, or credentials. Runtime deployments
provide those facts through local adapter configuration.

## Naming Note

`lobster-buffet` is memorable and fits the Lobster Portage family, but it is
whimsical for public infrastructure. Treat it as the working name until a naming
pass confirms whether the public package should keep the name or adopt a
plainer one.
