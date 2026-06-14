# 杉並区イベントまとめサイト — spec.md

## 概要
杉並区の複数のイベント情報サイトを1日1回クロールし、
タイトル・概要・リンクをまとめて表示するアグリゲーションサイト。

- ホスティング: GitHub Pages（静的）
- データ蓄積: `data/items.json`（リポジトリ内に追記）
- 更新: GitHub Actions cron（毎日09:00 JST）

---

## リポジトリ構成
```
suginami-events/
├── .github/
│   └── workflows/
│       └── fetch.yml          # cron → fetch → commit → Pages deploy
├── data/
│   └── items.json             # 蓄積データ（URL重複排除・追記式）
├── scrapers/
│   ├── fetch.py               # エントリポイント。全スクレイパーを呼ぶ
│   ├── base.py                # 共通基底クラス
│   ├── goguynet.py            # 号外NET杉並区
│   ├── suginami_city.py       # 杉並区公式イベントカレンダー
│   ├── sesion.py              # セシオン杉並
│   ├── mypl.py                # まいぷれ杉並区
│   ├── jmty.py                # ジモティー杉並区
│   └── sugisyakyo.py          # 杉並区社会福祉協議会
├── index.html                 # フロントエンド（vanilla JS）
└── spec.md                    # 本ファイル
```

---

## データスキーマ — `data/items.json`
```json
[
  {
    "id": "goguynet_abc123",
    "source": "号外NET杉並区",
    "source_key": "goguynet",
    "source_url": "https://suginami.goguynet.jp/",
    "title": "高円寺びっくり大道芸2026が開催",
    "url": "https://suginami.goguynet.jp/2026/04/21/koenji-daidogei2026/",
    "summary": "4月25日・26日の2日間、高円寺駅周辺で第18回びっくり大道芸が開催されます。",
    "published_at": "2026-04-20",
    "fetched_at": "2026-05-31",
    "category": "イベント"
  }
]
```

### フィールド定義
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string | ✅ | `{source_key}_{urlのmd5先8桁}` で生成。重複排除キー |
| `source` | string | ✅ | 表示用サイト名 |
| `source_key` | string | ✅ | スクレイパー識別子（英数字） |
| `source_url` | string | ✅ | サイトトップURL |
| `title` | string | ✅ | 記事タイトル |
| `url` | string | ✅ | 記事の直接URL |
| `summary` | string | | 概要文（取得できれば。なければ空文字） |
| `published_at` | string | | `YYYY-MM-DD`。取得できなければ `fetched_at` で代替 |
| `fetched_at` | string | ✅ | `YYYY-MM-DD`。スクレイプ実行日 |
| `category` | string | | "イベント" / "お知らせ" / "講座" 等 |
| `image` | string | | サムネイル画像URL（取得できれば。なければ空文字。フロントはファビコン/文字アバターにフォールバック） |

---

## クロール対象サイト
実装順は下記のとおり。**1サイトずつ追加し、fetch.py に組み込んで冪等に動作確認する。**

### フェーズ1（RSS あり → 実装簡単）

#### 1. 号外NET杉並区
- `source_key`: `goguynet`
- トップURL: `https://suginami.goguynet.jp/`
- RSS: `https://suginami.goguynet.jp/feed/`
- 取得方法: `feedparser` でRSS取得
- 取得フィールド: `entry.title` / `entry.link` / `entry.summary` / `entry.published`

### フェーズ2（HTML パース）

#### 2. 杉並区公式イベントカレンダー
- `source_key`: `suginami_city`
- URL: `https://www.city.suginami.tokyo.jp/event/shinnchaku.html`
- 取得方法: `requests` + `BeautifulSoup`
- 取得対象: 新着イベント一覧の `<li>` 要素（タイトル・リンク・日付）

#### 3. セシオン杉並
- `source_key`: `sesion`
- URL: `https://www.sesion-suginami.jp/event`
- 取得方法: `requests` + `BeautifulSoup`
- 取得対象: イベント一覧カード（タイトル・日時・URL）

#### 4. まいぷれ杉並区
- `source_key`: `mypl`
- URL: `https://suginami.mypl.net/event/`
- 取得方法: `requests` + `BeautifulSoup`
- 取得対象: イベント一覧（タイトル・リンク・概要）

