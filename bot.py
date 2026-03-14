"""Telegram bot for downloading books from the ANL digital library as PDF."""

from __future__ import annotations

import asyncio
import logging
import re

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

from anl import download_book, parse_anl_url
from config import BOT_TOKEN, TELEGRAM_MAX_FILE_SIZE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

dp = Dispatcher()

# Regex to find ANL URLs in a message
ANL_URL_RE = re.compile(
    r"https?://[^\s]*anl\.az[^\s]*/read/page\.php\?[^\s]+",
)


@dp.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    await message.answer(
        "Salam! Mənə ANL kitabxanasının linkini göndərin, "
        "mən kitabı PDF formatında sizə göndərəcəyəm.\n\n"
        "Nümunə:\n"
        "<code>http://web2.anl.az:81/read/page.php?bibid=vtls000415938</code>",
    )


@dp.message()
async def handle_message(message: types.Message) -> None:
    if message.text is None:
        return

    urls = ANL_URL_RE.findall(message.text)
    if not urls:
        await message.answer(
            "Zəhmət olmasa düzgün ANL linki göndərin.\n"
            "Nümunə:\n"
            "<code>http://web2.anl.az:81/read/page.php?bibid=vtls000415938</code>",
        )
        return

    for url in urls:
        bibid = parse_anl_url(url)
        if bibid is None:
            await message.answer(f"Bu linkdən kitab ID-si tapılmadı: {url}")
            continue

        status_msg = await message.answer(
            f"⏳ Kitab yüklənir (ID: {bibid})...",
        )

        try:

            async def _progress(current: int, total: int) -> None:
                # Update progress every 5 pages to avoid rate-limits
                if current % 5 == 0 or current == total:
                    await status_msg.edit_text(
                        f"⏳ Yüklənir: {current}/{total} səhifə…",
                    )

            title, pdf_bytes = await download_book(
                bibid,
                progress_callback=_progress,
            )

            if len(pdf_bytes) > TELEGRAM_MAX_FILE_SIZE:
                await status_msg.edit_text(
                    "⚠️ PDF faylı çox böyükdür (>50 MB). "
                    "Telegram vasitəsilə göndərmək mümkün deyil.",
                )
                continue

            safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
            filename = f"{safe_title}.pdf"

            from aiogram.types import BufferedInputFile

            doc = BufferedInputFile(pdf_bytes, filename=filename)
            await message.answer_document(doc, caption=f"📖 {title}")
            await status_msg.delete()

        except Exception:
            logger.exception("Kitab yüklənərkən xəta baş verdi (bibid=%s)", bibid)
            await status_msg.edit_text(
                "❌ Kitab yüklənərkən xəta baş verdi. "
                "Zəhmət olmasa linki yoxlayın və yenidən cəhd edin.",
            )


async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    logger.info("Bot başladılır…")
    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
