# src/voice_service.py
from src.voice_input import listen_for_command as listen_vosk
from src.voice_input_baidu import listen_for_command as listen_baidu

# 通过修改这个变量来切换方案: 'vosk' 或 'baidu'
ACTIVE_PROVIDER = 'baidu'  # 改为 'vosk' 可切换回离线方案

def listen_for_command(timeout: int = 5) -> str:
    """统一的语音识别入口"""
    if ACTIVE_PROVIDER == 'baidu':
        print("🎤 正在使用百度语音识别...")
        # 百度方案中 duration 固定为 3 秒，也可以从 timeout 换算
        # 这里简单处理，默认 3 秒
        return listen_baidu(duration=3)
    else:
        return listen_vosk(timeout)