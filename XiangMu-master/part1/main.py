import signal
import sys
import time
import numpy as np
from audio.recorder import AudioRecorder
from audio.stream_buffer import StreamBuffer
from stt.whisper_engine import transcribe_once
from llm.deepseek_client import DeepSeekClient
from ui.console_ui import ConsoleUI
from rich.console import Console

# 文件操作
from file_operations import parse_file_operation, execute_file_operation

# 翻译
from googletrans import Translator

# 天气查询
from temperature import query_weather

# 新增：笔记助手
from note_assistant import NoteAssistant


console = Console()
recorder = AudioRecorder()
buffer = StreamBuffer()
llm = DeepSeekClient()
translator = Translator()
note_ai = NoteAssistant()

# 当前功能
function_type = None


# ===========================
# 选择功能（不阻塞录音线程）
# ===========================
def select_function():
    global function_type

    console.print("\n[bold blue]请选择功能：[/bold blue]")
    console.print("[green]1.[/green] 文件操作")
    console.print("[green]2.[/green] 翻译")
    console.print("[green]3.[/green] 天气查询")
    console.print("[green]4.[/green] 笔记助手")
    console.print("[green]5.[/green] 退出程序\n")

    while True:
        choice = input("请输入选项(1/2/3/4/5)：").strip()
        if choice in ['1', '2', '3', '4']:
            function_type = choice
            return
        elif choice == '5':
            console.print("[red]程序退出[/red]")
            sys.exit(0)
        else:
            console.print("[red]无效输入，请重新输入[/red]")


# ===========================
# 开始录音
# ===========================
def start():
    recorder.start_recording()
    buffer.clear()

    msg = {
        '1': "🎤 说出你的文件操作需求…",
        '2': "🎤 说出要翻译的内容…",
        '3': "🎤 说出要查询天气的城市…",
        '4': "🎤 说出笔记指令，例如：'记录明天买菜'、'搜索 作业'、'总结我所有笔记'…"
    }
    console.print(f"[cyan]{msg.get(function_type, '')}[/cyan]")


# ===========================
# 停止录音 + 功能执行
# ===========================
def stop():
    global function_type

    recorder.stop_recording()
    console.print("[yellow]⏹️ 正在识别语音…[/yellow]")

    audio_np = np.array(recorder.full_audio, dtype="int16")
    if not audio_np.size:
        console.print("[red]未检测到语音，请重试[/red]")
        return

    # ASR
    text = transcribe_once(audio_np)
    ConsoleUI.print_asr(text)
    final_asr = ConsoleUI.ask_edit(text)

    if not final_asr.strip():
        console.print("[red]空内容，请重试[/red]")
        return

    # ===========================
    # 功能 1：文件操作
    # ===========================
    if function_type == '1':
        console.print(f"[yellow]你的输入：{final_asr}[/yellow]")

        final_result = ConsoleUI.ask_edit(final_asr)

        op_type, obj_type, name, path = parse_file_operation(final_result)
        if not op_type:
            console.print("[red]无法解析指令[/red]")
        else:
            success, msg = execute_file_operation(op_type, obj_type, name, path)
            if success:
                console.print(f"[green]成功：{msg}[/green]")
            else:
                console.print(f"[red]失败：{msg}[/red]")

    # ===========================
    # 功能 2：翻译
    # ===========================
    elif function_type == '2':
        try:
            detect = translator.detect(final_asr)
            dest = "en" if detect.lang.startswith("zh") else "zh-cn"
            translated = translator.translate(final_asr, dest=dest)
            console.print(f"[yellow]翻译：{translated.text}[/yellow]")
        except Exception as e:
            console.print(f"[red]翻译失败：{e}[/red]")

    # ===========================
    # 功能 3：天气查询
    # ===========================
    elif function_type == '3':
        console.print("[blue]正在查询天气…[/blue]")
        result = query_weather(final_asr)
        console.print(f"[green]天气结果：{result}[/green]")

    # ===========================
    # 功能 4：笔记助手
    # ===========================
    elif function_type == '4':
        console.print("[blue]正在处理笔记…[/blue]")
        result = note_ai.process(final_asr)
        console.print(f"[green]{result}[/green]")

    # ===========================
    # 🔥 功能结束：是否返回主菜单
    # ===========================
    console.print("[blue]功能结束：按回车继续当前功能，输入 q 返回主菜单：[/blue]", end=" ")
    user_cmd = input().strip().lower()

    if user_cmd == "q":
        select_function()  # ❗ 不退出，而是返回菜单


# ===========================
# UI 初始化
# ===========================
ui = ConsoleUI(start, stop)


# ===========================
# Ctrl + C 处理
# ===========================
def sigint_handler(*_):
    console.print("\n[red]程序中断退出[/red]")
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)


# ===========================
# 主程序
# ===========================
if __name__ == "__main__":
    console.print("程序已启动。按空格开始/停止录音", style="bold green")

    select_function()

    recorder.start()

    while True:
        time.sleep(0.1)


