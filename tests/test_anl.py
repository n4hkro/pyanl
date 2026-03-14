"""Tests for the ANL URL parsing and helper utilities."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from anl import download_book, get_total_pages, parse_anl_url


# ---------------------------------------------------------------------------
# parse_anl_url
# ---------------------------------------------------------------------------

class TestParseAnlUrl:
    """Tests for :func:`anl.parse_anl_url`."""

    def test_standard_vtls_url(self):
        url = "http://web2.anl.az:81/read/page.php?bibid=vtls000415938"
        assert parse_anl_url(url) == "415938"

    def test_numeric_bibid(self):
        url = "http://web2.anl.az:81/read/page.php?bibid=415938&pno=3"
        assert parse_anl_url(url) == "415938"

    def test_bibid_with_leading_zeros(self):
        url = "http://web2.anl.az:81/read/page.php?bibid=000004"
        assert parse_anl_url(url) == "4"

    def test_bibid_zero(self):
        url = "http://web2.anl.az:81/read/page.php?bibid=0"
        assert parse_anl_url(url) == "0"

    def test_vtls_bibid_with_pno(self):
        url = "http://web2.anl.az:81/read/page.php?bibid=vtls000001234&pno=10"
        assert parse_anl_url(url) == "1234"

    def test_https_url(self):
        url = "https://web2.anl.az:81/read/page.php?bibid=vtls000415938"
        assert parse_anl_url(url) == "415938"

    def test_wrong_domain(self):
        url = "http://example.com/read/page.php?bibid=vtls000415938"
        assert parse_anl_url(url) is None

    def test_wrong_path(self):
        url = "http://web2.anl.az:81/other/page.php?bibid=vtls000415938"
        assert parse_anl_url(url) is None

    def test_missing_bibid(self):
        url = "http://web2.anl.az:81/read/page.php?other=value"
        assert parse_anl_url(url) is None

    def test_empty_bibid(self):
        url = "http://web2.anl.az:81/read/page.php?bibid="
        assert parse_anl_url(url) is None

    def test_non_numeric_bibid(self):
        url = "http://web2.anl.az:81/read/page.php?bibid=abc"
        assert parse_anl_url(url) is None

    def test_malformed_url(self):
        assert parse_anl_url("not-a-url") is None
        assert parse_anl_url("") is None


# ---------------------------------------------------------------------------
# get_total_pages (mocked HTTP)
# ---------------------------------------------------------------------------

class TestGetTotalPages:
    """Tests for :func:`anl.get_total_pages` with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_parses_page_count(self):
        html = (
            '<script>var last_page_params="?bibid=415938&pno=120";</script>'
        )
        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = AsyncMock(return_value=html)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        total = await get_total_pages(mock_session, "415938")
        assert total == 120

    @pytest.mark.asyncio
    async def test_raises_on_missing_page_count(self):
        html = "<html><body>No page info</body></html>"
        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = AsyncMock(return_value=html)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        with pytest.raises(ValueError, match="Səhifə sayını"):
            await get_total_pages(mock_session, "415938")


# ---------------------------------------------------------------------------
# download_book (mocked)
# ---------------------------------------------------------------------------

class TestDownloadBook:
    """Integration-style test for :func:`anl.download_book` with mocks."""

    @pytest.mark.asyncio
    async def test_produces_pdf(self):
        # Create a JPEG image large enough to pass MIN_IMAGE_SIZE check
        import os

        from PIL import Image

        img = Image.frombytes("RGB", (50, 50), os.urandom(50 * 50 * 3))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()

        page_html = (
            '<script>var last_page_params="?bibid=1&pno=2";</script>'
            '<h2 class="book-title font-f-book-reg">Test Book</h2>'
        )

        def fake_get(url, **kwargs):
            mock_resp = AsyncMock()
            mock_resp.raise_for_status = MagicMock()
            if "img.php" in url:
                mock_resp.read = AsyncMock(return_value=jpeg_bytes)
            else:
                mock_resp.text = AsyncMock(return_value=page_html)
                mock_resp.read = AsyncMock(return_value=jpeg_bytes)
            mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_resp.__aexit__ = AsyncMock(return_value=False)
            return mock_resp

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=fake_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("anl.aiohttp.ClientSession", return_value=mock_session):
            with patch("anl.asyncio.sleep", new_callable=AsyncMock):
                title, pdf_bytes = await download_book("1")

        assert title == "Test Book"
        assert pdf_bytes[:4] == b"%PDF"
