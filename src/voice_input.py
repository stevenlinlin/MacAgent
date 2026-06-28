import os
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# 模型路径：项目根目录下的 vosk-model-cn-0.22
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vosk-model-cn-0.22")

def listen_for_command(timeout: int = 5) -> str:
    """
    使用 Vosk 离线识别中文语音
    """
    if not os.path.exists(MODEL_PATH):
        print(f"❌ 模型目录不存在: {MODEL_PATH}")
        print("请下载 Vosk 中文模型并解压到项目根目录的 vosk-model-cn-0.22")
        return ""

    try:
        model = Model(MODEL_PATH)
        recognizer = KaldiRecognizer(model, 16000)
        recognizer.SetWords(False)

        q = queue.Queue()
        def callback(indata, frames, time, status):
            q.put(bytes(indata))

        print("🎤 请说话...")
        with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None,
                               dtype='int16', channels=1, callback=callback):
            # 等待识别结果（简单循环，无超时）
            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        print(f"📝 识别结果: {text}")
                        return text
    except Exception as e:
        print(f"❌ 语音识别异常: {e}")
        return ""
    return ""