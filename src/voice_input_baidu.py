# src/voice_input_baidu.py
import os
import tempfile
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
from pydub import AudioSegment
from aip import AipSpeech
from src.config import Config


client = AipSpeech(Config.BAIDU_APP_ID, Config.BAIDU_API_KEY, Config.BAIDU_SECRET_KEY)

def record_audio(duration: int = 3, samplerate: int = 16000) -> np.ndarray:
    """
    从麦克风录音，返回音频数据 (numpy array, dtype=int16)
    """
    print(f"🎤 录音中... ({duration}秒)")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate,
                   channels=1, dtype='int16')
    sd.wait()  # 等待录音完成
    print("🎤 录音结束")
    return audio

def save_audio_to_wav(audio_data: np.ndarray, samplerate: int = 16000) -> str:
    """
    将音频数据保存为临时 WAV 文件，返回文件路径
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, samplerate, audio_data)
        return f.name

def listen_once_from_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        return f"错误：文件 {file_path} 不存在"
    try:
        # 使用 pydub 加载并转换为 16kHz 单声道
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        # 导出为临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio.export(tmp.name, format="wav")
            tmp_path = tmp.name
        # 读取转换后的数据
        with open(tmp_path, 'rb') as fp:
            audio_data = fp.read()
        os.unlink(tmp_path)
        # 调用百度 API
        result = client.asr(audio_data, 'wav', 16000, {'dev_pid': 1537})
        if result['err_no'] == 0:
            return result['result'][0]
        else:
            return f"识别错误 (err_no: {result['err_no']}): {result['err_msg']}"
    except Exception as e:
        return f"处理失败: {str(e)}"

def listen_for_command(duration: int = 3) -> str:
    """
    录音 → 保存 → 百度识别 → 返回文本
    """
    try:
        audio_data = record_audio(duration)
        temp_file = save_audio_to_wav(audio_data)
        text = listen_once_from_file(temp_file)
        os.unlink(temp_file)  # 删除临时文件
        return text
    except Exception as e:
        print(f"❌ 语音识别异常: {e}")
        return ""