const { execFileSync } = require("node:child_process");
const path = require("node:path");

const PROVIDER_API = "lobster-buffet.provider.v0";
const LOCAL_ADAPTER_API = "lobster-buffet.local-adapter.v0";

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function defaultProjectRoot() {
  return path.resolve(__dirname, "..", "..");
}

function createOptions(config = {}) {
  return {
    projectRoot: typeof config.projectRoot === "string" && config.projectRoot.trim() ? config.projectRoot : defaultProjectRoot(),
    python: typeof config.python === "string" && config.python.trim() ? config.python : "python3",
  };
}

function parseCliOutput(output) {
  return JSON.parse(Buffer.isBuffer(output) ? output.toString("utf8") : output);
}

function runCli(args, options) {
  try {
    const output = execFileSync(options.python, ["-m", "lobster_buffet.cli", ...args], {
      cwd: options.projectRoot,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    });
    return parseCliOutput(output);
  } catch (error) {
    if (error && error.stdout) {
      return parseCliOutput(error.stdout);
    }
    throw error;
  }
}

function mcpJsonResult(payload) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(payload, null, 2),
      },
    ],
    structuredContent: payload,
    isError: Boolean(payload.error),
  };
}

function commandList(params, options) {
  const args = ["command", "list"];
  if (params.include_deprecated === true) {
    args.push("--include-deprecated");
  }
  return mcpJsonResult(runCli(args, options));
}

const tools = [
  {
    name: "lobster_buffet_command_list",
    title: "Lobster Buffet Command List",
    description: "List Lobster Buffet operations through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        include_deprecated: {
          type: "boolean",
          description: "Include deprecated operations.",
        },
      },
    },
  },
];

function listTools() {
  return {
    providerApi: PROVIDER_API,
    localAdapterApi: LOCAL_ADAPTER_API,
    tools,
  };
}

function callTool(name, rawParams = {}, config = {}) {
  const params = isRecord(rawParams) ? rawParams : {};
  const options = createOptions(config);
  if (name === "lobster_buffet_command_list") {
    return commandList(params, options);
  }
  return mcpJsonResult({
    error: {
      code: "mcp.tool_not_found",
      message: `Unknown MCP wrapper tool: ${name}`,
      retryable: false,
      details: {},
    },
  });
}

module.exports = {
  PROVIDER_API,
  LOCAL_ADAPTER_API,
  callTool,
  createOptions,
  listTools,
};
