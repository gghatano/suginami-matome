"""X(@gg_hatano) の #方南町 投稿 — rss.app のRSSフィードから取得。"""

import logging
import re

import feedparser

from base import BaseScraper, Item, USER_AGENT

logger = logging.getLogger(__name__)

SOURCE = "X @gg_hatano"
SOURCE_KEY = "x_honancho"
SOURCE_URL = "https://x.com/gg_hatano"
FEED_URL = "https://rss.app/feeds/bJMyPNo2Ue8x8f4M.xml"

# 抽出条件: 本文にこのいずれかを含む投稿だけを採用する
KEYWORDS = ("#方南町", "方南町")


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(entry) -> str:
    parsed = getattr(entry, "published_parsed", None) or getattr(
        entry, "updated_parsed", None
    )
    if parsed:
        return f"{parsed.tm_year:04d}-{parsed.tm_mon:02d}-{parsed.tm_mday:02d}"
    return ""


def _extract_image(entry) -> str:
    """RSSエントリから画像URLを取得する（rss.app は media/enclosure を含むことが多い）。"""
    for key in ("media_content", "media_thumbnail"):
        media = getattr(entry, key, None)
        if media:
            url = media[0].get("url")
            if url:
                return url
    for link in getattr(entry, "links", []):
        if link.get("rel") == "enclosure" and "image" in link.get("type", ""):
            return link.get("href", "")
    content = getattr(entry, "summary", "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    if m:
        return m.group(1)
    return ""


def _is_retweet_or_reply(title: str, summary: str) -> bool:
    """リツイート/リプライを除外するための判定。"""
    text = (title or summary or "").lstrip()
    # リツイート（RT @user: ...）
    if text.startswith("RT @") or text.startswith("RT@"):
        return True
    # リプライ（先頭が @user で始まる）
    if re.match(r"^@\w+", text):
        return True
    return False


class XHonanchoScraper(BaseScraper):
    def fetch(self) -> list[Item]:
        try:
            feed = feedparser.parse(FEED_URL, agent=USER_AGENT)
        except Exception as e:  # noqa: BLE001
            logger.warning("[%s] フィード取得失敗: %s", SOURCE_KEY, e)
            return []

        items: list[Item] = []
        for entry in feed.entries:
            title = _strip_html(getattr(entry, "title", ""))
            url = getattr(entry, "link", "").strip()
            summary = _strip_html(getattr(entry, "summary", ""))
            if not url:
                continue

            blob = f"{title} {summary}"
            # 条件: #方南町（または方南町）を含む
            if not any(k in blob for k in KEYWORDS):
                continue
            # リツイート・リプライは除外
            if _is_retweet_or_reply(title, summary):
                continue

            # タイトルが空/長すぎる場合は本文から整える
            display_title = title or summary
            if len(display_title) > 80:
                display_title = display_title[:80] + "…"
            # 概要がタイトルと同一なら重複表示を避ける
            if summary == title:
                summary = ""
            elif len(summary) > 200:
                summary = summary[:200] + "…"

            if not display_title:
                continue

            items.append(
                Item(
                    source=SOURCE,
                    source_key=SOURCE_KEY,
                    source_url=SOURCE_URL,
                    title=display_title,
                    url=url,
                    summary=summary,
                    published_at=_parse_date(entry),
                    category="方南町",
                    image=_extract_image(entry),
                )
            )
        logger.info("[%s] %d件取得", SOURCE_KEY, len(items))
        return items
