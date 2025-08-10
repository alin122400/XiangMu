# 语音转文本模块
from .whisper_engine import transcribe_once, transcribe_window

__all__ = ["transcribe_once", "transcribe_window"]