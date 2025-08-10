import requests, json, logging
from config import OLLAMA_URL, LLM_MODEL, MAX_HISTORY, SYSTEM_PROMPT   

_logger = logging.getLogger(__name__)

class DeepSeekClient:
    def __init__(self):
        self.history = [SYSTEM_PROMPT]

    def chat(self, user_text: str):
        self.history.append({"role": "user", "content": user_text})
        if len(self.history) > MAX_HISTORY * 2 + 1:
            self.history = [SYSTEM_PROMPT] + self.history[-MAX_HISTORY * 2:]
        payload = {"model": LLM_MODEL, "messages": self.history, "stream": True}
        try:
            resp = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True)
            resp.raise_for_status()
            full = ""
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                    full += content
                if chunk.get("done"):
                    break
            self.history.append({"role": "assistant", "content": full})
        except Exception as e:
            _logger.error("LLM error: %s", e)
            yield "抱歉，大模型调用失败"