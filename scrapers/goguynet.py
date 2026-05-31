"""号外NET杉並区 — RSSフィードから取得。"""

import logging
import re

import feedparser

from base import BaseScraper, Item, USER_AGENT

logger = logging.getLogger(__name__)

SOURCE = "号外NET杉並区"
SOURCE_KEY = "goguynet"
SOURCE_URL = "https://suginami.goguynet.jp/"
FEED_URL = "https://suginami.goguynet.jp/feed/"


def _strip_html(text: str) -> str:
    """簡易的にHTMLタグを除去して概要テキストを整える。"""
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _extract_image(entry) -> str:
    """RSSエントリからサムネイル画像URLを取得する（追加リクエストなし）。"""
    # media:content / media:thumbnail
    for key in ("media_content", "media_thumbnail"):
        media = getattr(entry, key, None)
        if media:
            url = media[0].get("url")
            if url:
                return url
    # enclosure（画像）
    for link in getattr(entry, "links", []):
        if link.get("rel") == "enclosure" and "image" in link.get("type", ""):
            return link.get("href", "")
    # 本文中の最初の <img>
    content = getattr(entry, "summary", "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    if m:
        return m.group(1)
    return ""


def _parse_date(entry) -> str:
    """feedparser の published_parsed から YYYY-MM-DD を作る。"""
    parsed = getattr(entry, "published_parsed", None) or getattr(
        entry, "updated_parsed", None
    )
    if parsed:
        return f"{parsed.tm_year:04d}-{parsed.tm_mon:02d}-{parsed.tm_mday:02d}"
    return ""


class GoguynetScraper(BaseScraper):
    def fetch(self) -> list[Item]:
        try:
            feed = feedparser.parse(
                FEED_URL, agent=USER_AGENT
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("[%s] フィード取得失敗: %s", SOURCE_KEY, e)
            return []

        items: list[Item] = []
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            url = getattr(entry, "link", "").strip()
            if not title or not url:
                continue
            summary = _strip_html(getattr(entry, "summary", ""))
            if len(summary) > 200:
                summary = summary[:200] + "…"
            items.append(
                Item(
                    source=SOURCE,
                    source_key=SOURCE_KEY,
                    source_url=SOURCE_URL,
                    title=title,
                    url=url,
                    summary=summary,
                    published_at=_parse_date(entry),
                    category="イベント",
                    image=_extract_image(entry),
                )
            )
        logger.info("[%s] %d件取得", SOURCE_KEY, len(items))
        return items
