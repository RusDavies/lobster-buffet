const { execFileSync } = require("node:child_process");
const path = require("node:path");

const PROVIDER_API = "lobster-buffet.provider.v0";
const LOCAL_ADAPTER_API = "lobster-buffet.local-adapter.v0";
const DEFAULT_ADAPTER_FIXTURE = "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json";
const DEFAULT_ADAPTER_CONFIG = "";
const LIFECYCLE_ACTIONS = ["bootstrap", "adopt", "repair", "migrate", "archive"];

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function defaultProjectRoot() {
  return path.resolve(__dirname, "..", "..");
}

function readString(value) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function errorResult(code, message) {
  return mcpJsonResult({
    error: {
      code,
      message,
      retryable: false,
      details: {},
    },
  });
}

function createOptions(config = {}) {
  return {
    projectRoot: readString(config.projectRoot) || defaultProjectRoot(),
    python: readString(config.python) || "python3",
    defaultAdapterFixture: readString(config.defaultAdapterFixture) || DEFAULT_ADAPTER_FIXTURE,
    defaultAdapterConfig: readString(config.defaultAdapterConfig) || DEFAULT_ADAPTER_CONFIG,
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

function projectInspect(params, options) {
  const args = ["project", "inspect"];
  const adapterFixture = readString(params.adapter_fixture);
  const adapterConfig = readString(params.adapter_config) || options.defaultAdapterConfig;
  if (adapterFixture) {
    args.push("--adapter-fixture", adapterFixture);
  } else if (adapterConfig) {
    args.push("--adapter-config", adapterConfig);
  } else {
    args.push("--adapter-fixture", options.defaultAdapterFixture);
  }
  return mcpJsonResult(runCli(args, options));
}

function projectLifecycle(params, options) {
  const action = readString(params.action);
  const projectName = readString(params.project_name);
  const mode = readString(params.mode) || "plan";
  const adapterFixture = readString(params.adapter_fixture);
  const adapterConfig = readString(params.adapter_config) || options.defaultAdapterConfig;
  if (!LIFECYCLE_ACTIONS.includes(action)) {
    return errorResult("mcp.input_invalid", `Lifecycle action must be one of: ${LIFECYCLE_ACTIONS.join(", ")}`);
  }
  if (!projectName) {
    return errorResult("mcp.input_invalid", "Missing required parameter: project_name");
  }
  if (!["plan", "apply"].includes(mode)) {
    return errorResult("mcp.unsupported_mode", "Lifecycle mode must be plan or apply.");
  }

  const args = ["project", action, "--project-name", projectName];
  if (mode === "apply") {
    args.push("--mode", "apply");
    if (adapterFixture) {
      args.push("--adapter-fixture", adapterFixture);
    } else if (adapterConfig) {
      args.push("--adapter-config", adapterConfig);
    }
  }
  const reason = readString(params.reason);
  if (reason) {
    args.push("--reason", reason);
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
  {
    name: "lobster_buffet_project_inspect",
    title: "Lobster Buffet Project Inspect",
    description: "Inspect project state through the CLI core and configured adapter fixture or config.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        adapter_fixture: {
          type: "string",
          description: "Optional adapter fixture path relative to the project root.",
        },
        adapter_config: {
          type: "string",
          description: "Optional adapter config path relative to the project root.",
        },
      },
    },
  },
  {
    name: "lobster_buffet_project_lifecycle",
    title: "Lobster Buffet Project Lifecycle",
    description: "Generate a lifecycle operation preview through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["action", "project_name"],
      properties: {
        action: {
          type: "string",
          description: "Lifecycle action.",
          enum: LIFECYCLE_ACTIONS,
        },
        project_name: {
          type: "string",
          description: "Opaque or sanitized project name.",
        },
        mode: {
          type: "string",
          description: "Lifecycle mode. Apply mode is currently covered for blocked paths.",
          enum: ["plan", "apply"],
        },
        reason: {
          type: "string",
          description: "Optional local reason for the lifecycle preview.",
        },
        adapter_fixture: {
          type: "string",
          description: "Optional adapter fixture path relative to the project root for apply mode.",
        },
        adapter_config: {
          type: "string",
          description: "Optional adapter config path relative to the project root for apply mode.",
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
  if (name === "lobster_buffet_project_inspect") {
    return projectInspect(params, options);
  }
  if (name === "lobster_buffet_project_lifecycle") {
    return projectLifecycle(params, options);
  }
  return errorResult("mcp.tool_not_found", `Unknown MCP wrapper tool: ${name}`);
}

module.exports = {
  PROVIDER_API,
  LOCAL_ADAPTER_API,
  callTool,
  createOptions,
  listTools,
};
