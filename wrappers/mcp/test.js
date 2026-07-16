const wrapper = require("./index.js");
const server = require("./server.js");

const metadata = wrapper.listTools();
if (metadata.providerApi !== "lobster-buffet.provider.v0") {
  throw new Error("MCP wrapper metadata did not declare the provider API");
}
if (metadata.localAdapterApi !== "lobster-buffet.local-adapter.v0") {
  throw new Error("MCP wrapper metadata did not declare the local adapter API");
}
const expectedTools = [
  "lobster_buffet_alignment_scan",
  "lobster_buffet_command_describe",
  "lobster_buffet_command_list",
  "lobster_buffet_git_workflow_guard",
  "lobster_buffet_heartbeat_check",
  "lobster_buffet_heartbeat_packet",
  "lobster_buffet_incident_list",
  "lobster_buffet_operation_plan",
  "lobster_buffet_project_inspect",
  "lobster_buffet_project_lifecycle",
  "lobster_buffet_review_list",
  "lobster_buffet_review_update",
];
for (const toolName of expectedTools) {
  if (!metadata.tools.some((tool) => tool.name === toolName)) {
    throw new Error(`MCP wrapper did not expose ${toolName}`);
  }
}

const initialize = server.handleRequest({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {},
});
if (initialize.result?.serverInfo?.name !== "lobster-buffet-mcp-wrapper") {
  throw new Error("MCP server entrypoint did not return server identity");
}

const serverTools = server.handleRequest({
  jsonrpc: "2.0",
  id: 2,
  method: "tools/list",
  params: {},
});
if (!serverTools.result?.tools?.some((tool) => tool.name === "lobster_buffet_command_list")) {
  throw new Error("MCP server entrypoint did not expose wrapper tools");
}

const list = wrapper.callTool("lobster_buffet_command_list", {});
if (list.isError || !Array.isArray(list.content) || !list.structuredContent) {
  throw new Error("MCP wrapper command.list returned an invalid MCP-style result");
}
if (!list.structuredContent.operations.some((operation) => operation.name === "project.inspect")) {
  throw new Error("MCP wrapper command.list did not delegate to the CLI core");
}

const serverList = server.handleRequest({
  jsonrpc: "2.0",
  id: 3,
  method: "tools/call",
  params: {
    name: "lobster_buffet_command_list",
    arguments: {},
  },
});
if (
  serverList.error ||
  !serverList.result?.structuredContent?.operations?.some((operation) => operation.name === "project.inspect")
) {
  throw new Error("MCP server entrypoint did not delegate tools/call to the wrapper path");
}

const initialized = server.handleRequest({
  jsonrpc: "2.0",
  method: "notifications/initialized",
  params: {},
});
if (initialized !== undefined) {
  throw new Error("MCP server entrypoint should not respond to initialized notifications");
}

