import subprocess
import logging

logger = logging.getLogger(__name__)

class SystemClient:
    """直接调用 macOS 系统命令（无需 MCP）"""
    
    def launch_app(self, app_name: str) -> bool:
        """启动 macOS 应用"""
        try:
            result = subprocess.run(
                ["open", "-a", app_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True
            else:
                logger.error(f"启动 {app_name} 失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"启动 {app_name} 异常: {e}")
            return False

    def activate_app(self, app_name: str) -> bool:
        """将应用置于前台"""
        try:
            script = f'tell application "{app_name}" to activate'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"激活 {app_name} 异常: {e}")
            return False