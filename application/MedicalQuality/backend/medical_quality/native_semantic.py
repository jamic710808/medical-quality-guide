"""通過原生 stdio MCP 協議調用語義工具；運行身份只有讀權限。"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from .config import PROJECT, WORKSPACE

READ_TOOLS = {"browse_semantics", "resolve_semantics", "validate_semantics", "list_versions"}


def call_tool(name: str, arguments: dict, *, construction=False):
    if not construction and name not in READ_TOOLS:
        raise PermissionError("運行端不得建設、演化、激活或發佈本體")
    workspace = PROJECT / ".evoontology"
    if arguments.get("workspace") and arguments["workspace"] != str(workspace):
        raise PermissionError("語義工具不得跳出項目建設空間")
    arguments = {**arguments, "workspace": str(workspace)}
    launcher = WORKSPACE / ".agents/vendor/evoontology/scripts/launch_evo_semantic_mcp"
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "medical-quality", "version": "0.1.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": arguments}},
    ]
    process = subprocess.run(
        [str(launcher)],
        input="\n".join(json.dumps(x, ensure_ascii=False) for x in requests) + "\n",
        capture_output=True,
        text=True,
        timeout=45,
        env={**os.environ, "EVO_ONTOLOGY_PYTHON": sys.executable, "EVO_ONTOLOGY_DEBUG": ""},
    )
    if process.returncode:
        raise RuntimeError("原生語義 MCP 未能運行")
    response = next(
        (json.loads(line) for line in process.stdout.splitlines() if json.loads(line).get("id") == 2), None
    )
    if not response or "error" in response:
        raise RuntimeError("語義工具調用未產生有效協議結果")
    result = response["result"]
    text = next((c["text"] for c in result.get("content", []) if c["type"] == "text"), "{}")
    parsed = json.loads(text)
    if result.get("isError"):
        raise RuntimeError(str(parsed.get("message", "native_semantic_error")))
    return parsed