const parseError = server.handleJsonRpcLine("{");
if (parseError.error?.code !== -32700) {
  throw new Error("MCP server entrypoint did not return JSON-RPC parse errors");
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

const commandDescribe = wrapper.callTool("lobster_buffet_command_describe", {
  name: "project.inspect",
});
if (commandDescribe.isError || commandDescribe.structuredContent.operation?.name !== "project.inspect") {
  throw new Error("MCP wrapper command.describe did not delegate to the CLI core");
}

const operationPlan = wrapper.callTool("lobster_buffet_operation_plan", {
  name: "project.inspect",
  surface: "discord",
});
if (operationPlan.isError || operationPlan.structuredContent.plan_id !== "plan:project.inspect:v0.1.0") {
  throw new Error("MCP wrapper operation.plan did not delegate to the CLI core");
}

const gitWorkflowGuard = wrapper.callTool("lobster_buffet_git_workflow_guard", {
  requested_action: "lifecycle_apply",
  adapter_fixture: "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
});
if (gitWorkflowGuard.isError || gitWorkflowGuard.structuredContent.decision !== "allowed") {
  throw new Error("MCP wrapper git.workflow.guard did not return the expected guard decision");
}

const incidentList = wrapper.callTool("lobster_buffet_incident_list", {
  adapter_fixture: "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
});
if (incidentList.isError || incidentList.structuredContent.counts?.active !== 1) {
  throw new Error("MCP wrapper incident.list did not return the expected incident counts");
}

const alignmentScan = wrapper.callTool("lobster_buffet_alignment_scan", {
  adapter_fixture: "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
});
if (alignmentScan.isError || alignmentScan.structuredContent.verdict !== "aligned") {
  throw new Error("MCP wrapper alignment.scan did not return the expected verdict");
}

const reviewList = wrapper.callTool("lobster_buffet_review_list", {
  adapter_fixture: "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
});
if (reviewList.isError || reviewList.structuredContent.counts?.active !== 1) {
  throw new Error("MCP wrapper review.list did not return the expected review counts");
}

const reviewUpdate = wrapper.callTool("lobster_buffet_review_update", {
  review_id: "review-001",
  kind: "note",
  summary: "Synthetic MCP review update.",
  adapter_fixture: "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
});
if (
  reviewUpdate.isError ||
  reviewUpdate.structuredContent.operation?.name !== "review.update" ||
  reviewUpdate.structuredContent.status !== "requires_approval" ||
  reviewUpdate.structuredContent.mutates !== false
) {
  throw new Error("MCP wrapper review.update did not preserve the gated preview result");
}

const heartbeatPacket = wrapper.callTool("lobster_buffet_heartbeat_packet", {
  adapter_fixture: "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
});
if (heartbeatPacket.isError || heartbeatPacket.structuredContent.overall_status !== "blocked") {
  throw new Error("MCP wrapper heartbeat.packet did not return the expected packet status");
}

const heartbeatCheck = wrapper.callTool("lobster_buffet_heartbeat_check", {
  adapter_fixture: "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
});
if (heartbeatCheck.isError || heartbeatCheck.structuredContent.status !== "not_due") {
  throw new Error("MCP wrapper heartbeat.check did not return the expected due state");
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

const lifecycleInvalidJson = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  mode: "apply",
  adapter_config: "fixtures/adapters/synthetic-command-invalid-json-config.v0.1.0.json",
});
if (!lifecycleInvalidJson.isError || lifecycleInvalidJson.structuredContent.error?.code !== "adapter.command_invalid_json") {
  throw new Error("MCP wrapper lifecycle apply did not preserve the invalid JSON error envelope");
}

const lifecycleNonzero = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  mode: "apply",
  adapter_config: "fixtures/adapters/synthetic-command-nonzero-exit-config.v0.1.0.json",
});
if (!lifecycleNonzero.isError || lifecycleNonzero.structuredContent.error?.code !== "adapter.command_failed") {
  throw new Error("MCP wrapper lifecycle apply did not preserve the nonzero-exit error envelope");
}

const lifecycleTimeout = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  mode: "apply",
  adapter_config: "fixtures/adapters/synthetic-command-timeout-config.v0.1.0.json",
});
if (!lifecycleTimeout.isError || lifecycleTimeout.structuredContent.error?.code !== "adapter.command_timeout") {
  throw new Error("MCP wrapper lifecycle apply did not preserve the timeout error envelope");
}

const lifecycleMissingCapability = wrapper.callTool("lobster_buffet_project_lifecycle", {
  action: "archive",
  project_name: "synthetic-project",
  mode: "apply",
  adapter_config: "fixtures/adapters/synthetic-command-missing-capability-config.v0.1.0.json",
});
if (
  lifecycleMissingCapability.isError ||
  lifecycleMissingCapability.structuredContent.status !== "blocked" ||
  lifecycleMissingCapability.structuredContent.mutates !== false
) {
  throw new Error("MCP wrapper lifecycle apply did not preserve the missing-capability blocked result");
}

const unknown = wrapper.callTool("lobster_buffet_missing_tool", {});
if (!unknown.isError || unknown.structuredContent.error?.code !== "mcp.tool_not_found") {
  throw new Error("MCP wrapper did not return a structured unknown-tool error");
}

const serialized = JSON.stringify({
  commandInspect,
  commandDescribe,
  operationPlan,
  gitWorkflowGuard,
  incidentList,
  alignmentScan,
  inspect,
  lifecycle,
  lifecycleApply,
  lifecycleApprovalMissing,
  lifecycleDirty,
  lifecycleInvalidJson,
  lifecycleMissingCapability,
  lifecycleNonzero,
  lifecycleStale,
  lifecycleTimeout,
  list,
  metadata,
  parseError,
  reviewList,
  reviewUpdate,
  heartbeatPacket,
  heartbeatCheck,
  serverList,
  serverTools,
  unknown,
});
for (const fragment of ["channel:", "999999999999999999", "/home/", "github.com/RusDavies"]) {
  if (serialized.includes(fragment)) {
    throw new Error(`MCP wrapper output contains forbidden private/local fragment ${fragment}`);
  }
}
