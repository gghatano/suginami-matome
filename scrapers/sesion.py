"""セシオン杉並 — イベント一覧。"""

import logging
import re

from base import BaseScraper, Item
from httputil import get_soup, absolute_url

logger = logging.getLogger(__name__)

SOURCE = "セシオン杉並"
SOURCE_KEY = "sesion"
SOURCE_URL = "https://www.sesion-suginami.jp/"
PAGE_URL = "https://www.sesion-suginami.jp/event"

_DATE_RE = re.compile(r"(\d{4})[年/.-](\d{1,2})[月/.-](\d{1,2})")


def _extract_date(text: str) -> str:
    m = _DATE_RE.search(text or "")
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return ""


class SesionScraper(BaseScraper):
    def fetch(self) -> list[Item]:
        soup = get_soup(PAGE_URL)
        if soup is None:
            return []

        items: list[Item] = []
        seen: set[str] = set()

        container = soup.find("main") or soup

        # イベント詳細へのリンクを拾う
        for a in container.find_all("a", href=True):
            href = a["href"].strip()
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue
            if "/event" not in href:
                continue
            url = absolute_url(PAGE_URL, href)
            if url in seen or url.rstrip("/") == PAGE_URL.rstrip("/"):
                continue
            seen.add(url)

            card = a.find_parent(["article", "li", "div"])
            context = card.get_text(" ", strip=True) if card else title
            published = _extract_date(context)

            items.append(
                Item(
                    source=SOURCE,
                    source_key=SOURCE_KEY,
                    source_url=SOURCE_URL,
                    title=title,
                    url=url,
                    published_at=published,
                    category="イベント",
                )
            )

        logger.info("[%s] %d件取得", SOURCE_KEY, len(items))
        return items
