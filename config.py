import os

BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")

ANL_BASE_URL: str = "http://web2.anl.az:81/read"
ANL_PAGE_URL: str = f"{ANL_BASE_URL}/page.php"
ANL_IMG_URL: str = f"{ANL_BASE_URL}/img.php"

REQUEST_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": ANL_BASE_URL,
}

# Delay between page requests in seconds
REQUEST_DELAY: float = 1.0

# Minimum valid image size in bytes
MIN_IMAGE_SIZE: int = 1024

# Maximum file size Telegram allows for document upload (50 MB)
TELEGRAM_MAX_FILE_SIZE: int = 50 * 1024 * 1024