#### 5. ジモティー杉並区
- `source_key`: `jmty`
- URL: `https://jmty.jp/tokyo/eve-all/g-all/a-270-suginami`
- 取得方法: `requests` + `BeautifulSoup`
- 取得対象: 投稿一覧（タイトル・リンク・投稿日）

#### 6. 杉並区社会福祉協議会
- `source_key`: `sugisyakyo`
- URL: `https://www.sugisyakyo.com/`
- 取得方法: `requests` + `BeautifulSoup`
- 取得対象: 新着・イベント情報（タイトル・リンク・日付）

### フェーズ3（X / SNS）

#### 7. X @gg_hatano（方南町）
- `source_key`: `x_honancho`
- トップURL: `https://x.com/gg_hatano`
- フィード: rss.app で生成した検索フィード（`from:gg_hatano #方南町`）のRSS
- 取得方法: `feedparser` でRSS取得
- 抽出条件: 本文に「#方南町 / 方南町」を含み、**リツイート・リプライは除外**
- 画像: フィードの media/enclosure を使用（記事ページの og:image 補完は対象外）

---

## スクレイパー基底クラス — `scrapers/base.py`
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
import hashlib

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
```

---

## fetch.py の動作仕様
```
1. data/items.json を読み込む（なければ空リスト）
2. 既存アイテムの id を set に格納
3. 全スクレイパーを順番に実行
4. 取得した Item のうち id が未登録のものだけをリストに追加
5. リスト全体を published_at 降順でソート
6. data/items.json に書き戻す（pretty JSON, ensure_ascii=False）
7. 追加件数をログ出力して終了
```

### 冪等性の保証
- 同じURLを2回取得しても `id`（= md5ベース）が同じため追記されない
- 実行のたびにファイルが肥大化しないよう、**最大保持件数を500件**とする（古い順に削除）

---

## GitHub Actions — `.github/workflows/fetch.yml`
```yaml
name: Fetch Events
on:
  schedule:
    - cron: "0 0 * * *"   # UTC 00:00 = JST 09:00
  workflow_dispatch:        # 手動実行も可能
jobs:
  fetch:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install requests beautifulsoup4 feedparser lxml
      - name: Run scrapers
        run: python scrapers/fetch.py
      - name: Commit updated data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/items.json
          git diff --cached --quiet || git commit -m "chore: update events $(date +%Y-%m-%d)"
          git push
  deploy:
    needs: fetch
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: main   # fetch job のコミット後を取得
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: "."
      - uses: actions/deploy-pages@v4
        id: deployment
```

---

## フロントエンド — `index.html`
### 要件
- vanilla JS のみ（ビルド不要）
- `data/items.json` を fetch して表示
- フィルタ: サイト別（source_key）・カテゴリ別
- ソート: 新着順（published_at 降順）固定
- カード表示: タイトル（リンク）・サイト名バッジ・日付・概要テキスト
- レスポンシブ対応（モバイル閲覧も想定）

### モック先行
- **最初に `index.html` のモックを `data/items.json` のサンプルデータで作る**
- データが実際に入ってきても崩れないよう設計する

---

## 実装ロードマップ
| ステップ | 作業内容 | 完了条件 |
|---|---|---|
| 0 | `spec.md` 作成 | 本ファイル |
| 1 | `index.html` モック | サンプルJSONで表示・フィルタ動作確認 |
| 2 | `base.py` + `fetch.py` 骨格 | `python scrapers/fetch.py` が空で動く |
| 3 | `goguynet.py`（RSS） | fetch実行 → items.json に追記確認 |
| 4 | `suginami_city.py` | 同上 |
| 5 | `sesion.py` | 同上 |
| 6 | `mypl.py` | 同上 |
| 7 | `jmty.py` | 同上 |
| 8 | `sugisyakyo.py` | 同上 |
| 9 | `fetch.yml` | Actions手動実行 → deploy確認 |

---

## 注意事項
- **robots.txt の確認**: 各サイトのクロール許可を実装前に確認すること
- **User-Agent**: `Mozilla/5.0` ベースの一般的なものを指定し、過負荷をかけない
- **リクエスト間隔**: スクレイパー間に `time.sleep(2)` を挟む
- **エラー処理**: 1サイトの失敗が他サイトに影響しないよう、各スクレイパーは独立して例外をキャッチしログ出力する
- **文字コード**: `ensure_ascii=False` で日本語をそのままJSONに保存
