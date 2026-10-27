"""Composition root for the QQ adapter and platform-independent application."""
import logging

import botpy
from botpy.message import GroupMessage, C2CMessage

from adapters.qq import group_message, direct_message
from app.handler import MessageHandler
from config import Settings
from guard import is_allowed, rate_limit
import llm
import memory
from prompts import build_system_prompt, detect_trigger_intent, trigger_to_context

LOG = logging.getLogger("qq_bot")


class QQBot(botpy.Client):
    def __init__(self, handler: MessageHandler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handler = handler

    async def on_ready(self):
        LOG.info("机器人已上线")

    async def on_group_at_message_create(self, message: GroupMessage):
        reply = await self.handler.handle(group_message(message))
        if reply is not None:
            try:
                await message._api.post_group_message(
                    group_openid=message.group_openid, msg_type=0,
                    msg_id=message.id, content=reply)
            except Exception:
                LOG.exception("群消息发送失败")

    async def on_c2c_message_create(self, message: C2CMessage):
        reply = await self.handler.handle(direct_message(message))
        if reply is not None:
            try:
                await message._api.post_c2c_message(
                    openid=getattr(message.author, "user_openid", ""),
                    msg_type=0, msg_id=message.id, content=reply)
            except Exception:
                LOG.exception("私聊消息发送失败")


if __name__ == "__main__":
    try:
        settings = Settings.load()
    except ValueError as exc:
        raise SystemExit(f"{exc}\n请把 .env.example 复制成 .env 并填好。") from exc

    memory.configure(settings.data_dir)
    llm.configure(settings.llm_api_key, settings.llm_base_url, settings.llm_model)
    handler = MessageHandler(
        llm.achat, memory, build_system_prompt, detect_trigger_intent,
        trigger_to_context, memory, is_allowed, rate_limit)

    # C2C callbacks require direct_message plus the platform-side permission.
    intents = botpy.Intents(public_messages=True, direct_message=True)
    bot = QQBot(handler, intents=intents)
    bot.run(appid=settings.bot_appid, secret=settings.bot_secret)
