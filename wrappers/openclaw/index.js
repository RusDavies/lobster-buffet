const { execFileSync } = require("node:child_process");
const path = require("node:path");

const DEFAULT_ADAPTER_FIXTURE = "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json";

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
        },
      },
      execute: (params) => {
        return runCli(
          ["project", "inspect", "--adapter-fixture", readString(params.adapter_fixture) || options.defaultAdapterFixture],
          options,
        );
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
