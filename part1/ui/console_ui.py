from rich.console import Console
from prompt_toolkit import prompt
import keyboard

console = Console()

class ConsoleUI:
    def __init__(self, start_cb, stop_cb):
        self.start_cb = start_cb
        self.stop_cb = stop_cb
        keyboard.add_hotkey("space", self._toggle)

    def _toggle(self):
        if getattr(self, "_recording", False):
            self._recording = False
            self.stop_cb()
        else:
            self._recording = True
            self.start_cb()

    @staticmethod
    def print_asr(text: str):
        console.print(f"[ASR] {text}", style="dim")

    @staticmethod
    def print_assistant(text: str):
        console.print(text, end="")

    @staticmethod
    def ask_edit(default: str) -> str:
        try:
            edited = prompt("如需修改识别内容，请直接编辑后回车：", default=default).strip()
            return edited or default
        except KeyboardInterrupt:
            return default