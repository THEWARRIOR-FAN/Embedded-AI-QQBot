"""
不连 QQ 的离线自测脚本：
    pip install python-dotenv openai
    设置 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 环境变量后运行
    python smoke_test.py

它会用 `persona.json` 跑一组测试样例，检查当前机器人配置的回复质量。
"""
import os
from datetime import datetime
from dotenv import load_dotenv

from prompts import build_system_prompt, detect_trigger_intent, trigger_to_context
from llm import chat

load_dotenv()

TESTS = [
    ("可以帮我解释一下什么是 API 吗？", "准确、清晰地解释概念"),
    ("帮我把这句话改得简洁一点：由于天气原因，活动将会延后举行。", "简洁改写"),
    ("周末想做点什么？", "提供选项并询问偏好"),
    ("你确定这个答案吗？", "表达把握程度，不夸大确定性"),
    ("帮我列一个整理书桌的三步计划。", "给出清晰、可执行的步骤"),
]


def run():
    if not os.environ.get("LLM_API_KEY"):
        print("⚠️  请先在 .env 里配置 LLM_API_KEY")
        print("   复制 .env.example 为 .env，填入即可。")
        return

    print("=" * 60)
    print("QQ 群聊机器人 · 离线烟雾测试")
    print("=" * 60)

    for text, expect in TESTS:
        triggered = detect_trigger_intent(text)
        extra = trigger_to_context(datetime.now().hour, triggered)
        system = build_system_prompt(extra_context=extra)

        print(f"\n👤 用户：{text}")
        print(f"   （期望：{expect}）")

        try:
            reply = chat(system, [{"role": "user", "content": text}])
        except Exception as e:
            print(f"   ❌ 调用失败：{e}")
            continue

        print(f"🤖 机器人：{reply}")
        print("-" * 60)


if __name__ == "__main__":
    run()
