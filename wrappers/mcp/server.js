#!/usr/bin/env node

const readline = require("node:readline");
const wrapper = require("./index.js");

const PROTOCOL_VERSION = "2024-11-05";

function jsonRpcResult(id, result) {
  return {
    jsonrpc: "2.0",
    id,
    result,
  };
}

function jsonRpcError(id, code, message, data = {}) {
  return {
    jsonrpc: "2.0",
    id: id === undefined ? null : id,
    error: {
      code,
      message,
      data,
    },
  };
}

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function toolDefinitions() {
  return wrapper.listTools().tools.map((tool) => ({
    name: tool.name,
    title: tool.title,
    description: tool.description,
    inputSchema: tool.inputSchema,
  }));
}

function initializeResult() {
  return {
    protocolVersion: PROTOCOL_VERSION,
    capabilities: {
      tools: {},
    },
    serverInfo: {
      name: "lobster-buffet-mcp-wrapper",
      version: "0.1.0",
    },
  };
}

function handleRequest(request, config = {}) {
  if (!isRecord(request) || request.jsonrpc !== "2.0" || typeof request.method !== "string") {
    return jsonRpcError(isRecord(request) ? request.id : null, -32600, "Invalid JSON-RPC request.");
  }

  if (request.method === "notifications/initialized") {
    return undefined;
  }

  if (request.method === "initialize") {
    return jsonRpcResult(request.id, initializeResult());
  }

  if (request.method === "tools/list") {
    return jsonRpcResult(request.id, { tools: toolDefinitions() });
  }

  if (request.method === "tools/call") {
    const params = isRecord(request.params) ? request.params : {};
    const toolName = typeof params.name === "string" ? params.name : "";
    const toolArgs = isRecord(params.arguments) ? params.arguments : {};
    try {
      return jsonRpcResult(request.id, wrapper.callTool(toolName, toolArgs, config));
    } catch (error) {
      return jsonRpcError(request.id, -32603, "MCP tool call failed.", {
        message: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return jsonRpcError(request.id, -32601, `Unsupported MCP method: ${request.method}`);
}

function handleJsonRpcLine(line, config = {}) {
  try {
    return handleRequest(JSON.parse(line), config);
  } catch (error) {
    return jsonRpcError(null, -32700, "Parse error.", {
      message: error instanceof Error ? error.message : String(error),
    });
  }
}

function startStdioServer(config = {}) {
  const reader = readline.createInterface({
    input: process.stdin,
    crlfDelay: Infinity,
  });

  reader.on("line", (line) => {
    if (!line.trim()) {
      return;
    }
    const response = handleJsonRpcLine(line, config);
    if (response !== undefined) {
      process.stdout.write(`${JSON.stringify(response)}\n`);
    }
  });
}

if (require.main === module) {
  startStdioServer();
}

module.exports = {
  PROTOCOL_VERSION,
  handleJsonRpcLine,
  handleRequest,
  initializeResult,
  startStdioServer,
  toolDefinitions,
};
