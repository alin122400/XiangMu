import whisper, threading, opencc, numpy as np
from config import WHISPER_MODEL  

_lock = threading.Lock()
_model = whisper.load_model(WHISPER_MODEL)
_converter = opencc.OpenCC("t2s")

def transcribe_once(audio_np: np.ndarray) -> str:
    """整段音频转文字"""
    with _lock:
        result = _model.transcribe(audio_np.astype("float32") / 32768.0,
                                   language="zh", fp16=False)
    return _converter.convert(result["text"].strip())

def transcribe_window(audio_np: np.ndarray) -> str:
    """实时窗口转文字（更快）"""
    with _lock:
        result = _model.transcribe(audio_np.astype("float32") / 32768.0,
                                   language="zh", fp16=False,
                                   condition_on_previous_text=False)
    return _converter.convert(result["text"].strip())