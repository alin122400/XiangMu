import threading, pyaudio, logging, numpy as np, webrtcvad
from array import array
from config import CHUNK, RATE, CHANNELS, FORMAT   

_logger = logging.getLogger(__name__)
_vad = webrtcvad.Vad(2)

class AudioRecorder(threading.Thread):
    daemon = True

    def __init__(self):
        super().__init__()
        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._is_recording = False
        self.full_audio = array("h")

    def start_recording(self):
        if self._is_recording:
            return
        self.full_audio = array("h")
        self._is_recording = True

    def stop_recording(self):
        self._is_recording = False

    @property
    def is_recording(self):
        return self._is_recording

    def run(self):
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
                _logger.error("read stream error: %s", e)
                continue
            pcm = np.frombuffer(data, np.int16)
            if _vad.is_speech(data, RATE):
                self.full_audio.extend(pcm)