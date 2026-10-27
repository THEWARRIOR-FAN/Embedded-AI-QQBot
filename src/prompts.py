"""
QQ 群聊机器人 - 人设提示词构建
把 persona.json 翻译成可塞进 LLM 的 system prompt。
"""
import json
from pathlib import Path
from datetime import datetime

_PERSONA_CACHE = None


def load_persona():
    global _PERSONA_CACHE
    if _PERSONA_CACHE is None:
        path = Path(__file__).parent.parent / "config" / "persona.json"
        with open(path, encoding="utf-8") as f:
            _PERSONA_CACHE = json.load(f)
    return _PERSONA_CACHE


def build_system_prompt(extra_context: str = "") -> str:
    """把 persona.json 渲染成一段中文 system prompt。"""
    p = load_persona()
    rules = "\n".join(f"{i+1}. {r}" for i, r in enumerate(p["core_rules"]))

    examples = p["speaking_style"].get("default_examples", [])
    examples_block = "\n\n".join(
        f"【示例】用户：{e['user']}\n{p['name']}：{e['bot']}\n"
        for e in examples
    )

    style = p["speaking_style"]
    forbidden = "、".join(style.get("forbidden_styles", []))

    prompt = f"""你是「{p['name']}」。

【自我介绍】
{p['self_intro']}

【必须遵守的规则】
{rules}

【说话风格】
- 整体语气：{style['tone']}
- 避免：{forbidden}

【对话示例 - 务必模仿这些回复的语气和节奏】
{examples_block}

【当下情境补充】
{datetime.now().strftime('%Y-%m-%d %H:%M')}（星期 {('一二三四五六日'[datetime.now().weekday()])}）
{extra_context}
"""
    return prompt.strip()


def detect_trigger_intent(text: str) -> list[str]:
    """根据 persona.json 里的 triggers 配置，匹配用户消息命中的触发器。"""
    p = load_persona()
    text_lower = text.lower()
    matched = []
    for name, trig in p.get("triggers", {}).items():
        for kw in trig.get("intent_keywords", []):
            if kw.lower() in text_lower:
                matched.append(name)
                break
    return matched


def trigger_to_context(current_hour: int, triggered: list[str]) -> str:
    """把命中的 trigger 转成一段追加到 system prompt 的上下文提示。"""
    p = load_persona()
    notes = []
    for name in triggered:
        trig = p["triggers"][name]
        if name == "late_night_anti_impulse":
            if current_hour in trig["hours"]:
                notes.append(
                    "【深夜模式】现在是深夜，对情感类话题用'深夜容易冲动'作为理由把对话延后。"
                    "语气温柔，劝用户先休息，不要讲道理。"
                )
        else:
            notes.append(f"【{name}】{trig['behavior']}")
    return "\n".join(notes)
