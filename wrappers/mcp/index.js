const { execFileSync } = require("node:child_process");
const path = require("node:path");

const PROVIDER_API = "lobster-buffet.provider.v0";
const LOCAL_ADAPTER_API = "lobster-buffet.local-adapter.v0";
const DEFAULT_ADAPTER_FIXTURE = "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json";
const DEFAULT_ADAPTER_CONFIG = "";
const LIFECYCLE_ACTIONS = ["bootstrap", "adopt", "repair", "migrate", "archive"];
const GIT_WORKFLOW_ACTIONS = ["branch", "commit", "merge", "push", "release", "lifecycle_apply"];
const REVIEW_UPDATE_KINDS = ["comment", "decision", "approval", "blocker", "note"];
const REVIEW_APPLY_GATES = ["none", "pending", "approved", "blocked"];

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

function requireParam(params, name) {
  const value = readString(params[name]);
  if (!value) {
    return errorResult("mcp.input_invalid", `Missing required parameter: ${name}`);
  }
  return value;
}

function optionalValue(value, allowed, fallback) {
  const item = readString(value);
  return allowed.includes(item) ? item : fallback;
}

function appendAdapterArgs(args, params, options) {
  const adapterFixture = readString(params.adapter_fixture);
  const adapterConfig = readString(params.adapter_config) || options.defaultAdapterConfig;
  if (adapterFixture) {
    args.push("--adapter-fixture", adapterFixture);
  } else if (adapterConfig) {
    args.push("--adapter-config", adapterConfig);
  } else {
    args.push("--adapter-fixture", options.defaultAdapterFixture);
  }
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

function commandDescribe(params, options) {
  const name = requireParam(params, "name");
  if (isRecord(name)) {
    return name;
  }
  return mcpJsonResult(runCli(["command", "describe", "--name", name], options));
}

function operationPlan(params, options) {
  const name = requireParam(params, "name");
  if (isRecord(name)) {
    return name;
  }
  const args = ["operation", "plan", "--name", name];
  const actorRef = readString(params.actor_ref);
  if (actorRef) {
    args.push("--actor-ref", actorRef);
  }
  args.push("--surface", optionalValue(params.surface, ["discord", "tui", "api", "cron", "unknown"], "unknown"));
  return mcpJsonResult(runCli(args, options));
}

function projectInspect(params, options) {
  const args = ["project", "inspect"];
  appendAdapterArgs(args, params, options);
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
  args.push("--mode", mode);
  const reason = readString(params.reason);
  if (reason) {
    args.push("--reason", reason);
  }
  appendAdapterArgs(args, { adapter_fixture: adapterFixture, adapter_config: adapterConfig }, options);
  return mcpJsonResult(runCli(args, options));
}

function gitWorkflowGuard(params, options) {
  const args = [
    "git",
    "workflow-guard",
    "--requested-action",
    optionalValue(params.requested_action, GIT_WORKFLOW_ACTIONS, "lifecycle_apply"),
    "--detail",
    optionalValue(params.detail, ["summary", "full"], "summary"),
  ];
  appendAdapterArgs(args, params, options);
  return mcpJsonResult(runCli(args, options));
}

function incidentList(params, options) {
  const args = [
    "incident",
    "list",
    "--status",
    optionalValue(params.status, ["active", "stale", "closed", "all"], "active"),
    "--detail",
    optionalValue(params.detail, ["summary", "full"], "summary"),
  ];
  appendAdapterArgs(args, params, options);
  return mcpJsonResult(runCli(args, options));
}

function alignmentScan(params, options) {
  const args = [
    "alignment",
    "scan",
    "--source",
    optionalValue(params.source, ["project", "channel", "explicit"], "project"),
    "--detail",
    optionalValue(params.detail, ["summary", "full"], "summary"),
  ];
  for (const [paramName, flagName] of [
    ["project", "--project"],
    ["label", "--label"],
    ["current_plan_summary", "--current-plan-summary"],
  ]) {
    const value = readString(params[paramName]);
    if (value) {
      args.push(flagName, value);
    }
  }
  appendAdapterArgs(args, params, options);
  return mcpJsonResult(runCli(args, options));
}

function reviewList(params, options) {
  const args = [
    "review",
    "list",
    "--status",
    optionalValue(params.status, ["active", "blocked", "closed", "all"], "active"),
    "--detail",
    optionalValue(params.detail, ["summary", "full"], "summary"),
  ];
  appendAdapterArgs(args, params, options);
  return mcpJsonResult(runCli(args, options));
}

function reviewUpdate(params, options) {
  const reviewId = requireParam(params, "review_id");
  const summary = requireParam(params, "summary");
  if (isRecord(reviewId)) {
    return reviewId;
  }
  if (isRecord(summary)) {
    return summary;
  }
  const kind = readString(params.kind);
  if (!REVIEW_UPDATE_KINDS.includes(kind)) {
    return errorResult("mcp.input_invalid", `Review update kind must be one of: ${REVIEW_UPDATE_KINDS.join(", ")}`);
  }
  const args = [
    "review",
    "update",
    "--review-id",
    reviewId,
    "--kind",
    kind,
    "--summary",
    summary,
    "--mode",
    readString(params.mode) === "apply" ? "apply" : "plan",
  ];
  const applyGate = optionalValue(params.apply_gate, REVIEW_APPLY_GATES, undefined);
  const reason = readString(params.reason);
  if (applyGate) {
    args.push("--apply-gate", applyGate);
  }
  if (reason) {
    args.push("--reason", reason);
  }
  appendAdapterArgs(args, params, options);
  return mcpJsonResult(runCli(args, options));
}

function heartbeatPacket(params, options) {
  const args = ["heartbeat", "packet", "--detail", optionalValue(params.detail, ["summary", "full"], "summary")];
  appendAdapterArgs(args, params, options);
  return mcpJsonResult(runCli(args, options));
}

function heartbeatCheck(params, options) {
  const args = [
    "heartbeat",
    "check",
    "--scope",
    optionalValue(params.scope, ["project", "incident", "review", "all"], "all"),
    "--detail",
    optionalValue(params.detail, ["summary", "full"], "summary"),
  ];
  appendAdapterArgs(args, params, options);
  return mcpJsonResult(runCli(args, options));
}

function adapterProperties() {
  return {
    adapter_fixture: {
      type: "string",
      description: "Optional adapter fixture path relative to the project root.",
    },
    adapter_config: {
      type: "string",
      description: "Optional adapter config path relative to the project root.",
    },
  };
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
    name: "lobster_buffet_command_describe",
    title: "Lobster Buffet Command Describe",
    description: "Describe one Lobster Buffet operation through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["name"],
      properties: {
        name: {
          type: "string",
          description: "Operation name, such as project.inspect.",
        },
      },
    },
  },
  {
    name: "lobster_buffet_operation_plan",
    title: "Lobster Buffet Operation Plan",
    description: "Generate a Lobster Buffet operation plan through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["name"],
      properties: {
        name: {
          type: "string",
          description: "Operation name, such as project.inspect.",
        },
        actor_ref: {
          type: "string",
          description: "Opaque local actor reference.",
        },
        surface: {
          type: "string",
          description: "Caller surface.",
          enum: ["discord", "tui", "api", "cron", "unknown"],
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
      properties: adapterProperties(),
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
  {
    name: "lobster_buffet_git_workflow_guard",
    title: "Lobster Buffet Git Workflow Guard",
    description: "Evaluate whether a requested git workflow step is allowed before mutation.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        requested_action: {
          type: "string",
          description: "Git workflow action being considered.",
          enum: GIT_WORKFLOW_ACTIONS,
        },
        detail: {
          type: "string",
          description: "Guard detail level.",
          enum: ["summary", "full"],
        },
        ...adapterProperties(),
      },
    },
  },
  {
    name: "lobster_buffet_incident_list",
    title: "Lobster Buffet Incident List",
    description: "List active, stale, or closed incidents through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        status: {
          type: "string",
          description: "Incident status filter.",
          enum: ["active", "stale", "closed", "all"],
        },
        detail: {
          type: "string",
          description: "Incident detail level.",
          enum: ["summary", "full"],
        },
        ...adapterProperties(),
      },
    },
  },
  {
    name: "lobster_buffet_alignment_scan",
    title: "Lobster Buffet Alignment Scan",
    description: "Scan project intent, backlog, and artifact evidence through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        source: {
          type: "string",
          description: "Alignment context source.",
          enum: ["project", "channel", "explicit"],
        },
        project: {
          type: "string",
          description: "Optional project label or opaque reference.",
        },
        label: {
          type: "string",
          description: "Optional context label.",
        },
        current_plan_summary: {
          type: "string",
          description: "Short summary of the work being checked.",
        },
        detail: {
          type: "string",
          description: "Alignment detail level.",
          enum: ["summary", "full"],
        },
        ...adapterProperties(),
      },
    },
  },
  {
    name: "lobster_buffet_review_list",
    title: "Lobster Buffet Review List",
    description: "List active, blocked, or closed review sessions through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        status: {
          type: "string",
          description: "Review status filter.",
          enum: ["active", "blocked", "closed", "all"],
        },
        detail: {
          type: "string",
          description: "Review detail level.",
          enum: ["summary", "full"],
        },
        ...adapterProperties(),
      },
    },
  },
  {
    name: "lobster_buffet_review_update",
    title: "Lobster Buffet Review Update",
    description: "Generate a gated review.update write preview through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["review_id", "kind", "summary"],
      properties: {
        review_id: {
          type: "string",
          description: "Opaque review id.",
        },
        kind: {
          type: "string",
          description: "Review update kind.",
          enum: REVIEW_UPDATE_KINDS,
        },
        summary: {
          type: "string",
          description: "Update summary.",
        },
        mode: {
          type: "string",
          description: "Review update mode.",
          enum: ["plan", "apply"],
        },
        apply_gate: {
          type: "string",
          description: "Optional target apply gate.",
          enum: REVIEW_APPLY_GATES,
        },
        reason: {
          type: "string",
          description: "Optional local reason for the review update.",
        },
        ...adapterProperties(),
      },
    },
  },
  {
    name: "lobster_buffet_heartbeat_packet",
    title: "Lobster Buffet Heartbeat Packet",
    description: "Build a compact read-only status packet through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        detail: {
          type: "string",
          description: "Heartbeat detail level.",
          enum: ["summary", "full"],
        },
        ...adapterProperties(),
      },
    },
  },
  {
    name: "lobster_buffet_heartbeat_check",
    title: "Lobster Buffet Heartbeat Check",
    description: "Check whether a visible heartbeat is due through the CLI core.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        scope: {
          type: "string",
          description: "Heartbeat check scope.",
          enum: ["project", "incident", "review", "all"],
        },
        detail: {
          type: "string",
          description: "Heartbeat detail level.",
          enum: ["summary", "full"],
        },
        ...adapterProperties(),
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
  if (name === "lobster_buffet_command_describe") {
    return commandDescribe(params, options);
  }
  if (name === "lobster_buffet_operation_plan") {
    return operationPlan(params, options);
  }
  if (name === "lobster_buffet_project_inspect") {
    return projectInspect(params, options);
  }
  if (name === "lobster_buffet_project_lifecycle") {
    return projectLifecycle(params, options);
  }
  if (name === "lobster_buffet_git_workflow_guard") {
    return gitWorkflowGuard(params, options);
  }
  if (name === "lobster_buffet_incident_list") {
    return incidentList(params, options);
  }
  if (name === "lobster_buffet_alignment_scan") {
    return alignmentScan(params, options);
  }
  if (name === "lobster_buffet_review_list") {
    return reviewList(params, options);
  }
  if (name === "lobster_buffet_review_update") {
    return reviewUpdate(params, options);
  }
  if (name === "lobster_buffet_heartbeat_packet") {
    return heartbeatPacket(params, options);
  }
  if (name === "lobster_buffet_heartbeat_check") {
    return heartbeatCheck(params, options);
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
