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

        # 投稿詳細は /article/{数字} を含むURL。ページ構造変更に強いよう
        # 全アンカーから該当リンクを直接拾う。
        article_re = re.compile(r"/article/\d+")
        anchors = soup.find_all("a", href=True)
        for a in anchors:
            href = a["href"].strip()
            if not article_re.search(href):
                continue
            # タイトル: title属性 → 自身のテキスト → 内包する見出し
            title = (a.get("title") or a.get_text(" ", strip=True) or "").strip()
            if len(title) < 4:
                node = a.find_parent(["li", "article", "div"])
                if node:
                    h = node.find(["h2", "h3"])
                    if h:
                        title = h.get_text(" ", strip=True)
            title = title.strip()
            if not title or len(title) < 4:
                continue
            url = absolute_url(PAGE_URL, href)
            if url in seen:
                continue
            seen.add(url)

            node = a.find_parent(["li", "article", "div"])
            context = node.get_text(" ", strip=True) if node else title
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

        logger.info(
            "[%s] %d件取得（アンカー総数%d）", SOURCE_KEY, len(items), len(anchors)
        )
        return items
