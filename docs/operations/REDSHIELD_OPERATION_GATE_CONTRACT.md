# Redshield Operation Gate Contract

Status: Stable v0.1 contract for Lobster Buffet operation-plan review.

## Purpose

Lobster Buffet owns portable runtime/provider operations. This contract defines
the operation-plan, Warden policy decision, Armor assurance decision, and audit
event shape that adjacent Redshield products can consume without reading
private local adapter state directly.

Lobster Portage may package or distribute Lobster Buffet provider artifacts, but
this runtime-facing contract belongs here.

## Ownership Split

- Lobster Buffet defines operation plans, side effects, approval requirements,
  adapter capability categories, structured results, and audit events.
- Redshield Warden reviews operation plans for policy, approval, governance,
  and evidence requirements.
- Redshield Armor reviews operation plans and provider packages for hardening,
  conformance, private-data boundaries, and unsafe capability use.
- Local OpenClaw adapters resolve private facts and decide what can be disclosed
  into a shared operation plan.
- Lobster Portage distributes provider packages, schemas, manifests, release
  metadata, and rollback guidance.

## Operation Plan Envelope

Before execution, Lobster Buffet should be able to emit an operation plan:

```json
{
  "schema": "lobster-buffet.operation-plan.v0.1.0",
  "plan_id": "plan-123",
  "operation": {
    "namespace": "lobster-buffet",
    "name": "project.inspect",
    "version": "0.1.0",
    "stability": "draft"
  },
  "requested_by": {
    "actor_ref": "local-actor-ref",
    "surface": "discord|tui|api|cron|unknown"
  },
  "input_summary": {
    "redaction": "private_refs",
    "fields": {}
  },
  "side_effects": [
    "filesystem.read",
    "git.read"
  ],
  "approval": {
    "required": false,
    "classes": [],
    "reason": "Read-only inspection."
  },
  "adapter_capabilities": [
    "project.resolve",
    "git.inspect_status"
  ],
  "affected_surfaces": [
    {
      "kind": "project",
      "ref_policy": "category_only"
    }
  ],
  "verification": [
    {
      "kind": "command",
      "description": "Validate output schema."
    }
  ],
  "privacy": {
    "contains_private_values": false,
    "private_refs_only": true,
    "disclosure_policy": "local_adapter_controlled"
  }
}
```

Shared plans should use categories, opaque refs, and summaries. They must not
include raw secrets, private memory, local channel IDs, personal data, customer
documents, or unrelated local paths unless a local adapter explicitly authorizes
that disclosure.

## Warden Decision Contract

Redshield Warden may consume an operation plan and return:

```json
{
  "schema": "redshield-warden.operation-decision.v0.1.0",
  "plan_id": "plan-123",
  "decision": "allow|deny|require_approval|require_extra_checks|downgrade|inconclusive",
  "required_approvals": [],
  "policy_refs": [],
  "evidence_requirements": [],
  "rationale": "Policy decision summary.",
  "expires_at": null
}
```

Decision rules:

- `allow`: operation may execute under the current plan.
- `deny`: operation must not execute.
- `require_approval`: local adapter or human approval must complete first.
- `require_extra_checks`: Armor or another validation gate must complete first.
- `downgrade`: operation may execute only with reduced capabilities.
- `inconclusive`: operation must pause because policy evidence is insufficient.

## Armor Decision Contract

Redshield Armor may consume an operation plan, provider package metadata, or
execution evidence and return:

```json
{
  "schema": "redshield-armor.assurance-decision.v0.1.0",
  "plan_id": "plan-123",
  "decision": "pass|fail|needs_review|not_required|inconclusive",
  "checks": [],
  "findings": [],
  "hardening_recommendations": [],
  "evidence_refs": [],
  "rationale": "Assurance decision summary."
}
```

Armor checks should focus on:

- private-data and secret boundary violations;
- unsafe adapter capabilities;
- provider package/schema conformance;
- runtime file, network, process, and external-surface risk;
- operation evidence completeness;
- unsupported security or enterprise-readiness claims.

## Buffet Audit Event

Every gated operation should be able to emit an audit event:

```json
{
  "schema": "lobster-buffet.audit-event.v0.1.0",
  "event_id": "audit-123",
  "plan_id": "plan-123",
  "operation": "project.inspect",
  "phase": "planned|warden_decided|armor_decided|approved|executed|blocked|failed",
  "decision_refs": [],
  "result_ref": null,
  "redaction": "private_refs",
  "created_at": "2026-07-09T00:00:00Z"
}
```

Audit events should preserve enough evidence for Warden policy evidence and
Armor assurance evidence without storing raw private adapter data in the shared
provider artifact.

## CLI/API Integration

The stable conceptual command surfaces are:

```bash
redshield-warden buffet decide --operation-plan /path/to/plan.json --evidence-out /path/to/decision.json
redshield-armor buffet assess --operation-plan /path/to/plan.json --evidence-out /path/to/decision.json
```

These commands belong to the adjacent Redshield products. Lobster Buffet should
only rely on the request/result contract and should remain useful without paid
Redshield tooling.

## Enterprise Boundary

Enterprise Redshield editions may add organization policy packs, signed
evidence, central audit storage, dashboards, support, and governance workflow
integrations.

Enterprise credentials, tenant IDs, service URLs, signing keys, and
organization-specific policy must stay in local adapters, CI secrets, or
enterprise configuration. They must not be committed to Lobster Buffet provider
schemas, fixtures, or package artifacts.

## Non-Goals

- Do not make Redshield required for ordinary Lobster Buffet local use.
- Do not move Lobster Portage package/distribution duties into Lobster Buffet.
- Do not store private local adapter state in shared operation plans.
- Do not claim compliance, signing, audit, or enterprise readiness without
  evidence and approval.
