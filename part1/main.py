import signal, sys, time, numpy as np
from audio.recorder import AudioRecorder
from audio.stream_buffer import StreamBuffer
from stt.whisper_engine import transcribe_once
from llm.deepseek_client import DeepSeekClient
from ui.console_ui import ConsoleUI
from rich.console import Console

console = Console()
recorder = AudioRecorder()
buffer = StreamBuffer()
llm = DeepSeekClient()

def start():
    recorder.start_recording()
    buffer.clear()
    console.print("[cyan]🎤 开始录音，再按空格结束[/cyan]")

def stop():
    recorder.stop_recording()
    console.print("[yellow]⏹️ 录音结束，整合文本…[/yellow]")
    audio_np = np.array(recorder.full_audio, dtype="int16")
    if not audio_np.size:
        console.print("[red]未检测到语音[/red]")
        return
    text = transcribe_once(audio_np)
    ConsoleUI.print_asr(text)
    final = ConsoleUI.ask_edit(text)
    console.print(f"[ASK] {final}")
    for token in llm.chat(final):
        ConsoleUI.print_assistant(token)
    console.print()

ui = ConsoleUI(start, stop)

def sigint_handler(*_):
    console.print("\n[red]退出[/red]")
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

if __name__ == "__main__":
    recorder.start()          
    console.print("程序已启动，按空格开始/停止录音，Ctrl+C 退出", style="bold green")
    while True:
        time.sleep(0.1)