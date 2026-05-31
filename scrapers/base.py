"""共通基底クラスとデータモデル。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
import hashlib

# 各スクレイパーが共通で利用するUser-Agent
USER_AGENT = (
    "Mozilla/5.0 (compatible; SuginamiMatomeBot/1.0; "
    "+https://github.com/gghatano/suginami-matome)"
)


@dataclass
class Item:
    source: str
    source_key: str
    source_url: str
    title: str
    url: str
    summary: str = ""
    published_at: str = ""
    fetched_at: str = field(default_factory=lambda: date.today().isoformat())
    category: str = ""

    @property
    def id(self) -> str:
        digest = hashlib.md5(self.url.encode()).hexdigest()[:8]
        return f"{self.source_key}_{digest}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "source_key": self.source_key,
            "source_url": self.source_url,
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "published_at": self.published_at,
            "fetched_at": self.fetched_at,
            "category": self.category,
        }


class BaseScraper(ABC):
    @abstractmethod
    def fetch(self) -> list[Item]:
        """新着アイテムのリストを返す。失敗時は空リストを返す（例外を投げない）。"""
        ...
