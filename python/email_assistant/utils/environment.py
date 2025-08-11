from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Environment:
    """Handles loading and validation of environment variables
    for the Email Assistant."""

    @staticmethod
    def load_env_variable(name: str, fallback: Optional[str] = None) -> Optional[str]:
        return os.getenv(name, fallback)

    # --- Variables ---
