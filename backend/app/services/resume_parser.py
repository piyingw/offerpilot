"""简历解析：PDF / DOCX 文本抽取 + LLM 结构化（失败时降级为纯文本）。"""

import json

import pymupdf as fitz  # PyMuPDF 新版推荐导入名
from docx import Document as DocxDocument
from langchain_core.messages import HumanMessage
from loguru import logger

from app.services.llm import get_chat_model

MAX_RESUME_CHARS = 6000

STRUCTURE_PROMPT = """你是简历解析器。请把下面的简历文本整理为严格的 JSON。
除 JSON 外不要输出任何内容。
结构如下（缺失的字段用空数组或空字符串，不要编造简历中没有的信息）：
{
  "basic_info": {"name": "", "email": "", "phone": ""},
  "education": [{"school": "", "major": "", "degree": "", "start": "", "end": ""}],
  "experiences": [{"company": "", "role": "", "start": "", "end": "", "highlights": [""]}],
  "projects": [{"name": "", "role": "", "tech_stack": [""], "highlights": [""]}],
  "skills": [""]
}

简历文本：
"""


def extract_text(file_path: str, suffix: str) -> str:
    if suffix == ".pdf":
        with fitz.open(file_path) as doc:
            return "\n".join(page.get_text() for page in doc)
    if suffix == ".docx":
        document = DocxDocument(file_path)
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())
    raise ValueError(f"不支持的文件类型: {suffix}")


def _loads_json(text: str) -> dict | None:
    """从模型输出中提取 JSON 对象，容忍 markdown 代码块包裹。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned[:4].lower() == "json":
            cleaned = cleaned[4:]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _content_str(message_content: object) -> str:
    if isinstance(message_content, str):
        return message_content
    if isinstance(message_content, list):
        return "".join(
            part.get("text", "") for part in message_content if isinstance(part, dict)
        )
    return str(message_content)


def structure_resume(text: str) -> dict:
    """调用 LLM 把简历文本转为结构化 JSON；解析失败时抛出异常，由调用方降级。"""
    model = get_chat_model(temperature=0)
    messages = [HumanMessage(content=STRUCTURE_PROMPT + text[:MAX_RESUME_CHARS])]
    for attempt in range(2):
        resp = model.invoke(messages)
        data = _loads_json(_content_str(resp.content))
        if data is not None:
            return data
        messages.append(resp)
        messages.append(
            HumanMessage(content="上面的输出不是合法 JSON。请重新输出，只输出 JSON 本身。")
        )
        logger.warning(f"简历结构化第 {attempt + 1} 次输出无法解析，已重试")
    raise ValueError("简历结构化失败：LLM 输出无法解析为 JSON")
