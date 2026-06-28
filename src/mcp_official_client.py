import asyncio
import json
import traceback
from typing import Any, Dict, List, Optional

class MCPOfficialClient:
    def __init__(self, command: str = "python", args: List[str] = None):
        self.command = command
        self.args = args or ["-m", "src.mac_server"]  # 模块方式

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        print(f"🔧 调用工具: {tool_name}, 参数: {arguments}")
        init_req = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "macagent", "version": "1.0.0"},
                "capabilities": {}
            }
        }
        init_notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        tool_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }

        proc = await asyncio.create_subprocess_exec(
            self.command, *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT  # 合并 stderr
        )
        try:
            proc.stdin.write((json.dumps(init_req) + "\n").encode())
            await proc.stdin.drain()
            print("📤 已发送 initialize 请求")

            init_resp = None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                print(f"📥 收到行(init): {line_str}")
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                    if data.get("id") == 0:
                        init_resp = data
                        break
                except json.JSONDecodeError:
                    print(f"⚠️ 非JSON行(init): {line_str}")
                    continue
            if init_resp is None:
                raise RuntimeError("未收到初始化响应")
            if "error" in init_resp:
                raise RuntimeError(f"初始化错误: {init_resp['error']}")
            print("✅ 初始化成功")

            proc.stdin.write((json.dumps(init_notification) + "\n").encode())
            await proc.stdin.drain()
            print("📤 已发送 initialized 通知")

            proc.stdin.write((json.dumps(tool_req) + "\n").encode())
            await proc.stdin.drain()
            print("📤 已发送 tools/call 请求")

            tool_resp = None
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                print(f"📥 收到行(tool): {line_str}")
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                    if data.get("id") == 1:
                        tool_resp = data
                        break
                except json.JSONDecodeError:
                    print(f"⚠️ 非JSON行(tool): {line_str}")
                    continue
            if tool_resp is None:
                raise RuntimeError("未收到工具调用响应")
            if "error" in tool_resp:
                raise RuntimeError(f"MCP错误: {tool_resp['error']}")
            result = tool_resp.get("result", {})
            print(f"📋 工具返回结果: {result}")
            return result
        except Exception as e:
            print("❌ _call_tool 发生异常")
            traceback.print_exc()
            raise
        finally:
            proc.stdin.close()
            await proc.wait()
            print("🔚 子进程已退出")

    async def launch_app(self, app_name: str) -> bool:
        try:
            result = await self._call_tool("launch_app", {"app_name": app_name})
            # 如果服务器返回字典（含 success），则直接取
            if isinstance(result, dict) and "success" in result:
                return result.get("success", False)
            # 否则尝试从 content 中提取文本判断（兼容字符串返回）
            content = result.get("content", [])
            if content and isinstance(content, list):
                text = content[0].get("text", "")
                return "✅" in text
            return False
        except Exception as e:
            print(f"❌ launch_app 失败: {e}")
            traceback.print_exc()
            return False
    # ---------- 统一工具调用封装 ----------
    async def _call_and_parse(self, tool_name: str, args: Dict = None) -> bool:
        """调用工具并解析结果，返回布尔值表示成功/失败"""
        result = await self._call_tool(tool_name, args or {})
        if isinstance(result, dict):
            return result.get("success", True)
        return False
    async def volume_up(self) -> bool:
        return await self._call_and_parse("volume_control", {"action": "up"})

    async def volume_down(self) -> bool:
        return await self._call_and_parse("volume_control", {"action": "down"})

    async def set_volume(self, value: int) -> bool:
        return await self._call_and_parse("volume_control", {"action": "set", "value": value})

    async def mute_volume(self) -> bool:
        return await self._call_and_parse("volume_control", {"action": "mute"})
    
    async def send_wechat_message(self, contact: str, message: str) -> bool:
        return await self._call_and_parse("send_wechat_message", {"contact": contact, "message": message})
