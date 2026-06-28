import subprocess
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """轻量级 MCP 客户端，自动处理 initialize 握手"""
    
    def __init__(self, command: str = "axterminator", args: List[str] = None):
        self.command = command
        self.args = args or ["mcp", "serve"]
        self.process = None
        self._initialized = False
        self._request_id = 0

    def _start_process(self):
        """启动子进程（如果尚未启动或已终止）"""
        if self.process is None or self.process.poll() is not None:
            self.process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self._initialized = False

    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发送 JSON-RPC 请求并读取响应"""
        self._start_process()
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # 读取一行响应（MCP 协议每行一个 JSON）
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("MCP server closed connection")
        response = json.loads(line)
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        return response.get("result", {})

    def _initialize(self):
        """发送 initialize 请求（仅执行一次）"""
        if self._initialized:
            return
        self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "macagent", "version": "1.0"},
            "capabilities": {}
        })
        self._initialized = True

    def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具（自动先初始化）"""
        self._initialize()
        return self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

    # ---------- 具体工具方法 ----------
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