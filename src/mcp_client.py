import subprocess
import json
from typing import Any, Dict, List, Optional

class SimpleMCPClient:
    """MCP 客户端：每次调用工具时创建独立子进程"""
    
    def __init__(self, command: str = "axterminator", args: List[str] = None):
        self.command = command
        self.args = args or ["mcp", "serve"]

    def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # 构建 initialize 请求（必须第一个）
        init_req = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "macagent", "version": "1.0"},
                "capabilities": {}
            }
        }
        # 构建工具调用请求
        tool_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        # 拼接两个请求（每行一个 JSON）
        input_text = json.dumps(init_req) + "\n" + json.dumps(tool_req) + "\n"
        
        # 执行子进程
        result = subprocess.run(
            [self.command] + self.args,
            input=input_text,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"MCP process failed (code {result.returncode}): {result.stderr}")
        
        # 解析输出（通常返回两行，第二行是工具调用结果）
        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]
        if not lines:
            raise RuntimeError("No response from MCP server")
        # 取最后一行作为工具调用响应
        last_response = json.loads(lines[-1])
        if "error" in last_response:
            raise RuntimeError(f"MCP error: {last_response['error']}")
        return last_response.get("result", {})

    # ---------- 工具方法 ----------
    def launch_app(self, app_name: str) -> bool:
        result = self._call_tool("ax_launch_app", {"app_name": app_name})
        return result.get("success", False)

    def click(self, query: str) -> bool:
        result = self._call_tool("ax_click", {"query": query})
        return result.get("success", False)

    def type_text(self, text: str) -> bool:
        result = self._call_tool("ax_type", {"text": text})
        return result.get("success", False)

    def press_key(self, key: str) -> bool:
        result = self._call_tool("ax_press_key", {"key": key})
        return result.get("success", False)

    def screenshot(self) -> str:
        result = self._call_tool("ax_screenshot", {})
        return result.get("image", "")