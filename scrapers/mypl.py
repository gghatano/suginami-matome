"""まいぷれ杉並区 — イベント一覧。"""

import logging
import re

from base import BaseScraper, Item
from httputil import get_soup, absolute_url

logger = logging.getLogger(__name__)

SOURCE = "まいぷれ杉並区"
SOURCE_KEY = "mypl"
SOURCE_URL = "https://suginami.mypl.net/"
PAGE_URL = "https://suginami.mypl.net/event/"

_DATE_RE = re.compile(r"(\d{4})[年/.-](\d{1,2})[月/.-](\d{1,2})")


def _extract_date(text: str) -> str:
    m = _DATE_RE.search(text or "")
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return ""


class MyplScraper(BaseScraper):
    def fetch(self) -> list[Item]:
        soup = get_soup(PAGE_URL)
        if soup is None:
            return []

        items: list[Item] = []
        seen: set[str] = set()

        container = soup.find("main") or soup

        for a in container.find_all("a", href=True):
            href = a["href"].strip()
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue
            # 詳細ページ /event/detail/ 等
            if "/event/" not in href or href.rstrip("/").endswith("/event"):
                continue
            url = absolute_url(PAGE_URL, href)
            if url in seen or url.rstrip("/") == PAGE_URL.rstrip("/"):
                continue
            seen.add(url)

            card = a.find_parent(["article", "li", "div"])
            context = card.get_text(" ", strip=True) if card else title
            published = _extract_date(context)
            summary = ""
            if card:
                summary = card.get_text(" ", strip=True)
                summary = re.sub(r"\s+", " ", summary)[:200]

            items.append(
                Item(
                    source=SOURCE,
                    source_key=SOURCE_KEY,
                    source_url=SOURCE_URL,
                    title=title,
                    url=url,
                    summary=summary,
                    published_at=published,
                    category="イベント",
                )
            )

        logger.info("[%s] %d件取得", SOURCE_KEY, len(items))
        return items
