"""HTML取得の共通ユーティリティ。"""

import logging

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
