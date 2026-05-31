"""ジモティー杉並区 — イベント投稿一覧。"""

import logging
import re

from base import BaseScraper, Item
from httputil import get_soup, absolute_url

logger = logging.getLogger(__name__)

SOURCE = "ジモティー杉並区"
SOURCE_KEY = "jmty"
SOURCE_URL = "https://jmty.jp/"
PAGE_URL = "https://jmty.jp/tokyo/eve-all/g-all/a-270-suginami"

_DATE_RE = re.compile(r"(\d{4})[年/.-](\d{1,2})[月/.-](\d{1,2})")


def _extract_date(text: str) -> str:
    m = _DATE_RE.search(text or "")
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return ""


class JmtyScraper(BaseScraper):
    def fetch(self) -> list[Item]:
        soup = get_soup(PAGE_URL)
        if soup is None:
            return []

        items: list[Item] = []
        seen: set[str] = set()

        # 投稿一覧の各記事ブロック
        articles = soup.select("li.p-articles-list-item, .p-item-list li, article")
        if not articles:
            articles = soup.find_all("a", href=True)

        for node in articles:
            a = node if node.name == "a" else node.find("a", href=True)
            if not a or not a.get("href"):
                continue
            href = a["href"].strip()
            # 投稿詳細は /tokyo/.../数字 形式
            if not re.search(r"/\d+$", href):
                continue
            title = a.get("title") or a.get_text(strip=True)
            title = (title or "").strip()
            if not title or len(title) < 4:
                continue
            url = absolute_url(PAGE_URL, href)
            if url in seen:
                continue
            seen.add(url)

            context = node.get_text(" ", strip=True) if node.name != "a" else title
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
