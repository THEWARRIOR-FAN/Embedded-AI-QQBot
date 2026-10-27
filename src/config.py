"""Runtime configuration shared by all platform adapters."""
from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_appid: str
    bot_secret: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    data_dir: Path

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        missing = [key for key in ("BOT_APPID", "BOT_SECRET", "LLM_API_KEY") if not os.environ.get(key)]
        if missing:
            raise ValueError(f"缺少环境变量: {', '.join(missing)}")
        data_dir = Path(os.environ.get("DATA_DIR", "./data")).expanduser().resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            bot_appid=os.environ["BOT_APPID"],
            bot_secret=os.environ["BOT_SECRET"],
            llm_api_key=os.environ["LLM_API_KEY"],
            llm_base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            llm_model=os.environ.get("LLM_MODEL", "deepseek-chat"),
            data_dir=data_dir,
        )
