import subprocess
import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MacOS_Launcher")

# 扩大映射字典，包含常见的别名和中英文
APP_NAME_MAP = {
    "微信": "WeChat",
    "wechat": "WeChat",
    "weixin": "WeChat",
    "safari": "Safari",
    "浏览器": "Safari",
    "终端": "Terminal",
    "terminal": "Terminal",
    "系统偏好设置": "System Preferences",
    "设置": "System Preferences",
    "音乐": "Music",
    "备忘录": "Notes",
    "照片": "Photos",
    "计算器": "Calculator",
    "日历": "Calendar",
    "邮件": "Mail",
    "appstore": "App Store",
    "app store": "App Store",
}

def get_actual_app_name(input_name: str) -> str:
    """从 LLM 可能传来的各种奇怪参数中，提取并映射正确的 App 名称"""
    # 1. 转换为小写并去除首尾空格，方便匹配
    cleaned_input = input_name.lower().strip()
    
    # 2. 如果完全匹配，直接返回
    if cleaned_input in APP_NAME_MAP:
        return APP_NAME_MAP[cleaned_input]
    
    # 3. 模糊匹配：如果输入包含在某个 key 中（例如输入"打开微信app"，包含"微信"）
    for key, value in APP_NAME_MAP.items():
        if key in cleaned_input:
            return value
            
    # 4. 如果映射表里没有，尝试提取引号或书名号里的内容（LLM 常见输出格式）
    # 例如输入：'请打开名为"WeChat"的程序' -> 提取 WeChat
    match = re.search(r'["\u201c\u300a](.*?)["\u201d\u300b]', input_name)
    if match:
        extracted = match.group(1).lower()
        if extracted in APP_NAME_MAP:
            return APP_NAME_MAP[extracted]
        return extracted # 提取出来的原样传给系统试试
            
    # 5. 兜底：原样返回（交给 macOS 的 open 命令去处理）
    return input_name

