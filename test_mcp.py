import sys
from pathlib import Path
# 将项目根目录添加到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_client_simple import SimpleMCPClient

def main():
    mcp = SimpleMCPClient()
    try:
        success = mcp.launch_app("WeChat")
        print(f"✅ 微信启动结果: {success}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
