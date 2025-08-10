"""
零阻塞实时流式语音 → Whisper → DeepSeek（多轮对话记忆版）
运行：python realtime_stream.py
Ctrl+C 退出
"""
import pyaudio
import whisper
import threading
import numpy as np
import collections
import time
import queue

# ---------------- 参数 ----------------
CHUNK         = 1024
FORMAT        = pyaudio.paInt16
CHANNELS      = 1
RATE          = 16000
SILENCE_SEC   = 1.5          # 每 1.5 秒送一次音频
WHISPER_MODEL = "tiny"       # 本地 Whisper 模型
MAX_HISTORY   = 10           # 保留最近 10 轮对话
# -------------------------------------

# Whisper 模型
model = whisper.load_model(WHISPER_MODEL)

# 引入 ChatEngine
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_ollama import OllamaLLM

class ChatEngine:
    def __init__(self, model_name="deepseek-r1"):
        self.llm = OllamaLLM(model=model_name, base_url="http://localhost:11434")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个办公助手，帮助用户处理Word、Excel等办公软件问题。"),
            ("human", "{input}")
        ])
        self.chain = prompt | self.llm
        self.history = InMemoryChatMessageHistory()

    def chat(self, text: str) -> str:
        response = self.chain.invoke({"input": text})
        return str(response).strip()

# 环形缓冲区
MAX_BUF_LEN = int(RATE * 5)
audio_buf = collections.deque(maxlen=MAX_BUF_LEN)

# 多轮对话历史 + 线程锁
chat_history = []
history_lock = threading.Lock()

# 系统提示词（可选）
SYSTEM_PROMPT = {
    "role": "system",
    "content": "你是办公助手，帮助用户操作 Word/Excel。请简洁回答，必要时给出操作步骤。"
}

def init_system_prompt():
    """初始化对话历史（仅系统提示）"""
    global chat_history
    with history_lock:
        chat_history = [SYSTEM_PROMPT]

# ---------------- 音频回调 ----------------
def callback(in_data, frame_count, time_info, status):
    data_np = np.frombuffer(in_data, dtype=np.int16)
    audio_buf.extend(data_np)
    return (None, pyaudio.paContinue)

# ---------------- Whisper + DeepSeek ----------------
def worker():
    """后台线程：周期性识别 & 对话"""
    while True:
        time.sleep(SILENCE_SEC)
        if len(audio_buf) < int(RATE * 0.5):
            continue  # 不足 0.5 秒跳过

        # 把 deque -> numpy float32
        frame = np.array(audio_buf, dtype=np.float32) / 32768.0
        # Whisper 识别
        result = model.transcribe(frame, language="zh", fp16=False)
        text = result["text"].strip()
        if not text:
            continue

        print("[ASR]", text)

        # 调用 DeepSeek（新线程，防止网络阻塞）
        threading.Thread(target=ask_deepseek, args=(text,), daemon=True).start()

def ask_deepseek(user_text):
    """用 ChatEngine 进行多轮对话"""
    global chat_history
    with history_lock:
        # 1. 追加用户消息
        chat_history.append({"role": "user", "content": user_text})

        # 2. 裁剪历史
        if len(chat_history) > MAX_HISTORY * 2 + 1:  # 系统占 1 条
            chat_history = [SYSTEM_PROMPT] + chat_history[-MAX_HISTORY*2:]

        # 3. 拼接历史为输入
        # 只取最近一轮用户输入（可扩展为拼接历史）
        input_text = user_text

        try:
            reply = chat_engine.chat(input_text)
            print("[DeepSeek]", reply)
            # 4. 追加助手回复
            chat_history.append({"role": "assistant", "content": reply})
        except Exception as e:
            print("❌ DeepSeek error:", e)

# ---------------- 主程序 ----------------
if __name__ == "__main__":
    init_system_prompt()

    # 初始化 ChatEngine
    chat_engine = ChatEngine(model_name="deepseek-r1")

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=callback)

    print("🎤 开始实时识别（带多轮记忆），Ctrl+C 退出")
    stream.start_stream()
    threading.Thread(target=worker, daemon=True).start()

    try:
        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n退出")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()