"""杉並区公式イベントカレンダー（新着）。"""

import logging
import re

from base import BaseScraper, Item
from httputil import get_soup, absolute_url

logger = logging.getLogger(__name__)

SOURCE = "杉並区公式"
SOURCE_KEY = "suginami_city"
SOURCE_URL = "https://www.city.suginami.tokyo.jp/"
PAGE_URL = "https://www.city.suginami.tokyo.jp/event/shinnchaku.html"

# 日付らしき文字列（例: 2026年5月31日 / 2026/5/31）
_DATE_RE = re.compile(r"(\d{4})[年/.-](\d{1,2})[月/.-](\d{1,2})")


def _extract_date(text: str) -> str:
    m = _DATE_RE.search(text or "")
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return ""


class SuginamiCityScraper(BaseScraper):
    def fetch(self) -> list[Item]:
        soup = get_soup(PAGE_URL)
        if soup is None:
            return []

        items: list[Item] = []
        seen: set[str] = set()

        # 本文領域内のリンクを対象にする（ナビ等を避ける）
        container = (
            soup.find("main")
            or soup.find(id="contents")
            or soup.find(id="main")
            or soup
        )

        for a in container.find_all("a", href=True):
            href = a["href"].strip()
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue
            # イベント詳細ページらしいリンクに絞る
            if "/event/" not in href:
                continue
            url = absolute_url(PAGE_URL, href)
            if url in seen or url.rstrip("/") == PAGE_URL.rstrip("/"):
                continue
            seen.add(url)

            # 近傍テキストから日付を拾う
            li = a.find_parent(["li", "dd", "tr", "p"])
            context = li.get_text(" ", strip=True) if li else title
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
