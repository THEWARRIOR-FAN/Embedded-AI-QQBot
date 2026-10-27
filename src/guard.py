"""
QQ 群聊机器人 - 限速、白名单/黑名单。
防止开发期被人刷屏，也避免 token 被烧光。
"""
import time
from collections import defaultdict

# 每用户最近一次发言时间
_last_msg: dict[str, float] = {}

# 每用户每分钟发言计数
_msg_count: dict[str, list[float]] = defaultdict(list)

# 默认不限制；想开就填 QQ 号进去
WHITELIST: set[str] = set()  # 比如 {"QQ_123456"} - 只有这些人能触发
BLACKLIST: set[str] = set()


def is_allowed(user_id: str) -> bool:
    """白名单模式：开了白名单就只允许白名单里的人。"""
    if user_id in BLACKLIST:
        return False
    if WHITELIST and user_id not in WHITELIST:
        return False
    return True


def rate_limit(user_id: str, per_minute: int = 8, per_second: int = 1) -> bool:
    """返回 True 表示通过，False 表示被限流。"""
    now = time.time()

    # 1 秒内不能连发
    if user_id in _last_msg and now - _last_msg[user_id] < per_second:
        return False

    # 1 分钟内最多 N 条
    _msg_count[user_id] = [t for t in _msg_count[user_id] if now - t < 60]
    if len(_msg_count[user_id]) >= per_minute:
        return False

    _msg_count[user_id].append(now)
    _last_msg[user_id] = now
    return True
