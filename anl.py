"""Async helpers for downloading books from the ANL digital library."""

from __future__ import annotations

import asyncio
import io
import re
from urllib.parse import parse_qs, urlparse

import aiohttp
from PIL import Image

from config import (
    ANL_IMG_URL,
    ANL_PAGE_URL,
    MIN_IMAGE_SIZE,
    REQUEST_DELAY,
    REQUEST_HEADERS,
)


def parse_anl_url(url: str) -> str | None:
    """Extract the *bibid* value from an ANL page URL.

    Accepts URLs like:
        http://web2.anl.az:81/read/page.php?bibid=vtls000415938
        http://web2.anl.az:81/read/page.php?bibid=415938&pno=3

    Returns the numeric bibid (leading zeros stripped) or ``None``
    if the URL does not match the expected pattern.
    """
    parsed = urlparse(url)

    if "anl.az" not in parsed.hostname:
        return None

    if "/read/page.php" not in parsed.path:
        return None

    qs = parse_qs(parsed.query)
    raw_bibid = qs.get("bibid", [None])[0]
    if raw_bibid is None:
        return None

    digits = re.sub(r"\D", "", raw_bibid)
    if not digits:
        return None

    return digits.lstrip("0") or "0"


async def get_total_pages(
    session: aiohttp.ClientSession,
    bibid: str,
) -> int:
    """Return the total number of pages for the given *bibid*."""
    url = f"{ANL_PAGE_URL}?bibid={bibid}&pno=1"
    async with session.get(url) as resp:
        resp.raise_for_status()
        text = await resp.text()

    match = re.search(r'last_page_params="\?bibid=\d+&pno=(\d+)"', text)
    if not match:
        raise ValueError("Səhifə sayını almaq mümkün olmadı.")
    return int(match.group(1))


async def get_book_title(
    session: aiohttp.ClientSession,
    bibid: str,
) -> str:
    """Try to extract the book title from the first page."""
    url = f"{ANL_PAGE_URL}?bibid={bibid}&pno=1"
    async with session.get(url) as resp:
        resp.raise_for_status()
        text = await resp.text()

    match = re.search(
        r'<h2 class="book-title[^"]*">(.*?)</h2>',
        text,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    return f"book_{bibid}"


async def download_page_image(
    session: aiohttp.ClientSession,
    bibid: str,
    page_no: int,
) -> bytes | None:
    """Download a single page image and return its bytes.

    Returns ``None`` when the server responds with invalid / too-small data.
    """
    # Pre-load the viewer page (sets server-side session state)
    preload_url = f"{ANL_PAGE_URL}?bibid={bibid}&pno={page_no}"
    async with session.get(preload_url) as resp:
        resp.raise_for_status()

    await asyncio.sleep(REQUEST_DELAY)

    # Fetch the actual image
    img_url = f"{ANL_IMG_URL}?bibid={bibid}&pno={page_no}"
    async with session.get(img_url) as resp:
        resp.raise_for_status()
        data = await resp.read()

    if len(data) < MIN_IMAGE_SIZE:
        return None

    return data


async def download_book(
    bibid: str,
    progress_callback=None,
) -> tuple[str, bytes]:
    """Download all pages of a book and return ``(title, pdf_bytes)``.

    *progress_callback*, when provided, is called as
    ``await progress_callback(current_page, total_pages)``
    after each page is downloaded.
    """
    async with aiohttp.ClientSession(headers=REQUEST_HEADERS) as session:
        total_pages = await get_total_pages(session, bibid)
        title = await get_book_title(session, bibid)

        images: list[Image.Image] = []

        for page_no in range(1, total_pages + 1):
            data = await download_page_image(session, bibid, page_no)
            if data is not None:
                img = Image.open(io.BytesIO(data))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                images.append(img)

            if progress_callback is not None:
                await progress_callback(page_no, total_pages)

        if not images:
            raise ValueError("Heç bir şəkil yüklənə bilmədi.")

        pdf_buffer = io.BytesIO()
        images[0].save(
            pdf_buffer,
            format="PDF",
            save_all=True,
            append_images=images[1:],
        )
        pdf_bytes = pdf_buffer.getvalue()

    return title, pdf_bytes
