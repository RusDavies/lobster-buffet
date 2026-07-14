const wrapper = require("./index.js");

const metadata = wrapper.listTools();
if (metadata.providerApi !== "lobster-buffet.provider.v0") {
  throw new Error("MCP wrapper metadata did not declare the provider API");
}
if (metadata.localAdapterApi !== "lobster-buffet.local-adapter.v0") {
  throw new Error("MCP wrapper metadata did not declare the local adapter API");
}
if (!metadata.tools.some((tool) => tool.name === "lobster_buffet_command_list")) {
  throw new Error("MCP wrapper did not expose lobster_buffet_command_list");
}
if (!metadata.tools.some((tool) => tool.name === "lobster_buffet_project_inspect")) {
  throw new Error("MCP wrapper did not expose lobster_buffet_project_inspect");
}
if (!metadata.tools.some((tool) => tool.name === "lobster_buffet_project_lifecycle")) {
  throw new Error("MCP wrapper did not expose lobster_buffet_project_lifecycle");
}

const list = wrapper.callTool("lobster_buffet_command_list", {});
if (list.isError || !Array.isArray(list.content) || !list.structuredContent) {
  throw new Error("MCP wrapper command.list returned an invalid MCP-style result");
}
if (!list.structuredContent.operations.some((operation) => operation.name === "project.inspect")) {
  throw new Error("MCP wrapper command.list did not delegate to the CLI core");
}

const inspect = wrapper.callTool("lobster_buffet_project_inspect", {
  adapter_config: "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
});
if (inspect.isError || inspect.structuredContent.project?.name !== "lobster-buffet") {
  throw new Error("MCP wrapper project.inspect did not return the expected synthetic project");
}

const commandInspect = wrapper.callTool("lobster_buffet_project_inspect", {
  adapter_config: "fixtures/adapters/synthetic-command-adapter-config.v0.1.0.json",
});
if (commandInspect.isError || commandInspect.structuredContent.project?.name !== "lobster-buffet") {
  throw new Error("MCP wrapper project.inspect did not support command-backed adapter config");
}

const lifecycle = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  reason: "Synthetic MCP lifecycle preview.",
});
if (
  lifecycle.isError ||
  lifecycle.structuredContent.operation?.name !== "project.archive" ||
  lifecycle.structuredContent.status !== "requires_approval" ||
  lifecycle.structuredContent.mutates !== false
) {
  throw new Error("MCP wrapper lifecycle preview did not return the expected non-mutating approval gate");
}

const lifecycleApprovalMissing = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  mode: "apply",
  adapter_config: "fixtures/adapters/synthetic-command-lifecycle-apply-approval-missing-config.v0.1.0.json",
});
if (
  lifecycleApprovalMissing.isError ||
  lifecycleApprovalMissing.structuredContent.status !== "requires_approval" ||
  lifecycleApprovalMissing.structuredContent.mutates !== false
) {
  throw new Error("MCP wrapper lifecycle apply did not preserve the missing-approval blocked path");
}

const lifecycleDirty = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  mode: "apply",
  adapter_config: "fixtures/adapters/synthetic-command-lifecycle-apply-dirty-git-config.v0.1.0.json",
});
if (
  lifecycleDirty.isError ||
  lifecycleDirty.structuredContent.status !== "blocked" ||
  lifecycleDirty.structuredContent.mutates !== false
) {
  throw new Error("MCP wrapper lifecycle apply did not preserve the dirty-git blocked path");
}

const lifecycleStale = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  mode: "apply",
  adapter_config: "fixtures/adapters/synthetic-command-lifecycle-apply-stale-approval-config.v0.1.0.json",
});
if (
  lifecycleStale.isError ||
  lifecycleStale.structuredContent.status !== "blocked" ||
  lifecycleStale.structuredContent.mutates !== false
) {
  throw new Error("MCP wrapper lifecycle apply did not preserve the stale-approval blocked path");
}

const lifecycleApply = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  mode: "apply",
  adapter_config: "fixtures/adapters/synthetic-command-lifecycle-apply-config.v0.1.0.json",
});
if (
  lifecycleApply.isError ||
  lifecycleApply.structuredContent.status !== "applied" ||
  lifecycleApply.structuredContent.mutates !== true
) {
  throw new Error("MCP wrapper lifecycle apply did not preserve the approved synthetic apply path");
}

const unknown = wrapper.callTool("lobster_buffet_missing_tool", {});
if (!unknown.isError || unknown.structuredContent.error?.code !== "mcp.tool_not_found") {
  throw new Error("MCP wrapper did not return a structured unknown-tool error");
}

const serialized = JSON.stringify({
  commandInspect,
  inspect,
  lifecycle,
  lifecycleApply,
  lifecycleApprovalMissing,
  lifecycleDirty,
  lifecycleStale,
  list,
  metadata,
  unknown,
});
for (const fragment of ["channel:", "0000000000000000000", "/home/", "github.com/RusDavies"]) {
  if (serialized.includes(fragment)) {
    throw new Error(`MCP wrapper output contains forbidden private/local fragment ${fragment}`);
  }
}
