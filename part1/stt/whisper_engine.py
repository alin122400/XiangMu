import whisper
import threading
import opencc
import numpy as np
from config import WHISPER_MODEL  

_lock = threading.Lock()
_model = whisper.load_model(WHISPER_MODEL)
_converter = opencc.OpenCC("t2s")

def transcribe_once(audio_np: np.ndarray) -> str:
    """
    单次语音转文字(适用于完整音频片段)
    :param audio_np: 音频数据(numpy数组)
    :return: 转换后的文本(简体中文)
    """
    with _lock: 
        result = _model.transcribe(
            audio_np.astype("float32") / 32768.0,  
            language="zh",  
            fp16=False
        )
    return _converter.convert(result["text"].strip())

def transcribe_window(audio_np: np.ndarray) -> str:
    """
    实时窗口语音转文字
    param audio_np: 音频数据
    return: 转换后的文本，无语音时返回空字符串
    """
    with _lock:  
        result = _model.transcribe(
            audio_np.astype("float32") / 32768.0, 
            language="zh",
            fp16=False,
            condition_on_previous_text=True,  
            temperature=0.3,  
            no_speech_threshold=0.7 
        )
    if result.get("no_speech_prob", 0.0) > 0.7:
        return ""
    return _converter.convert(result["text"].strip())