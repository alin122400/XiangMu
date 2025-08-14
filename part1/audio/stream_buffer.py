from collections import deque
from config import RATE, RING_SEC  

class StreamBuffer:
    """音频流缓冲区，用于存储实时音频片段并提供numpy转换功能"""
    def __init__(self):
        self._buf = deque(maxlen=RATE * RING_SEC)

    def extend(self, pcm):
        """添加音频数据到缓冲区"""
        self._buf.extend(pcm)

    def clear(self):
        """清空缓冲区"""
        self._buf.clear()

    def to_numpy(self):
        """将缓冲区数据转换为numpy数组"""
        from numpy import array
        return array(self._buf, dtype="int16")