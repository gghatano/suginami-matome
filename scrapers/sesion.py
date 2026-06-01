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


# プレースホルダ／ロゴ等として除外したい画像URLのパターン
_SKIP_IMG_RE = re.compile(
    r"(logo|icon|sprite|blank|spacer|no[-_]?image|noimage|dummy|loading)", re.I
)


def _extract_image(card, link) -> str:
    """イベントカードからサムネイル画像URLを抽出する。失敗時は空文字。

    タイトルリンクの直近の親に画像が無いこともあるため、祖先を数段
    たどって最初に見つかった有効な画像を返す。
    """
    candidates = []
    if card is not None:
        candidates.append(card)
    node = link
    for _ in range(4):  # 祖先を最大4段たどる
        if node is None:
            break
        candidates.append(node)
        node = node.parent

    for scope in candidates:
        for img in scope.find_all("img"):
            # 遅延読み込み属性を優先的に見る
            src = (
                img.get("data-src")
                or img.get("data-original")
                or img.get("data-lazy-src")
                or img.get("src")
                or ""
            ).strip()
            if not src and img.get("srcset"):
                # srcset の先頭URLを使う
                src = img["srcset"].split(",")[0].strip().split(" ")[0]
            if not src or src.startswith("data:"):
                continue
            if _SKIP_IMG_RE.search(src):
                continue
            return absolute_url(PAGE_URL, src)
    return ""


class SesionScraper(BaseScraper):
    def fetch(self) -> list[Item]:
        soup = get_soup(PAGE_URL)
        if soup is None:
            return []

        items: list[Item] = []
        seen: set[str] = set()

        container = soup.find("main") or soup

        # イベント詳細へのリンクのみを拾う。
        # 個別ページは /event/{カテゴリ}/{数字ID} 形式。
        # カテゴリ一覧(/eventcat/)や「前の月へ/次の月へ」等のページ送り
        # (?postyear=...&postmonth=... クエリ) は除外する。
        detail_re = re.compile(r"/event/[^/?]+/\d+")
        for a in container.find_all("a", href=True):
            href = a["href"].strip()
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue
            if not detail_re.search(href):
                continue
            url = absolute_url(PAGE_URL, href)
            if url in seen or url.rstrip("/") == PAGE_URL.rstrip("/"):
                continue
            seen.add(url)

            card = a.find_parent(["article", "li", "div"])
            context = card.get_text(" ", strip=True) if card else title
            published = _extract_date(context)
            image = _extract_image(card, a)

            items.append(
                Item(
                    source=SOURCE,
                    source_key=SOURCE_KEY,
                    source_url=SOURCE_URL,
                    title=title,
                    url=url,
                    published_at=published,
                    category="イベント",
                    image=image,
                )
            )

        logger.info("[%s] %d件取得", SOURCE_KEY, len(items))
        return items
