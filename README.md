# 杉並区イベントまとめ

杉並区の複数のイベント情報サイトを1日1回クロールし、タイトル・概要・リンクをまとめて表示する静的アグリゲーションサイトです。

- ホスティング: GitHub Pages（静的）
- データ蓄積: [`data/items.json`](data/items.json)（URL重複排除・追記式）
- 更新: GitHub Actions cron（毎日 09:00 JST）

詳細な仕様は [`spec.md`](spec.md) を参照してください。

## ローカルでの実行

```bash
pip install -r requirements.txt
python scrapers/fetch.py
```

実行すると各サイトをクロールし、`data/items.json` に新着アイテムを追記します
（`id` = `{source_key}_{url の md5 先8桁}` により重複排除）。

フロントエンドは `index.html` を任意の静的サーバーで開いて確認できます。

```bash
python -m http.server 8000
# → http://localhost:8000/ を開く
```

## クロール対象サイト

| source_key | サイト | 取得方法 |
|---|---|---|
| `goguynet` | 号外NET杉並区 | RSS (feedparser) |
| `suginami_city` | 杉並区公式イベントカレンダー | requests + BeautifulSoup |
| `sesion` | セシオン杉並 | requests + BeautifulSoup |
| `mypl` | まいぷれ杉並区 | requests + BeautifulSoup |
| `jmty` | ジモティー杉並区 | requests + BeautifulSoup |
| `sugisyakyo` | 杉並区社会福祉協議会 | requests + BeautifulSoup |

## 注意事項

- 各サイトの robots.txt・利用規約を確認のうえ、過度な負荷をかけないよう運用してください。
- スクレイパー間には `time.sleep(2)` のインターバルを挟んでいます。
- 1サイトの失敗が他サイトに影響しないよう、各スクレイパーは例外をキャッチして空リストを返します。
