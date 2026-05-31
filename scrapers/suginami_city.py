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

        # 新着ページはサイト全体のイベントを集約するため、詳細URLは /event/ 配下とは
        # 限らない。そこで「日付を伴う内部リンク（=新着リストの行）」のみを採用する。
        # グローバルナビ等は日付を持たないため自然に除外される。
        page_path = PAGE_URL.rsplit("/", 1)[0]  # .../event
        raw = 0
        for a in container.find_all("a", href=True):
            href = a["href"].strip()
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue
            url = absolute_url(PAGE_URL, href)
            # 杉並区公式サイト内のページのみ
            if "city.suginami.tokyo.jp" not in url:
                continue
            # 一覧ページ自身・添付ファイル等は除外
            if url.rstrip("/") == PAGE_URL.rstrip("/"):
                continue
            if url in seen:
                continue
            raw += 1

            # 行コンテキスト（親 li/dd/tr と直前の dt 等）から日付を探す
            row = a.find_parent(["li", "dd", "tr"]) or a.parent
            context = row.get_text(" ", strip=True) if row else title
            prev = row.find_previous_sibling() if row else None
            if prev:
                context = prev.get_text(" ", strip=True) + " " + context
            published = _extract_date(context)
            # 日付が取れない＝新着リストの項目ではない（ナビ等）→ 除外
            if not published:
                continue

            seen.add(url)
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

        logger.info("[%s] %d件取得（候補リンク%d）", SOURCE_KEY, len(items), raw)
        return items
