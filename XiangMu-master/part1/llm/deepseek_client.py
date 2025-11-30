import requests
import json
import logging
from config import OLLAMA_URL, LLM_MODEL, MAX_HISTORY, SYSTEM_PROMPT  

_logger = logging.getLogger(__name__)

class DeepSeekClient:
    """大模型客户端，用于与OLLAMA服务交互实现对话功能"""
    def __init__(self):
        self.history = [SYSTEM_PROMPT]

    def chat(self, user_text: str):
        """
        与大模型进行对话
        param user_text: 用户输入文本
        return: 生成的回复内容(流式返回)
        """
        self.history.append({"role": "user", "content": user_text})
        
        if len(self.history) > MAX_HISTORY * 2 + 1:
            self.history = [SYSTEM_PROMPT] + self.history[-MAX_HISTORY * 2:]
        
        payload = {
            "model": LLM_MODEL, 
            "messages": self.history,  
            "stream": True  #
        }
        
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
                stream=True  
            )
            resp.raise_for_status()  
            
            full_response = ""  
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content  
                    full_response += content
                if chunk.get("done"):  
                    break
            
            self.history.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            _logger.error("大模型调用失败: %s", e)
            yield "抱歉，大模型调用失败"