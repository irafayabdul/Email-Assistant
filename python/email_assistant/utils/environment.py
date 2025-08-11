from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Environment:
    """Handles loading and validation of environment variables
    for the Email Assistant."""

    @staticmethod
    def load_env_variable(
        name: str, fallback: Optional[str] | Optional[int] = None
    ) -> Optional[str] | Optional[int]:
        return os.getenv(name, fallback)

    # --- API Keys ---
    @staticmethod
    def get_notion_api_key() -> Optional[str] | Optional[int]:
        return Environment.load_env_variable("NOTION_API_KEY")

    @staticmethod
    def get_notion_db_id() -> Optional[str] | Optional[int]:
        return Environment.load_env_variable("NOTION_DATABASE_ID")

    @staticmethod
    def get_gmail_label() -> Optional[str] | Optional[int]:
        return Environment.load_env_variable("GMAIL_LABEL_TO_POLL", "Zapped")

    @staticmethod
    def get_gmail_polling_interval() -> Optional[str] | Optional[int]:
        return Environment.load_env_variable("POLLING_INTERVAL_SECONDS", 300)
