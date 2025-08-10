from collections import deque
from config import RATE, RING_SEC   

class StreamBuffer:
    def __init__(self):
        self._buf = deque(maxlen=RATE * RING_SEC)

    def extend(self, pcm):
        self._buf.extend(pcm)

    def clear(self):
        self._buf.clear()

    def to_numpy(self):
        from numpy import array
        return array(self._buf, dtype="int16")