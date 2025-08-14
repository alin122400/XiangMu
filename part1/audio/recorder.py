import threading
import pyaudio
import logging
import numpy as np
import webrtcvad
from array import array
from config import CHUNK, RATE, CHANNELS, FORMAT  

_logger = logging.getLogger(__name__)
_vad = webrtcvad.Vad(3)

class AudioRecorder(threading.Thread):
    """音频录制器，基于PyAudio实现实时音频采集与处理"""
    daemon = True

    def __init__(self):
        super().__init__()
        self._pa = pyaudio.PyAudio() 
        self._stream = None
        self._is_recording = False 
        self.full_audio = array("h")  
        self.realtime_buffer = array("h") 
        self.buffer_lock = threading.Lock()  

    def start_recording(self):
        """开始录音，初始化缓冲区"""
        if self._is_recording:
            return
        self.full_audio = array("h")
        self.realtime_buffer = array("h")
        self._is_recording = True

    def stop_recording(self):
        """停止录音"""
        self._is_recording = False

    def get_realtime_chunk(self, max_length=None):
        """
        获取实时音频片段
        :param max_length: 最大长度限制，None表示获取全部
        :return: 音频数据的numpy数组( dtype=int16 )，无数据时返回None
        """
        with self.buffer_lock:
            if not self.realtime_buffer:
                return None
            if max_length and len(self.realtime_buffer) > max_length:
                chunk = self.realtime_buffer[:max_length]
                self.realtime_buffer = self.realtime_buffer[max_length:]
            else:
                chunk = self.realtime_buffer
                self.realtime_buffer = array("h")
            return np.array(chunk, dtype="int16")

    @property
    def is_recording(self):
        """获取当前录音状态"""
        return self._is_recording

    def run(self):
        """线程主方法，持续采集音频数据"""
        self._stream = self._pa.open(
            format=getattr(pyaudio, f"pa{FORMAT}"),  
            channels=CHANNELS,  
            rate=RATE,  
            input=True, 
            frames_per_buffer=CHUNK, 
        )
        self._stream.start_stream()
        
        while True:
            if not self._is_recording:
                continue 
            try:
                data = self._stream.read(CHUNK, exception_on_overflow=False)
            except Exception as e:
                _logger.error("读取音频流失败: %s", e)
                continue
            
            pcm = np.frombuffer(data, np.int16)
            
            with self.buffer_lock:
                self.realtime_buffer.extend(pcm)
            
            if _vad.is_speech(data, RATE):
                self.full_audio.extend(pcm)