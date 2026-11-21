# 杉並区イベントまとめ（トップページ）

区内のイベント情報サイトを1日1回クロールし、記事のタイトル・概要・リンクを1か所にまとめて見せるサイトです。

## 取得元

| `source_key` | サイト | 取得方法 | ファイル |
|---|---|---|---|
| `goguynet` | 号外NET杉並区 | RSS（feedparser） | `scrapers/goguynet.py` |
| `suginami_city` | 杉並区公式イベントカレンダー | HTML（requests + BeautifulSoup） | `scrapers/suginami_city.py` |
| `sesion` | セシオン杉並 | HTML | `scrapers/sesion.py` |
| `mypl` | まいぷれ杉並区 | HTML | `scrapers/mypl.py` |
| `jmty` | ジモティー杉並区 | HTML | `scrapers/jmty.py` |
| `sugisyakyo` | 杉並区社会福祉協議会 | HTML | `scrapers/sugisyakyo.py` |
| `x_honancho` | X（#方南町 の投稿） | rss.app の RSS | `scrapers/x_honancho.py` |

## 処理の流れ（`scrapers/fetch.py`）

1. `data/items.json` を読む
2. 各スクレイパーを順に実行する（間に2秒待つ。1つが失敗しても他は続ける）
3. 記事の `id`（`{source_key}_{URL の md5 先頭8桁}`）で重複を除いて追加する
4. タイトル・概要からイベント開催日を抽出して `event_dates` に入れる（`scrapers/dateextract.py`）
5. 画像がない記事は、記事ページの og:image で補う（1回80件まで。X とジモティーは対象外）
6. 新しい順に並べ、最大500件に切り詰めて書き戻す

各スクレイパーは `scrapers/base.py` の `BaseScraper` を継承し、`fetch()` で `Item` のリストを返します。失敗したときは例外を投げずに空のリストを返す決まりです。

## 定期実行

`.github/workflows/fetch.yml` が **毎日 23:00 JST**（UTC 14:00）に動き、`data/items.json` を `main` に直接コミットします。README や `spec.md` には「09:00」と書かれた古い記述が残っていますが、正しいのは 23:00 です。

## データ（`data/items.json`）

記事の配列です。主なフィールドは次のとおりです。全体は [`spec.md`](../spec.md) の「データスキーマ」を見てください。

| フィールド | 内容 |
|---|---|
| `id` | 重複排除のキー |
| `source` / `source_key` | 取得元の表示名・識別子 |
| `title` / `url` / `summary` | 記事 |
| `published_at` / `fetched_at` | 公開日・取得日（`YYYY-MM-DD`） |
| `event_dates` | 抽出した開催日（`YYYY-MM-DD` の配列） |
| `image` | サムネイル（なければ空文字） |

## 画面（`index.html`）

- 上段：月カレンダー（`event_dates` から作る）と、注目の記事・近日のイベント
- 中段：キーワード・期間・カテゴリーの絞り込み、取得元とエリアのチップ
- 下段：記事の一覧（20件ごとのページ送り）
- ヘッダー：児童館カレンダーへのリンク、GitHub、ダークモード切り替え（`localStorage` の `theme` に保存。児童館カレンダーと共有）

## 取得元を足すとき

1. `scrapers/<key>.py` に `BaseScraper` を継承したクラスを書く（失敗時は空リスト）
2. `scrapers/fetch.py` の `SCRAPERS` に追加する
3. ローカルで `python scrapers/fetch.py` を2回実行し、2回目に重複が追加されないこと（冪等性）を確かめる
4. 画面側の取得元の色（`SOURCE_COLORS`）とアイコン（`assets/icons/`）を必要に応じて足す
5. README とこのドキュメントの表を更新する
