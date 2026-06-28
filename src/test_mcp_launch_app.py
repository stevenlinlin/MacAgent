import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_launch_app():
    # ⚠️ 关键：确保这里的路径和文件名与你刚创建的 Server 一致
    server_params = StdioServerParameters(
        command="python",
        args=["src/mac_server.py"],  # 指向你的 Server 文件
        env=None
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # 执行握手初始化
                await session.initialize()
                print("✅ MCP Server 初始化成功！")
                
                # 列出可用工具，看看 launch_app 是否在里面
                tools = await session.list_tools()
                print("可用工具:", [tool.name for tool in tools.tools])
                
                # 调用工具打开微信
                result = await session.call_tool("launch_app", arguments={"app_name": "微信"})
                print("调用结果:", result.content[0].text)
                
    except ExceptionGroup as eg:
        print("❌ 捕获到 ExceptionGroup，详细错误如下：")
        for exc in eg.exceptions:
            import traceback
            traceback.print_exception(type(exc), exc, exc.__traceback__)
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_launch_app())
