"""Tests for configuration module."""

from __future__ import annotations

import importlib
import os
from unittest.mock import patch


class TestBotTokenConfig:
    """Tests for BOT_TOKEN configuration."""

    def test_bot_token_defaults_to_empty_when_unset(self):
        env = os.environ.copy()
        env.pop("BOT_TOKEN", None)
        with patch.dict(os.environ, env, clear=True):
            import config

            importlib.reload(config)
            assert config.BOT_TOKEN == ""

    def test_bot_token_reads_from_env(self):
        with patch.dict(os.environ, {"BOT_TOKEN": "test-token-123"}):
            import config

            importlib.reload(config)
            assert config.BOT_TOKEN == "test-token-123"
