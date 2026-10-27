"""Application use case: handle a normalized message and return a reply."""
import logging

from app.models import IncomingMessage

LOG = logging.getLogger("qq_bot")


class MessageHandler:
    def __init__(self, llm_provider, history_store, prompt_builder,
                 trigger_detector, trigger_context, profile_store,
                 access_policy, limiter):
        self.llm_provider = llm_provider
        self.history_store = history_store
        self.prompt_builder = prompt_builder
        self.trigger_detector = trigger_detector
        self.trigger_context = trigger_context
        self.profile_store = profile_store
        self.access_policy = access_policy
        self.limiter = limiter

    async def handle(self, message: IncomingMessage) -> str | None:
        namespaced_user = f"{message.platform}:{message.user_id}"
        # Keep whitelist values backward-compatible with raw platform user IDs;
        # namespace only the internal limiter and profile keys.
        if not self.access_policy(message.user_id) or not self.limiter(namespaced_user):
            return None

        triggered = self.trigger_detector(message.text)
        extra = self.trigger_context(message.timestamp.hour, triggered)
        history = self.history_store.get_history(message.session_id, limit_turns=8)
        history.append({"role": "user", "content": message.text})
        try:
            reply = await self.llm_provider(self.prompt_builder(extra_context=extra), history)
        except Exception:
            LOG.exception("LLM request failed")
            reply = "诶？我脑子突然卡了一下，等我缓缓再回你。"

        self.history_store.save_turn(message.session_id, message.text, reply)
        self.profile_store.update_profile(namespaced_user, nickname=message.nickname)
        return reply
