# Commercial Strategy

## Open-Core Position

Lobster Buffet should be the open-source core for portable OpenClaw process operations. It should remain useful without paid products:

- operation schemas
- local provider runtime, CLI, or provider wrappers
- basic operation catalog
- local adapter boundary
- side-effect and approval metadata
- structured operation results

The commercial opportunity should sit around trust, governance, assurance, reporting, and enterprise integration. The core should not be deliberately weakened to create a paywall.

## Product Split

### Lobster Buffet

Lobster Buffet owns the portable operation layer:

- define operation catalogs and schemas
- produce inspectable operation plans before execution
- declare side effects, mutation scope, approval requirements, and verification steps
- execute deterministic provider logic through local adapters
- return structured results and audit-friendly events

### Redshield Warden

Redshield Warden can become the paid governance and policy layer around Buffet operations:

- policy-as-code for agent and tool operations
- approval workflows by operation type, project, channel, data class, customer, or risk level
- role-based access control, SSO, and enterprise identity integration
- audit logs and policy decision evidence
- compliance-oriented policy packs
- human review queues for risky actions
- attestations explaining why an operation was allowed, blocked, or escalated

Warden should consume Buffet operation plans before execution and return a decision such as allow, deny, require approval, require extra checks, or downgrade capability.

### Redshield Armor

Redshield Armor can become the paid hardening and assurance layer around Buffet packages and runtime operations:

- provider, adapter, schema, and package security checks
- secret and private-data boundary validation
- adapter conformance tests
- supply-chain checks such as dependency risk, SBOMs, signatures, provenance, and release integrity
- pre-release certification for shared operation packs
- runtime guardrails for file, network, process, and external-surface access
- customer-facing security posture and assurance reports

Armor should consume Buffet packages, operation metadata, and execution evidence to produce validation results, hardening recommendations, and release or runtime gates.

## Execution Flow

The intended enterprise execution flow is:

1. LLM interprets user intent.
2. Lobster Buffet builds an operation plan.
3. Redshield Warden reviews policy, approval, and governance requirements.
4. Redshield Armor performs security or hardening checks when required by policy or operation class.
5. Lobster Buffet executes through local adapters if gates pass.
6. Lobster Buffet returns structured results and audit events.
7. Redshield products retain or report governance and assurance evidence according to local policy.

## Packaging Model

Suggested commercial packaging:

- Free/open source: Buffet core, schemas, local development mode, basic adapters, basic validation, and local audit event emission.
- Pro/team: reusable policy packs, richer audit trail, team configuration, dashboard, and common integrations.
- Enterprise: SSO/RBAC, approval workflows, compliance reporting, signed policy bundles, support SLAs, private integrations, deployment reviews, and hardened release channels.

## Implications For Redshield Warden

This direction implies Warden needs:

- a stable policy decision API for Buffet operation plans
- policy inputs based on declared metadata rather than private workspace internals
- approval workflow concepts for agent/tool actions
- audit evidence formats for allow, deny, approval-required, and downgraded decisions
- enterprise identity and role mapping
- policy pack versioning and signed policy bundle support

## Implications For Redshield Armor

This direction implies Armor needs:

- a validation API for Buffet packages, schemas, adapters, and operation plans
- checks for secret leakage, private-data boundary violations, and unsafe adapter capabilities
- adapter conformance fixtures
- runtime enforcement hooks for high-risk file, network, process, and external-surface access
- supply-chain evidence such as SBOMs, signatures, provenance, and dependency-risk reports
- release certification outputs that Warden and enterprise customers can consume

## Boundary

Redshield products should be optional and adjacent. Lobster Buffet should expose the metadata and hooks they need, but the initial portable provider should not depend on paid products to function.

The shared operation gate contract for those hooks lives in
`docs/operations/REDSHIELD_OPERATION_GATE_CONTRACT.md`.
