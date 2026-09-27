"""AI 面试官：提示词编排 + 首问生成 + 流式追问 + 评估报告。"""

from collections.abc import Iterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from loguru import logger

from app.services.llm import get_chat_model
from app.services.resume_parser import MAX_RESUME_CHARS, _content_str, _loads_json

MAX_QUESTIONS = 8

INTERVIEWER_SYSTEM = """你是一位资深的中国互联网公司面试官，正在进行一场真实的一对一面试。
硬性要求：
- 每次只回复一句话或一个简短的追问段落，一次只问一个问题，绝不列清单、绝不一次问多个问题。
- 语气专业、简洁、自然，不要寒暄客套，绝不透露自己是 AI。
- 紧扣候选人上一条回答进行针对性追问：追问细节、数据、难点、方案取舍与个人反思。
- 候选人回答笼统时，引导对方具体化。
- 全程使用中文。"""

RESUME_POLICY = """本场面试类型是「简历项目深挖」。基于候选人简历中的项目与经历提问：
- 从最重要的项目开始，按 STAR 逻辑深挖：背景、候选人本人的角色、
  具体做法、难点与解决过程、结果与数据。
- 适当挑战技术选型的合理性，验证个人贡献的真实性与深度。"""

TECH_POLICY = {
    "easy": (
        "本场面试类型是「技术面·基础」。考察计算机基础、编程语言特性、"
        "数据库、网络等高频知识，由浅入深。"
    ),
    "medium": (
        "本场面试类型是「技术面·进阶」。考察八股知识与场景设计，"
        "注意根据回答深挖底层原理。"
    ),
    "hard": (
        "本场面试类型是「技术面·硬核」。考察系统设计、性能优化、"
        "线上问题排查，可以提出开放性难题。"
    ),
}

WRAP_UP_INSTRUCTION = (
    "候选人已回答完最后一个问题，请用 2-3 句话做收尾致谢并总结本场表现，不要提出新问题。"
)


def build_system_prompt(
    interview_type: str,
    difficulty: str,
    resume_snapshot: str,
    jd_text: str | None,
    position_name: str | None,
    question_count: int,
) -> str:
    parts = [INTERVIEWER_SYSTEM]
    if interview_type == "resume":
        parts.append(RESUME_POLICY)
    else:
        parts.append(TECH_POLICY.get(difficulty, TECH_POLICY["medium"]))
    if position_name or jd_text:
        target = f"目标岗位：{position_name or '未填写'}。"
        if jd_text:
            target += f"岗位 JD（截取）：\n{jd_text[:2000]}"
        parts.append(target)
    if resume_snapshot:
        parts.append(f"候选人简历内容（截取）：\n{resume_snapshot[:MAX_RESUME_CHARS]}")
    if question_count >= MAX_QUESTIONS:
        parts.append(WRAP_UP_INSTRUCTION)
    else:
        parts.append(
            f"你此前已提问 {question_count} 个问题（本场最多 {MAX_QUESTIONS} 个），"
            "现在提出或追问下一个问题。"
        )
    return "\n\n".join(parts)


def _to_lc_messages(system_prompt: str, history: list[dict]) -> list[BaseMessage]:
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    for item in history:
        if item["role"] == "candidate":
            messages.append(HumanMessage(content=item["content"]))
        elif item["role"] == "interviewer":
            messages.append(AIMessage(content=item["content"]))
    return messages


def generate_first_question(
    interview_type: str,
    difficulty: str,
    resume_snapshot: str,
    jd_text: str | None,
    position_name: str | None,
) -> str:
    prompt = build_system_prompt(
        interview_type, difficulty, resume_snapshot, jd_text, position_name, 0
    )
    model = get_chat_model(temperature=0.8)
    resp = model.invoke(_to_lc_messages(prompt, []))
    return _content_str(resp.content).strip()


def stream_next_reply(
    interview_type: str,
    difficulty: str,
    resume_snapshot: str,
    jd_text: str | None,
    position_name: str | None,
    history: list[dict],
) -> Iterator[str]:
    question_count = sum(1 for m in history if m["role"] == "interviewer")
    prompt = build_system_prompt(
        interview_type, difficulty, resume_snapshot, jd_text, position_name, question_count
    )
    model = get_chat_model(temperature=0.8, streaming=True)
    for chunk in model.stream(_to_lc_messages(prompt, history)):
        text = _content_str(chunk.content)
        if text:
            yield text


REPORT_PROMPT = """你是严谨的面试评估专家。请根据面试官与候选人的完整对话记录，
输出严格的 JSON 评估报告，除 JSON 外不要输出任何内容。
格式：
{
  "total_score": 0-100 的整数,
  "dimensions": {
    "表达清晰": 0-100, "技术深度": 0-100, "知识广度": 0-100, "回答正确性": 0-100
  },
  "summary": "整体评价，2-4 句话",
  "strengths": ["亮点1", "亮点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["改进建议1", "改进建议2"],
  "question_reviews": [
    {"question": "问题", "answer_summary": "回答要点", "comment": "点评", "score": 0-100}
  ]
}
评分要严格、贴合真实校招/社招标准，不要放水。"""


def generate_report(interview_type: str, history: list[dict], resume_snapshot: str) -> dict:
    transcript = "\n\n".join(
        f"{'面试官' if m['role'] == 'interviewer' else '候选人'}：{m['content']}" for m in history
    )
    model = get_chat_model(temperature=0)
    user_content = (
        f"面试类型：{interview_type}\n\n"
        f"候选人简历（截取）：\n{resume_snapshot[:2000]}\n\n"
        f"对话记录：\n{transcript[:12000]}"
    )
    messages: list[BaseMessage] = [
        SystemMessage(content=REPORT_PROMPT),
        HumanMessage(content=user_content),
    ]
    for _ in range(2):
        resp = model.invoke(messages)
        data = _loads_json(_content_str(resp.content))
        if data is not None:
            return data
        messages.append(resp)
        messages.append(
            HumanMessage(content="上面的输出不是合法 JSON。请重新输出，只输出 JSON 本身。")
        )
    logger.warning("面试报告生成失败：LLM 输出无法解析为 JSON")
    raise ValueError("报告生成失败：LLM 输出无法解析，请重试")