@mcp.tool()
def launch_app(app_name: str) -> str:
    """在 macOS 上启动指定的应用程序。当用户要求打开、启动或运行某个软件时使用此工具。
    
    Args:
        app_name: 应用程序的名称，例如 '微信'、'Safari'、'WeChat'
    """
    try:
        # 获取真实的 macOS 应用名称
        actual_app_name = get_actual_app_name(app_name)
        
        # macOS 上使用 open -a 命令打开应用
        result = subprocess.run(
            ["open", "-a", actual_app_name], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if result.returncode == 0:
            return f"✅ {actual_app_name} 启动成功！"
        else:
            # 将 macOS 的报错原样返回，方便调试
            return f"❌ 启动失败: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return f"❌ 启动超时"
    except Exception as e:
        return f"❌ 发生未知错误: {str(e)}"

@mcp.tool()
def volume_control(action: str, value: int = None) :
    """
    控制音量
    action: 'up', 'down', 'mute', 'set'
    value: 当 action='set' 时，目标音量 0-100
    """
    try:
        # 获取当前音量
        get_vol_cmd = 'output volume of (get volume settings)'
        current = int(subprocess.check_output(["osascript", "-e", get_vol_cmd], text=True).strip())
        
        if action == "mute":
            # 静音切换（可通过 set volume output muted true/false）
            # 这里简化：直接设置音量为0
            target = 0
        elif action == "up":
            target = min(current + 10, 100)
        elif action == "down":
            target = max(current - 10, 0)
        elif action == "set":
            if value is None or not (0 <= value <= 100):
                return {"success": False, "message": "音量值必须在 0 到 100 之间"}
            target = value
        else:
            return {"success": False, "message": f"不支持的操作: {action}"}
        
        # 执行设置
        subprocess.run(["osascript", "-e", f"set volume output volume {target}"], check=True, capture_output=True)
        return {"success": True, "message": f"音量已{'设为' if action=='set' else '调'}{target}%"}
    except Exception as e:
        return {"success": False, "message": f"调节失败: {str(e)}"}
    
import subprocess
import time
import pyautogui
import pyperclip
import pygetwindow as gw

# ---------- 方法1：纯 AppleScript ----------
def _send_with_applescript(contact: str, message: str) -> dict:
    """使用 AppleScript + 剪贴板粘贴（支持中文和特殊字符，如空格）"""
    # 转义双引号，防止 AppleScript 语法错误
    contact_escaped = contact.replace('"', '\\"')
    message_escaped = message.replace('"', '\\"')

    script = f'''
    -- 将联系人写入剪贴板
    set the clipboard to "{contact_escaped}"
    tell application "WeChat"
        activate
        delay 1
    end tell
    tell application "System Events"
        -- 打开搜索框
        keystroke "f" using command down
        delay 0.6
        -- 清空搜索框（全选+删除）
        keystroke "a" using command down
        delay 0.2
        key code 51
        delay 0.3
        -- 粘贴联系人
        keystroke "v" using command down
        delay 0.8
        -- 按回车选择第一个联系人
        key code 36
        delay 0.8
    end tell
    -- 将消息写入剪贴板
    set the clipboard to "{message_escaped}"
    tell application "System Events"
        -- 清空输入框（假设已获得焦点）
        keystroke "a" using command down
        delay 0.2
        key code 51
        delay 0.3
        -- 粘贴消息
        keystroke "v" using command down
        delay 0.5
        -- 回车发送
        key code 36
    end tell
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode != 0:
        raise RuntimeError(f"AppleScript 执行失败: {result.stderr.strip()}")
    return {"success": True, "message": f"消息已发送给 {contact}"}

# ---------- 方法2：PyAutoGUI + 剪贴板 ----------
def _send_with_pyautogui(contact: str, message: str) -> dict:
    """使用 PyAutoGUI + 剪贴板（支持中文，不受输入法干扰）"""
    try:
        # 1. 激活微信
        subprocess.run(["osascript", "-e", 'tell application "WeChat" to activate'], check=True)
        time.sleep(1.2)

        # 2. 确保焦点在微信窗口（可选，使用 pygetwindow 精确定位）
        try:
            win = gw.getWindowsWithTitle('微信')[0]
            win.activate()
            time.sleep(0.3)
            # 点击窗口中心区域聚焦
            pyautogui.click(win.left + win.width//2, win.top + win.height//2 - 80)
        except:
            pyautogui.click(500, 300)  # 默认坐标
        time.sleep(0.3)

        # 3. 打开搜索框
        pyautogui.hotkey('command', 'f')
        time.sleep(0.6)
        # 清空
        pyautogui.hotkey('command', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.3)

        # 4. 粘贴联系人
        pyperclip.copy(contact)
        pyautogui.hotkey('command', 'v')
        time.sleep(1.0)
        pyautogui.press('enter')
        time.sleep(0.8)

        # 5. 粘贴消息
        pyautogui.hotkey('command', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.3)
        pyperclip.copy(message)
        pyautogui.hotkey('command', 'v')
        time.sleep(0.5)
        pyautogui.press('enter')

        return {"success": True, "message": f"消息已发送给 {contact}"}
    except Exception as e:
        return {"success": False, "message": f"PyAutoGUI 发送失败: {str(e)}"}

@mcp.tool()
def send_wechat_message(contact: str, message: str):
    """
    发送微信消息 - 优先使用 AppleScript，失败则回退到 PyAutoGUI
    """
    # 尝试方法1：AppleScript
    try:
        result = _send_with_applescript(contact, message)
        print("✅ 使用 AppleScript 发送成功")
        return result
    except Exception as e:
        print(f"⚠️ AppleScript 发送失败 ({e})，正在回退到 PyAutoGUI...")
        # 回退方法2：PyAutoGUI
        try:
            result = _send_with_pyautogui(contact, message)
            if result.get("success"):
                print("✅ 使用 PyAutoGUI 发送成功")
                return result
            else:
                # 如果 PyAutoGUI 也失败，返回错误信息
                return {"success": False, "message": f"所有发送方式均失败: {result.get('message', '未知错误')}"}
        except Exception as e2:
            return {"success": False, "message": f"PyAutoGUI 回退失败: {str(e2)}"}

if __name__ == "__main__":
    mcp.run()
