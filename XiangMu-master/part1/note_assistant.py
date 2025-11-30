import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import datetime
from llm.deepseek_client import DeepSeekClient
from collections import Counter
import re

class NoteAssistant:
    """
    智能笔记助手（已增强）
    - notes 存在 notes.json（同目录）
    - 本地快速摘要（笔记少时优先）
    - 大模型摘要（笔记多时，使用 DeepSeekClient）
    - 新增：列出全部笔记功能
    """

    def __init__(self, note_file="notes.json"):
        self.note_file = note_file
        self.ai = DeepSeekClient()

        if not os.path.exists(self.note_file):
            with open(self.note_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    # ----------------- 基础 I/O -----------------
    def _load_notes(self):
        with open(self.note_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []

    def _save_notes(self, notes):
        with open(self.note_file, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=4)

    # ----------------- 操作方法 -----------------
    def add_note(self, text):
        notes = self._load_notes()
        entry = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": text
        }
        notes.append(entry)
        self._save_notes(notes)
        return "已记录。"

    def list_notes(self, limit: int = None):
        """列出全部笔记（按时间升序），limit=None 列出全部"""
        notes = self._load_notes()
        if not notes:
            return "目前没有任何笔记。"
        lines = []
        for n in notes if limit is None else notes[-limit:]:
            lines.append(f"{n['time']} - {n['text']}")
        return "\n".join(lines)

    def search_notes(self, keyword):
        notes = self._load_notes()
        results = [n for n in notes if keyword in n["text"]]
        if not results:
            return "没有找到相关内容。"
        return "\n".join([f"{n['time']} - {n['text']}" for n in results])

    def delete_last(self):
        notes = self._load_notes()
        if not notes:
            return "没有可删除的笔记。"
        removed = notes.pop()
        self._save_notes(notes)
        return f"已删除：{removed['text']}"

    # ----------------- 本地快速摘要（当笔记较少时优先使用） -----------------
    def _local_summarize(self, notes):
        """
        简单而确定性的本地摘要逻辑：
        - 列出最近 5 条要点（倒序）
        - 提取高频关键词作为“关键词”
        - 给出一句简短总体概述
        """
        if not notes:
            return "目前没有任何笔记。"

        # 最近要点（最多 5 条）
        recent = notes[-5:]
        points = [f"- {n['text']}" for n in recent]

        # 汇总一句话：取前 6 个词频最高的词（排除停用词）
        all_text = " ".join([n["text"] for n in notes])
        words = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", all_text)
        stopwords = set(["的", "了", "在", "和", "是", "我", "你", "有", "吗", "就", "要", "与", "及"])
        filtered = [w for w in words if w not in stopwords and len(w) > 1]
        freq = Counter(filtered)
        keywords = ", ".join([w for w, _ in freq.most_common(6)])

        overview = f"共 {len(notes)} 条笔记，关键词：{keywords}" if keywords else f"共 {len(notes)} 条笔记。"

        result = "最近要点：\n" + "\n".join(points) + "\n\n" + overview
        return result

    # ----------------- AI 摘要（当笔记较多时更合适） -----------------
    def _ai_summarize(self, notes):
        content = "\n".join([f"[{n['time']}] {n['text']}" for n in notes])
        prompt = (
            "你是一个简洁的笔记总结助手。请根据下面的笔记内容，"
            "用中文分别列出：\n\n"
            "1) 主要事项（最多 6 条精炼要点，每条尽量短）\n"
            "2) 需要跟进的计划/待办（若无可写“无”）\n"
            "3) 风险/注意点（若无可写“无”）\n\n"
            "仅输出这三部分，标题使用“主要事项：”、“待办：”、“风险：”，不要输出多余解释。\n\n"
            f"笔记内容如下：\n{content}\n"
        )

        answer = ""
        for chunk in self.ai.chat(prompt):
            answer += chunk
        return answer.strip()

    # ----------------- 对外 summarize 接口 -----------------
    def summarize(self):
        notes = self._load_notes()
        if not notes:
            return "目前没有任何笔记。"

        # 当笔记较少时（<=5），使用本地摘要，稳定且直观
        if len(notes) <= 5:
            return self._local_summarize(notes)

        # 笔记较多时调用大模型，但增加明确提示（以减少模板化输出）
        try:
            return self._ai_summarize(notes)
        except Exception as e:
            # 出错时回退到本地摘要
            return "自动摘要失败（使用本地回退）。\n\n" + self._local_summarize(notes)

    # ----------------- 主入口：自然语言解析 -----------------
    def process(self, user_input: str):
        text = user_input.strip()

        # —— 列出全部笔记 ——
        if any(k in text for k in ["列出", "显示全部", "显示 笔记", "列出全部"]):
            return self.list_notes()

        # —— 添加笔记 ——
        if any(w in text for w in ["记录", "记一下", "添加笔记", "写一条"]):
            # 尝试使用 "：" 后面的内容作为笔记正文，否则用整句
            if "：" in text or ":" in text:
                real_text = text.split("：")[-1].split(":")[-1].strip()
            else:
                # 去掉关键词
                real_text = re.sub(r"(记录|记一下|添加笔记|写一条)", "", text).strip()
                if not real_text:
                    real_text = text
            return self.add_note(real_text)

        # —— 搜索笔记 ——
        if "找" in text or "搜索" in text:
            # 提取关键词（简化）
            keyword = re.sub(r"(找|搜索)", "", text).strip()
            if not keyword:
                return "请告诉我想找的关键词。"
            return self.search_notes(keyword)

        # —— 总结笔记 ——
        if "总结" in text:
            return self.summarize()

        # —— 删除笔记 ——
        if "删除" in text or "去掉" in text:
            return self.delete_last()

        # —— 其余
        return "我听不懂你的意思。你可以说：记录、搜索、列出、总结、删除。"





