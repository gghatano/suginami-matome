"""エントリポイント。全スクレイパーを実行して data/items.json を更新する。"""

import json
import logging
import sys
import time
from pathlib import Path

# scrapers ディレクトリを import パスに追加（単体実行・モジュール実行どちらでも動くように）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from base import BaseScraper  # noqa: E402
from httputil import get_article_image, PLACEHOLDER_IMG_RE  # noqa: E402
from goguynet import GoguynetScraper  # noqa: E402
from suginami_city import SuginamiCityScraper  # noqa: E402
from sesion import SesionScraper  # noqa: E402
from mypl import MyplScraper  # noqa: E402
from jmty import JmtyScraper  # noqa: E402
from sugisyakyo import SugisyakyoScraper  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("fetch")

# data/items.json のパス（リポジトリルート基準）
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "items.json"

# 最大保持件数
MAX_ITEMS = 500

# スクレイパー間のリクエスト間隔（秒）
SLEEP_BETWEEN = 2

# サムネイル画像の補完（記事ページの og:image）設定
ENRICH_IMAGES = True          # image が空のアイテムを og:image で補完する
MAX_ENRICH_PER_RUN = 80       # 1回の実行で記事ページを取得する最大件数（負荷抑制）
ENRICH_SLEEP = 1              # 補完リクエスト間のインターバル（秒）
# 補完対象外のソース（anti-bot 等で取得できないもの）
ENRICH_SKIP_SOURCES = {"jmty"}

# 実行するスクレイパー一覧（実装順）
SCRAPERS: list[BaseScraper] = [
    GoguynetScraper(),
    SuginamiCityScraper(),
    SesionScraper(),
    MyplScraper(),
    JmtyScraper(),
    SugisyakyoScraper(),
]


def load_existing() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    try:
        with DATA_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        logger.warning("items.json がリストではありません。空として扱います。")
    except Exception as e:  # noqa: BLE001
        logger.warning("items.json の読み込みに失敗: %s", e)
    return []


def main() -> int:
    existing = load_existing()
    known_ids = {it.get("id") for it in existing if it.get("id")}
    logger.info("既存アイテム: %d件", len(existing))

    all_items = list(existing)
    added = 0

    for i, scraper in enumerate(SCRAPERS):
        name = scraper.__class__.__name__
        try:
            fetched = scraper.fetch()
        except Exception as e:  # noqa: BLE001 — 1サイトの失敗が他に影響しないように
            logger.warning("[%s] 実行中に例外: %s", name, e)
            fetched = []

        new_for_source = 0
        for item in fetched:
            d = item.to_dict()
            # published_at が無ければ fetched_at で代替
            if not d.get("published_at"):
                d["published_at"] = d["fetched_at"]
            if d["id"] in known_ids:
                continue
            known_ids.add(d["id"])
            all_items.append(d)
            new_for_source += 1
            added += 1
        logger.info("[%s] 新規 %d件追加", name, new_for_source)

        # 最後のスクレイパー以外はインターバルを挟む
        if i < len(SCRAPERS) - 1:
            time.sleep(SLEEP_BETWEEN)

    # published_at 降順でソート（同日内は fetched_at 降順）
    all_items.sort(
        key=lambda d: (d.get("published_at", ""), d.get("fetched_at", "")),
        reverse=True,
    )

    # 最大保持件数を超えたら古いものを削除
    if len(all_items) > MAX_ITEMS:
        logger.info(
            "保持件数 %d > %d のため古いものを削除", len(all_items), MAX_ITEMS
        )
        all_items = all_items[:MAX_ITEMS]

    # サムネイル画像の補完: 記事ページから「個別の」画像を取得して埋める。
    # 対象は image が空、またはロゴ/共通OGP等のプレースホルダ画像のもの。
    # 新規・既存を問わず（＝既存アイテムへのバックフィル/置換も兼ねる）、新しい順に
    # 最大 MAX_ENRICH_PER_RUN 件まで記事ページを取得する。
    if ENRICH_IMAGES:
        attempts = 0
        enriched = 0
        for d in all_items:
            if attempts >= MAX_ENRICH_PER_RUN:
                break
            if d.get("source_key") in ENRICH_SKIP_SOURCES:
                continue
            cur = d.get("image", "")
            # 既に「個別の」画像が入っているものはスキップ
            if cur and not PLACEHOLDER_IMG_RE.search(cur):
                continue
            url = d.get("url")
            if not url:
                continue
            attempts += 1
            try:
                img = get_article_image(url)
            except Exception as e:  # noqa: BLE001
                logger.warning("画像取得失敗 %s: %s", url, e)
                img = ""
            # プレースホルダ画像しか得られなければ空にして（フロントは
            # ファビコン表示にフォールバック）、全カード同一画像を避ける
            new_img = img if (img and not PLACEHOLDER_IMG_RE.search(img)) else ""
            if new_img != cur:
                d["image"] = new_img
                if new_img:
                    enriched += 1
            time.sleep(ENRICH_SLEEP)
        logger.info("画像補完: %d件取得 / %d件試行", enriched, attempts)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
        f.write("\n")

    logger.info(
        "完了: %d件追加 / 合計 %d件 → %s", added, len(all_items), DATA_PATH
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
