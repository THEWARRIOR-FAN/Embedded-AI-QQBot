"""
命令行试聊 —— 不用 QQ、不用 NapCat，先验证模型连接和人设配置。

用法：
    pip install openai python-dotenv
    把 .env.example 复制成 .env，填入 LLM_API_KEY
    python cli_chat.py

输入 退出 / quit / exit 结束。
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

from prompts import build_system_prompt, detect_trigger_intent, trigger_to_context, load_persona

load_dotenv()

MAX_HISTORY = 10  # 保留最近多少条消息


def main():
    if not os.environ.get("LLM_API_KEY"):
        print("还没配置 LLM_API_KEY。")
        print("请把 .env.example 复制成 .env，填入你的 DeepSeek Key。")
        return

    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
    )
    model = os.environ.get("LLM_MODEL", "deepseek-chat")

    history = []
    name = load_persona()["name"]
    print("=" * 50)
    print(f"{name}已上线  (输入 退出 / quit 结束)")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{name}：那我先下了，下次再聊 :)")
            break

        if not user_input:
            continue
        if user_input.lower() in ("退出", "quit", "exit", "q"):
            print(f"{name}：那我先下了，下次再聊 :)")
            break

        # 触发器：深夜 / 表白 / 敏感词
        triggered = detect_trigger_intent(user_input)
        extra = trigger_to_context(datetime.now().hour, triggered)
        system_prompt = build_system_prompt(extra_context=extra)

        if triggered:
            print(f"   [触发：{', '.join(triggered)}]")

        history.append({"role": "user", "content": user_input})

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}, *history],
                temperature=0.8,
                max_tokens=400,
            )
            reply = resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"\n[调用失败] {e}")
            history.pop()
            continue

        history.append({"role": "assistant", "content": reply})
        history = history[-MAX_HISTORY:]

        print(f"{name}：{reply}")


if __name__ == "__main__":
    main()
