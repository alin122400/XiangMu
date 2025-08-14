import signal
import sys
import time
import numpy as np
import threading
from config import RATE, CHUNK
from audio.recorder import AudioRecorder
from audio.stream_buffer import StreamBuffer
from stt.whisper_engine import transcribe_window
from llm.deepseek_client import DeepSeekClient
from ui.console_ui import ConsoleUI
from rich.console import Console
import webrtcvad

# 初始化控制台
console = Console()
# 初始化核心组件
recorder = AudioRecorder()  # 音频录制器
buffer = StreamBuffer()  # 音频缓冲区
llm = DeepSeekClient()  # 大模型客户端
realtime_thread = None  # 实时处理线程
stop_event = threading.Event()  # 线程停止事件
realtime_vad = webrtcvad.Vad(3)  # 实时语音活动检测器(高灵敏度)

def start():
    """开始录音与实时处理"""
    global realtime_thread, stop_event
    stop_event.clear()  
    ui.reset_realtime()  #
    recorder.start_recording()  
    buffer.clear()  
    console.print("🎤 开始录音，再按空格结束")
    
    realtime_thread = threading.Thread(target=realtime_processing)
    realtime_thread.daemon = True 
    realtime_thread.start()

def is_voice_active(audio_chunk: np.ndarray, rate: int, chunk_size: int) -> bool:
    """
    判断音频片段是否包含有效语音
    param audio_chunk: 音频数据
    param rate: 采样率
    param chunk_size: 块大小
    return: 包含有效语音返回True，否则False
    """
    audio_bytes = audio_chunk.tobytes()
    frame_duration = chunk_size * 1000 // rate
    if frame_duration not in [10, 20, 30]:
        return False
    
    frame_count = 0  # 总帧数
    voice_frame_count = 0  # 语音帧数
    for i in range(0, len(audio_bytes), chunk_size * 2): 
        frame = audio_bytes[i:i + chunk_size * 2]
        if len(frame) < chunk_size * 2:
            break
        frame_count += 1
        if realtime_vad.is_speech(frame, rate):
            voice_frame_count += 1
    
    return voice_frame_count / frame_count > 0.5 if frame_count > 0 else False

def realtime_processing():
    """实时音频处理线程：语音检测与实时转文字"""
    last_voice_time = time.time()  # 最后一次检测到语音的时间
    silence_timeout = 2  # 静音超时时间
    last_text = ""  # 上一次识别的文本
    while not stop_event.is_set() and recorder.is_recording:
        audio_chunk = np.array(recorder.full_audio[-RATE*5:], dtype="int16")
        if len(audio_chunk) < RATE*0.5:
            time.sleep(0.2)
            continue
        
        if is_voice_active(audio_chunk, RATE, CHUNK):
            last_voice_time = time.time()  
            current_text = transcribe_window(audio_chunk)
            if current_text and current_text != last_text:
                ui.update_realtime(current_text)
                console.print(f"[实时] {current_text}")
                last_text = current_text  
        else:
            if time.time() - last_voice_time > silence_timeout:
                pass
            else:
                time.sleep(0.2)
                continue
        
        time.sleep(0.3) 

def stop():
    """停止录音与实时处理，执行后续流程"""
    global stop_event
    stop_event.set()  
    recorder.stop_recording() 
    if realtime_thread:
        realtime_thread.join()
    
    console.print("⏹️ 录音结束，整合文本…")
    final_text = ui.get_last_realtime_text().strip()
    if not final_text:
        console.print("未检测到有效语音内容")
        return
    
    ConsoleUI.print_asr(final_text)
    edited_text = ConsoleUI.ask_edit(final_text)
    console.print(f"[ASK] {edited_text}")
    
    for token in llm.chat(edited_text):
        ConsoleUI.print_assistant(token)
    console.print()

ui = ConsoleUI(start, stop)

def sigint_handler(*_):
    """处理Ctrl+C退出信号"""
    console.print("\n退出")
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

if __name__ == "__main__":
    recorder.start()  
    console.print("程序已启动，按空格开始/停止录音，Ctrl+C 退出", style="bold green")
    while True:
        time.sleep(0.1)