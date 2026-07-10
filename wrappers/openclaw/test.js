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

  const inspect = await call("lobster_buffet_project_inspect", {});
  if (inspect.project.name !== "lobster-buffet") {
    throw new Error("project inspect returned the wrong synthetic project");
  }

  const serialized = JSON.stringify({ description, inspect, list, plan });
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
