from src.system_client import SystemClient

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