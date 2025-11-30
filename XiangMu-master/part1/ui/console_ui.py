# part1/ui/console_ui.py
from rich.console import Console
import keyboard

console = Console()

class ConsoleUI:
    """控制台用户界面，处理用户交互与输出展示"""
    def __init__(self, start_cb, stop_cb):
        self.start_cb = start_cb  
        self.stop_cb = stop_cb 
        self.realtime_text = "" 
        self.last_segment = "" 

        # 绑定空格热键
        keyboard.add_hotkey("space", self._toggle)

        # 录音状态标志
        self._recording = False

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
        if self._recording:
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
        询问用户是否修改识别结果（使用 input，避免 keyboard 与 prompt 冲突）
        """
        console.print(f"[yellow]识别内容：{default}[/yellow]")

        try:
            edited = input("如需修改内容，请输入新内容；直接回车表示保持原样：").strip()
            return edited or default
        except KeyboardInterrupt:
            return default

    @staticmethod
    def ask_confirm_ai() -> bool:
        """
        询问用户是否需要调用 AI（使用 input，不使用 prompt）
        """
        try:
            confirm = input("是否询问 AI？(y/n，默认 y)：").strip().lower()
            return confirm in ["y", ""]
        except KeyboardInterrupt:
            return False
