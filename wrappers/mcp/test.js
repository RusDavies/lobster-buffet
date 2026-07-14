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

const unknown = wrapper.callTool("lobster_buffet_missing_tool", {});
if (!unknown.isError || unknown.structuredContent.error?.code !== "mcp.tool_not_found") {
  throw new Error("MCP wrapper did not return a structured unknown-tool error");
}

const serialized = JSON.stringify({ commandInspect, inspect, list, metadata, unknown });
for (const fragment of ["channel:", "0000000000000000000", "/home/", "github.com/RusDavies"]) {
  if (serialized.includes(fragment)) {
    throw new Error(`MCP wrapper output contains forbidden private/local fragment ${fragment}`);
  }
}
