from pathlib import Path

# ---------- 音频 ----------
CHUNK = 480
RATE = 16_000
CHANNELS = 1
FORMAT = "Int16"
MAX_RECORD_SEC = 600
RING_SEC = 15
REALTIME_PROCESS_INTERVAL = 0.5  

# ---------- 模型 ----------
WHISPER_MODEL = "small"  
OLLAMA_URL = "http://localhost:11434"
LLM_MODEL = "deepseek-r1:1.5b"
MAX_HISTORY = 10
SYSTEM_PROMPT = {"role": "system",
                 "content": "你是一个办公助手，帮助用户处理 1.文件的新增、删除、移动、查找。2.中英句子互译 等办公软件问题。"}

# ---------- 路径 ----------
PROJECT_ROOT = Path(__file__).parent.resolve()