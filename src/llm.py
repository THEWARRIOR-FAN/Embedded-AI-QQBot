"""
QQ 群聊机器人 - 调用 LLM
默认用 DeepSeek（便宜、中文好、OpenAI 兼容）。可换成任何 OpenAI 协议模型。
"""
import os
from openai import OpenAI

_client: OpenAI | None = None
_model = "deepseek-chat"


def configure(api_key: str, base_url: str, model: str) -> None:
    global _client, _model
    _client = OpenAI(api_key=api_key, base_url=base_url)
    _model = model


def get_client() -> OpenAI:
    global _client, _model
    if _client is None:
        _model = os.environ.get("LLM_MODEL", _model)
        _client = OpenAI(
            api_key=os.environ["LLM_API_KEY"],
            base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        )
    return _client


def chat(system_prompt: str, history: list[dict]) -> str:
    """
    单轮同步调用。history = [{"role": "user"|"assistant", "content": "..."}]
    返回模型回复文本。
    """
    client = get_client()
    resp = client.chat.completions.create(
        model=_model,
        messages=[{"role": "system", "content": system_prompt}, *history],
        temperature=0.8,
        max_tokens=400,
        frequency_penalty=0.3,  # 减少重复
        presence_penalty=0.2,
    )
    return resp.choices[0].message.content.strip()


async def achat(system_prompt: str, history: list[dict]) -> str:
    """异步版本，给 botpy 这种事件循环用。同步版本封到线程池里。"""
    import asyncio
    return await asyncio.to_thread(chat, system_prompt, history)
