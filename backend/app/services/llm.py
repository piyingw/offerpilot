"""LLM 接入层：基于 LangChain 的 ChatOpenAI，兼容 GLM / DeepSeek / Qwen 的 OpenAI 兼容端点。"""

from langchain_openai import ChatOpenAI

from app.core.config import settings

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
}


class LLMNotConfiguredError(Exception):
    """LLM API Key 或端点未配置。"""


def resolve_llm_config() -> tuple[str, str, str]:
    """返回 (base_url, model, api_key)。"""
    preset = PROVIDER_PRESETS.get(settings.LLM_PROVIDER, {})
    base_url = settings.LLM_BASE_URL or preset.get("base_url", "")
    model = settings.LLM_MODEL or preset.get("model", "")
    if not base_url or not model:
        raise LLMNotConfiguredError(
            f"未知的 LLM_PROVIDER: {settings.LLM_PROVIDER}，支持: glm / deepseek / qwen"
        )
    if not settings.LLM_API_KEY:
        raise LLMNotConfiguredError(
            "未配置 LLM API Key：请在 backend/.env 中设置 LLM_API_KEY（provider: "
            f"{settings.LLM_PROVIDER}）"
        )
    return base_url, model, settings.LLM_API_KEY


def get_chat_model(*, temperature: float = 0.7, streaming: bool = False) -> ChatOpenAI:
    base_url, model, api_key = resolve_llm_config()
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        streaming=streaming,
        timeout=60,
    )
