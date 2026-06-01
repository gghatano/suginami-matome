"""HTML取得の共通ユーティリティ。"""

import logging
import re

import requests
from bs4 import BeautifulSoup

from base import USER_AGENT

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 20


def get_soup(url: str) -> BeautifulSoup | None:
    """URLを取得してBeautifulSoupを返す。失敗時はNone。"""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        # 文字化け対策: apparent_encoding を優先
        if resp.encoding is None or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:  # noqa: BLE001
        logger.warning("HTML取得失敗 %s: %s", url, e)
        return None


def absolute_url(base: str, href: str) -> str:
    """相対URLを絶対URLに変換する。"""
    from urllib.parse import urljoin

    return urljoin(base, href)


# og:image 等として参照するメタタグ（優先順）
_OG_IMAGE_SELECTORS = [
    ("meta", {"property": "og:image"}),
    ("meta", {"property": "og:image:url"}),
    ("meta", {"property": "og:image:secure_url"}),
    ("meta", {"name": "og:image"}),
    ("meta", {"name": "twitter:image"}),
    ("meta", {"name": "twitter:image:src"}),
    ("meta", {"property": "twitter:image"}),
]


def get_og_image(url: str) -> str:
    """記事ページから og:image / twitter:image を取得する。失敗時は空文字。"""
    soup = get_soup(url)
    if soup is None:
        return ""
    for name, attrs in _OG_IMAGE_SELECTORS:
        tag = soup.find(name, attrs=attrs)
        if tag and tag.get("content", "").strip():
            return absolute_url(url, tag["content"].strip())
    return ""


# ロゴ／共通OGP／プレースホルダ等として除外したい画像URLのパターン
PLACEHOLDER_IMG_RE = re.compile(
    r"(logo|icon|sprite|blank|spacer|no[-_]?image|noimage|dummy|loading|"
    r"ogp|/common/|/themes/|/assets/|default)",
    re.I,
)

# 本文画像を探す際のコンテナ候補（記事本文に近い順）
_CONTENT_SELECTORS = (
    ".entry-content, article, main, #main, #contents, .post, .content"
)


def _img_src(img) -> str:
    """img要素から遅延読み込み属性も考慮して画像URLを取り出す。"""
    src = (
        img.get("data-src")
        or img.get("data-original")
        or img.get("data-lazy-src")
        or img.get("src")
        or ""
    ).strip()
    if not src and img.get("srcset"):
        src = img["srcset"].split(",")[0].strip().split(" ")[0]
    return src


def get_article_image(url: str) -> str:
    """記事ページから「個別の」サムネイル画像を取得する。失敗時は空文字。

    1. 本文コンテナ内の最初の有効画像（ロゴ/共通OGP等は除外）
    2. なければ og:image / twitter:image（ただし共通OGP等のプレースホルダは除外）
    """
    soup = get_soup(url)
    if soup is None:
        return ""

    content = soup.select_one(_CONTENT_SELECTORS) or soup
    for img in content.find_all("img"):
        src = _img_src(img)
        if not src or src.startswith("data:"):
            continue
        if PLACEHOLDER_IMG_RE.search(src):
            continue
        return absolute_url(url, src)

    for name, attrs in _OG_IMAGE_SELECTORS:
        tag = soup.find(name, attrs=attrs)
        content_attr = tag.get("content", "").strip() if tag else ""
        if content_attr and not PLACEHOLDER_IMG_RE.search(content_attr):
            return absolute_url(url, content_attr)
    return ""
