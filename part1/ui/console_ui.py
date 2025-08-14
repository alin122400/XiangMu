from rich.console import Console
from prompt_toolkit import prompt
import keyboard

console = Console()

class ConsoleUI:
    """控制台用户界面，处理用户交互与输出展示"""
    def __init__(self, start_cb, stop_cb):
        self.start_cb = start_cb  
        self.stop_cb = stop_cb 
        self.realtime_text = "" 
        self.last_segment = "" 
        keyboard.add_hotkey("space", self._toggle)

    def reset_realtime(self):
        """重置实时文本缓存"""
        self.realtime_text = ""
        self.last_segment = ""

    def update_realtime(self, text: str):
        """更新实时识别的文本"""
        self.realtime_text = text

    def get_last_realtime_text(self) -> str:
        """获取最终的实时识别文本"""
        return self.realtime_text

    def _toggle(self):
        """切换录音状态(开始/停止)"""
        if getattr(self, "_recording", False):
            self._recording = False
            self.stop_cb()
        else:
            self._recording = True
            self.start_cb()

    @staticmethod
    def print_asr(text: str):
        """打印语音识别结果"""
        console.print(f"[ASR] {text}", style="dim")

    @staticmethod
    def print_assistant(text: str):
        """打印大模型回复(流式输出)"""
        console.print(text, end="")

    @staticmethod
    def ask_edit(default: str) -> str:
        """
        询问用户是否修改识别结果
        param default:识别结果
        return: 用户确认或修改后的文本
        """
        try:
            edited = prompt("如需修改识别内容，请直接编辑后回车：", default=default).strip()
            return edited or default
        except KeyboardInterrupt:
            return default