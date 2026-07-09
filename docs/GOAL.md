# Goal

Build a portable shared-provider layer for OpenClaw process operations.

The first useful version should define the operation catalog, local adapter boundary, and provider transport choice well enough that one high-value operation can be implemented without copying private workspace data or relying on long prompt procedures.

## Immediate Outcomes

- Decide the provider shape: dynamic OpenClaw tool provider, MCP-style provider, CLI-first provider, or layered approach.
- Define operation schemas for command catalog/help and project inspection.
- Define local adapter contracts for channel/project mapping, filesystem roots, git remotes, and visible-message surfaces.
- Identify how Lobster Portage should distribute or version the provider.
- Preserve public open-source suitability from the start.

## First Spike

Compare provider transport options using two candidate operations:

1. `command.describe(name)`
2. `project.inspect(context)`

The spike should produce a recommendation, implementation sketch, security/privacy boundary, and test plan.
