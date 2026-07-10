const { execFileSync } = require("node:child_process");
const path = require("node:path");

const DEFAULT_ADAPTER_FIXTURE = "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json";
const DEFAULT_ADAPTER_CONFIG = "";
const LIFECYCLE_ACTIONS = ["bootstrap", "adopt", "repair", "migrate", "archive"];

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function readString(value) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function textResult(text, details) {
  return {
    content: [{ type: "text", text }],
    details,
  };
}

function jsonResult(payload) {
  return textResult(JSON.stringify(payload, null, 2), payload);
}

function defaultProjectRoot() {
  return path.resolve(__dirname, "..", "..");
}

function createOptions(config) {
  return {
    projectRoot: readString(config.projectRoot) || defaultProjectRoot(),
    python: readString(config.python) || "python3",
    defaultAdapterFixture: readString(config.defaultAdapterFixture) || DEFAULT_ADAPTER_FIXTURE,
    defaultAdapterConfig: readString(config.defaultAdapterConfig) || DEFAULT_ADAPTER_CONFIG,
  };
}

function runCli(args, options) {
  const output = execFileSync(options.python, ["-m", "lobster_buffet.cli", ...args], {
    cwd: options.projectRoot,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  return JSON.parse(output);
}

function requireParam(params, name) {
  const value = readString(params[name]);
  if (!value) {
    throw new Error(`Missing required parameter: ${name}`);
  }
  return value;
}

function optionalSurface(value) {
  const surface = readString(value);
  return ["discord", "tui", "api", "cron", "unknown"].includes(surface) ? surface : "unknown";
}

function requireLifecycleAction(value) {
  const action = readString(value);
  if (!LIFECYCLE_ACTIONS.includes(action)) {
    throw new Error(`Lifecycle action must be one of: ${LIFECYCLE_ACTIONS.join(", ")}`);
  }
  return action;
}

function optionalIncidentStatus(value) {
  const status = readString(value);
  return ["active", "stale", "closed", "all"].includes(status) ? status : "active";
}

function optionalReviewStatus(value) {
  const status = readString(value);
  return ["active", "blocked", "closed", "all"].includes(status) ? status : "active";
}

function optionalDetail(value) {
  const detail = readString(value);
  return ["summary", "full"].includes(detail) ? detail : "summary";
}

function optionalAlignmentSource(value) {
  const source = readString(value);
  return ["project", "channel", "explicit"].includes(source) ? source : "project";
}

function optionalHeartbeatScope(value) {
  const scope = readString(value);
  return ["project", "incident", "review", "all"].includes(scope) ? scope : "all";
}

function createTool({ name, label, description, parameters, execute }) {
  return {
    name,
    label,
    description,
    parameters,
    execute: async (_toolCallId, rawParams) => {
      const params = isRecord(rawParams) ? rawParams : {};
      return jsonResult(execute(params));
    },
  };
}

function tools(options) {
  return [
    createTool({
      name: "lobster_buffet_command_list",
      label: "Lobster Buffet Command List",
      description: "List Lobster Buffet operations through the CLI core.",
      parameters: {
        type: "object",
        additionalProperties: false,
        properties: {
          include_deprecated: {
            type: "boolean",
            description: "Include deprecated operations.",
          },
        },
      },
      execute: (params) => {
        const args = ["command", "list"];
        if (params.include_deprecated === true) {
          args.push("--include-deprecated");
        }
        return runCli(args, options);
      },
    }),
    createTool({
      name: "lobster_buffet_command_describe",
      label: "Lobster Buffet Command Describe",
      description: "Describe one Lobster Buffet operation through the CLI core.",
      parameters: {
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
      execute: (params) => runCli(["command", "describe", "--name", requireParam(params, "name")], options),
    }),
    createTool({
      name: "lobster_buffet_operation_plan",
      label: "Lobster Buffet Operation Plan",
      description: "Generate a Lobster Buffet operation plan through the CLI core.",
      parameters: {
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
      execute: (params) => {
        const args = ["operation", "plan", "--name", requireParam(params, "name")];
        const actorRef = readString(params.actor_ref);
        if (actorRef) {
          args.push("--actor-ref", actorRef);
        }
        args.push("--surface", optionalSurface(params.surface));
        return runCli(args, options);
      },
    }),
    createTool({
      name: "lobster_buffet_project_inspect",
      label: "Lobster Buffet Project Inspect",
      description: "Inspect project state through the CLI core and configured adapter fixture.",
      parameters: {
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
      execute: (params) => {
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
        return runCli(args, options);
      },
    }),
    createTool({
      name: "lobster_buffet_project_lifecycle",
      label: "Lobster Buffet Project Lifecycle",
      description: "Generate a lifecycle operation preview through the CLI core.",
      parameters: {
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
          reason: {
            type: "string",
            description: "Optional local reason for the lifecycle action.",
          },
        },
      },
      execute: (params) => {
        const args = ["project", requireLifecycleAction(params.action), "--project-name", requireParam(params, "project_name")];
        const reason = readString(params.reason);
        if (reason) {
          args.push("--reason", reason);
        }
        return runCli(args, options);
      },
    }),
    createTool({
      name: "lobster_buffet_incident_list",
      label: "Lobster Buffet Incident List",
      description: "List active, stale, or closed incidents through the CLI core and configured adapter fixture.",
      parameters: {
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
      execute: (params) => {
        const args = ["incident", "list", "--status", optionalIncidentStatus(params.status), "--detail", optionalDetail(params.detail)];
        const adapterFixture = readString(params.adapter_fixture);
        const adapterConfig = readString(params.adapter_config) || options.defaultAdapterConfig;
        if (adapterFixture) {
          args.push("--adapter-fixture", adapterFixture);
        } else if (adapterConfig) {
          args.push("--adapter-config", adapterConfig);
        } else {
          args.push("--adapter-fixture", options.defaultAdapterFixture);
        }
        return runCli(args, options);
      },
    }),
    createTool({
      name: "lobster_buffet_alignment_scan",
      label: "Lobster Buffet Alignment Scan",
      description: "Scan project intent, backlog, and artifact evidence through the CLI core.",
      parameters: {
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
      execute: (params) => {
        const args = ["alignment", "scan", "--source", optionalAlignmentSource(params.source), "--detail", optionalDetail(params.detail)];
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
        const adapterFixture = readString(params.adapter_fixture);
        const adapterConfig = readString(params.adapter_config) || options.defaultAdapterConfig;
        if (adapterFixture) {
          args.push("--adapter-fixture", adapterFixture);
        } else if (adapterConfig) {
          args.push("--adapter-config", adapterConfig);
        } else {
          args.push("--adapter-fixture", options.defaultAdapterFixture);
        }
        return runCli(args, options);
      },
    }),
    createTool({
      name: "lobster_buffet_review_list",
      label: "Lobster Buffet Review List",
      description: "List active, blocked, or closed review sessions through the CLI core and configured adapter fixture.",
      parameters: {
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
      execute: (params) => {
        const args = ["review", "list", "--status", optionalReviewStatus(params.status), "--detail", optionalDetail(params.detail)];
        const adapterFixture = readString(params.adapter_fixture);
        const adapterConfig = readString(params.adapter_config) || options.defaultAdapterConfig;
        if (adapterFixture) {
          args.push("--adapter-fixture", adapterFixture);
        } else if (adapterConfig) {
          args.push("--adapter-config", adapterConfig);
        } else {
          args.push("--adapter-fixture", options.defaultAdapterFixture);
        }
        return runCli(args, options);
      },
    }),
    createTool({
      name: "lobster_buffet_heartbeat_packet",
      label: "Lobster Buffet Heartbeat Packet",
      description: "Build a compact read-only status packet through the CLI core and configured adapter fixture.",
      parameters: {
        type: "object",
        additionalProperties: false,
        properties: {
          detail: {
            type: "string",
            description: "Heartbeat detail level.",
            enum: ["summary", "full"],
          },
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
      execute: (params) => {
        const args = ["heartbeat", "packet", "--detail", optionalDetail(params.detail)];
        const adapterFixture = readString(params.adapter_fixture);
        const adapterConfig = readString(params.adapter_config) || options.defaultAdapterConfig;
        if (adapterFixture) {
          args.push("--adapter-fixture", adapterFixture);
        } else if (adapterConfig) {
          args.push("--adapter-config", adapterConfig);
        } else {
          args.push("--adapter-fixture", options.defaultAdapterFixture);
        }
        return runCli(args, options);
      },
    }),
    createTool({
      name: "lobster_buffet_heartbeat_check",
      label: "Lobster Buffet Heartbeat Check",
      description: "Check whether a visible heartbeat is due through the CLI core and configured adapter fixture.",
      parameters: {
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
      execute: (params) => {
        const args = ["heartbeat", "check", "--scope", optionalHeartbeatScope(params.scope), "--detail", optionalDetail(params.detail)];
        const adapterFixture = readString(params.adapter_fixture);
        const adapterConfig = readString(params.adapter_config) || options.defaultAdapterConfig;
        if (adapterFixture) {
          args.push("--adapter-fixture", adapterFixture);
        } else if (adapterConfig) {
          args.push("--adapter-config", adapterConfig);
        } else {
          args.push("--adapter-fixture", options.defaultAdapterFixture);
        }
        return runCli(args, options);
      },
    }),
  ];
}

module.exports = {
  id: "lobster-buffet",
  name: "Lobster Buffet",
  description: "OpenClaw dynamic tool wrapper for Lobster Buffet CLI-core operations.",
  register(api) {
    const options = createOptions(isRecord(api.pluginConfig) ? api.pluginConfig : {});
    for (const tool of tools(options)) {
      api.registerTool(tool, { name: tool.name });
    }
  },
  _test: {
    createOptions,
    defaultProjectRoot,
    runCli,
    tools,
  },
};
