const plugin = require("./index.js");

const registered = [];
plugin.register({
  pluginConfig: {},
  registerTool(tool) {
    registered.push(tool);
  },
});

const byName = new Map(registered.map((tool) => [tool.name, tool]));
for (const expected of [
  "lobster_buffet_command_list",
  "lobster_buffet_command_describe",
  "lobster_buffet_operation_plan",
  "lobster_buffet_project_inspect",
  "lobster_buffet_project_lifecycle",
  "lobster_buffet_git_workflow_guard",
  "lobster_buffet_incident_list",
  "lobster_buffet_alignment_scan",
  "lobster_buffet_review_list",
  "lobster_buffet_review_update",
  "lobster_buffet_heartbeat_packet",
  "lobster_buffet_heartbeat_check",
]) {
  if (!byName.has(expected)) {
    throw new Error(`missing registered tool: ${expected}`);
  }
}

async function call(name, params) {
  const result = await byName.get(name).execute("call-1", params);
  if (!result || !result.details || !Array.isArray(result.content)) {
    throw new Error(`${name} returned an invalid OpenClaw tool result`);
  }
  return result.details;
}

async function main() {
  const list = await call("lobster_buffet_command_list", {});
  if (!list.operations.some((operation) => operation.name === "project.inspect")) {
    throw new Error("command list did not include project.inspect");
  }

  const description = await call("lobster_buffet_command_describe", { name: "project.inspect" });
  if (description.operation.name !== "project.inspect") {
    throw new Error("command describe returned the wrong operation");
  }

  const plan = await call("lobster_buffet_operation_plan", { name: "project.inspect", surface: "discord" });
  if (plan.schema !== "lobster-buffet.operation-plan.v0.1.0") {
    throw new Error("operation plan returned the wrong schema");
  }
  if (plan.requested_by.surface !== "discord") {
    throw new Error("operation plan did not preserve the caller surface");
  }

  const inspect = await call("lobster_buffet_project_inspect", {
    adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
  });
  if (inspect.project.name !== "lobster-buffet") {
    throw new Error("project inspect returned the wrong synthetic project");
  }

  const commandInspect = await call("lobster_buffet_project_inspect", {
    adapter_config: "fixtures/adapters/synthetic-command-adapter-config.v0.1.0.json",
  });
  if (commandInspect.project.name !== "lobster-buffet") {
    throw new Error("command-backed project inspect returned the wrong synthetic project");
  }

  const lifecycle = await call("lobster_buffet_project_lifecycle", {
    action: "archive",
    project_name: "synthetic-project",
  });
  if (lifecycle.operation.name !== "project.archive" || lifecycle.status !== "requires_approval") {
    throw new Error("project lifecycle wrapper returned the wrong preview");
  }

  const lifecycleApply = await call("lobster_buffet_project_lifecycle", {
    action: "archive",
    project_name: "synthetic-project",
    mode: "apply",
    adapter_fixture: "fixtures/adapters/synthetic-lifecycle-apply-approved.v0.1.0.json",
  });
  if (lifecycleApply.status !== "applied" || lifecycleApply.mutates !== true) {
    throw new Error("project lifecycle wrapper did not return the expected apply result");
  }

  const commandLifecycleApply = await call("lobster_buffet_project_lifecycle", {
    action: "archive",
    project_name: "synthetic-project",
    mode: "apply",
    adapter_config: "fixtures/adapters/synthetic-command-lifecycle-apply-config.v0.1.0.json",
  });
  if (commandLifecycleApply.status !== "applied" || commandLifecycleApply.mutates !== true) {
    throw new Error("command-backed project lifecycle wrapper did not return the expected apply result");
  }

  const guard = await call("lobster_buffet_git_workflow_guard", {
    adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
    requested_action: "lifecycle_apply",
  });
  if (guard.decision !== "allowed" || guard.requested_action !== "lifecycle_apply") {
    throw new Error("git workflow guard did not return the expected synthetic decision");
  }

  const incidents = await call("lobster_buffet_incident_list", {
    adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
  });
  if (!incidents.incidents.some((incident) => incident.status === "stale" && incident.resurface === true)) {
    throw new Error("incident list did not surface stale incident state");
  }

  const alignment = await call("lobster_buffet_alignment_scan", {
    adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
    current_plan_summary: "Implement an intent-alignment scanner.",
  });
  if (alignment.verdict !== "aligned") {
    throw new Error("alignment scan did not return the expected synthetic verdict");
  }

  const reviews = await call("lobster_buffet_review_list", {
    adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
  });
  if (!reviews.reviews.some((review) => review.status === "active" && review.apply_gate === "pending")) {
    throw new Error("review list did not return the expected active review");
  }

  const reviewUpdate = await call("lobster_buffet_review_update", {
    adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
    review_id: "review-001",
    kind: "approval",
    summary: "Plan approval after review evidence is accepted.",
    apply_gate: "approved",
  });
  if (reviewUpdate.status !== "requires_approval" || reviewUpdate.mutates !== false) {
    throw new Error("review update did not return the expected planning preview");
  }

  const heartbeat = await call("lobster_buffet_heartbeat_packet", {
    adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
  });
  if (heartbeat.overall_status !== "blocked") {
    throw new Error("heartbeat packet did not return the expected synthetic status");
  }

  const heartbeatCheck = await call("lobster_buffet_heartbeat_check", {
    adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
  });
  if (heartbeatCheck.status !== "not_due" || heartbeatCheck.due !== false) {
    throw new Error("heartbeat check did not return the expected synthetic due state");
  }

  const serialized = JSON.stringify({
    alignment,
    description,
    guard,
    heartbeat,
    heartbeatCheck,
    incidents,
    commandInspect,
    inspect,
    lifecycle,
    lifecycleApply,
    commandLifecycleApply,
    list,
    plan,
    reviews,
    reviewUpdate,
  });
  for (const fragment of ["channel:", "0000000000000000000", "/home/", "github.com/RusDavies"]) {
    if (serialized.includes(fragment)) {
      throw new Error(`wrapper output contains forbidden private/local fragment ${fragment}`);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
