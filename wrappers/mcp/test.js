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

const result = wrapper.callTool("lobster_buffet_command_list", {});
if (result.isError || !Array.isArray(result.content) || !result.structuredContent) {
  throw new Error("MCP wrapper command.list returned an invalid MCP-style result");
}
if (!result.structuredContent.operations.some((operation) => operation.name === "project.inspect")) {
  throw new Error("MCP wrapper command.list did not delegate to the CLI core");
}

const unknown = wrapper.callTool("lobster_buffet_missing_tool", {});
if (!unknown.isError || unknown.structuredContent.error?.code !== "mcp.tool_not_found") {
  throw new Error("MCP wrapper did not return a structured unknown-tool error");
}

const serialized = JSON.stringify({ metadata, result, unknown });
for (const fragment of ["channel:", "0000000000000000000", "/home/", "github.com/RusDavies"]) {
  if (serialized.includes(fragment)) {
    throw new Error(`MCP wrapper output contains forbidden private/local fragment ${fragment}`);
  }
}
