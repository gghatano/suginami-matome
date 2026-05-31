"""杉並区社会福祉協議会 — 新着・イベント情報。"""

import logging
import re

from base import BaseScraper, Item
from httputil import get_soup, absolute_url

logger = logging.getLogger(__name__)

SOURCE = "杉並区社会福祉協議会"
SOURCE_KEY = "sugisyakyo"
SOURCE_URL = "https://www.sugisyakyo.com/"
PAGE_URL = "https://www.sugisyakyo.com/"

_DATE_RE = re.compile(r"(\d{4})[年/.-](\d{1,2})[月/.-](\d{1,2})")


def _extract_date(text: str) -> str:
    m = _DATE_RE.search(text or "")
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return ""


class SugisyakyoScraper(BaseScraper):
    def fetch(self) -> list[Item]:
        soup = get_soup(PAGE_URL)
        if soup is None:
            return []

        items: list[Item] = []
        seen: set[str] = set()

        # 新着情報リストを優先的に探す
        nodes = soup.select(
            ".news li, .topics li, .information li, dl.news dd, li"
        )

        # 新着・お知らせ記事のみ拾う。
        # 記事は WordPress 投稿 (/wp/?p=NNNN) または /news/ 配下。
        # サイト共通メニュー（/about/ /purpose/ /kanri/ 等の固定ページ）は除外する。
        news_re = re.compile(r"/wp/.*[?&]p=\d+|/news/")
        for node in nodes:
            a = node.find("a", href=True)
            if not a:
                continue
            href = a["href"].strip()
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue
            # 外部・トップ・アンカーは除外
            if href.startswith("#") or href.startswith("javascript"):
                continue
            if not news_re.search(href):
                continue
            url = absolute_url(PAGE_URL, href)
            if url in seen or url.rstrip("/") == SOURCE_URL.rstrip("/"):
                continue
            seen.add(url)

            context = node.get_text(" ", strip=True)
            published = _extract_date(context)

            items.append(
                Item(
                    source=SOURCE,
                    source_key=SOURCE_KEY,
                    source_url=SOURCE_URL,
                    title=title,
                    url=url,
                    published_at=published,
                    category="お知らせ",
                )
            )

        logger.info("[%s] %d件取得", SOURCE_KEY, len(items))
        return items
