# Requirements

## Functional Requirements

- FR-1: Define a versioned operation catalog for shared OpenClaw process operations.
- FR-2: Provide machine-readable operation schemas for inputs, outputs, side effects, approval requirements, and error/blocker states.
- FR-3: Support local adapters for instance-specific data such as Discord channels, project roots, Git providers, visible-message surfaces, and secrets.
- FR-4: Provide command catalog/help operations that can stay current as commands are added.
- FR-5: Provide project-context inspection before mutating project/channel state.
- FR-6: Make operation results structured enough for LLM summarization without re-reading long process docs.
- FR-7: Integrate with Lobster Portage distribution and release practices.

## Non-Functional Requirements

- NFR-1: Deterministic core operations. The provider should not depend on LLM judgment for steps that can be scripted.
- NFR-2: Portability. Shared operations must avoid workspace-specific assumptions.
- NFR-3: Conservative mutation. Mutating operations should preview, validate, and fail safely.
- NFR-4: Testability. Operations should have deterministic fixtures and regression tests.
- NFR-5: Token efficiency. Operation results should be compact by default with optional detail expansion.

## Security And Privacy Requirements

- SEC-1: Do not store or distribute private workspace data.
- SEC-2: Treat secrets, channel maps, personal memory, local paths, and user-specific preferences as adapter/local-overlay data.
- SEC-3: Operation schemas must describe side effects and approval gates.
- SEC-4: Mutating operations must be auditable and return enough provenance for review.
- SEC-5: Public release requires privacy and security review.

## Operational Requirements

- OPS-1: The first version should be local-first, not hosted.
- OPS-2: If a hosted/shared runtime is introduced later, reclassify the product and add operations, privacy, reliability, and incident-response requirements.
- OPS-3: Provider versions should be pinnable by target instances.
