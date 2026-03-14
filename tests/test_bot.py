"""Tests for bot startup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestMain:
    """Tests for :func:`bot.main`."""

    @pytest.mark.asyncio
    async def test_delete_webhook_called_before_polling(self):
        """Ensure delete_webhook is called before start_polling to avoid
        TelegramConflictError when a webhook is still active."""
        call_order: list[str] = []

        mock_bot = AsyncMock()
        mock_bot.delete_webhook = AsyncMock(
            side_effect=lambda **kw: call_order.append("delete_webhook"),
        )

        mock_dp = AsyncMock()
        mock_dp.start_polling = AsyncMock(
            side_effect=lambda *a, **kw: call_order.append("start_polling"),
        )

        with (
            patch("bot.Bot", return_value=mock_bot),
            patch("bot.dp", mock_dp),
            patch("bot.BOT_TOKEN", "fake-token"),
        ):
            from bot import main

            await main()

        mock_bot.delete_webhook.assert_called_once()
        mock_dp.start_polling.assert_called_once_with(mock_bot)
        assert call_order == ["delete_webhook", "start_polling"]
