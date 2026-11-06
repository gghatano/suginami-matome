# 杉並区イベントまとめ

杉並区の複数のイベント情報サイトを1日1回クロールし、タイトル・概要・リンクをまとめて表示する静的アグリゲーションサイトです。

- ホスティング:
  - **本番**: Cloudflare Workers（`main` ブランチを自動デプロイ、[`wrangler.jsonc`](wrangler.jsonc)）
  - **テスト**: GitHub Pages（`develop` ブランチを配信、[`.github/workflows/pages.yml`](.github/workflows/pages.yml)）
- データ蓄積: [`data/items.json`](data/items.json)（URL重複排除・追記式）
- 更新: GitHub Actions cron（毎日 09:00 JST）

詳細な仕様は [`spec.md`](spec.md) を参照してください。

## デプロイ（環境）

| 環境 | ホスティング | ブランチ | デプロイ契機 |
|---|---|---|---|
| 本番 | Cloudflare Workers | `main` | `main` への push で自動（日次データ更新のコミット含む） |
| テスト | GitHub Pages | `develop` | `develop` への push、または手動実行 |

開発フロー:

1. 変更は `develop` ブランチで行い、GitHub Pages（テスト）で表示を確認する。
2. 問題なければ `develop` を `main` にマージし、Cloudflare Workers（本番）へ反映する。
3. 日次のデータ更新（`data/items.json`）は `main` に直接コミットされ、本番へ自動反映される。
   テスト環境で最新データを確認したい場合は `main` を `develop` にマージする。

> **セットアップ**: `develop` ブランチが未作成の場合は `git switch -c develop main && git push -u origin develop` で作成する。
> GitHub の `github-pages` 環境で `develop` からのデプロイが許可されていない場合は、
> リポジトリの Settings → Environments → github-pages の Deployment branches に `develop` を追加する。

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

## 児童館カレンダー（`/jidoukan/`）

イベントまとめとは別のページとして、児童館のおたより（PDF）から行事と申込の受付開始日をまとめたカレンダーを [`jidoukan/index.html`](jidoukan/index.html) で配信しています（本番では `https://<ドメイン>/jidoukan/`）。

| 項目 | 内容 |
|---|---|
| 対象の児童館 | [`data/jidoukan/sources.json`](data/jidoukan/sources.json) に1館ずつ追加する（`key` / `name` / `page_url` / `address` / `tel`）。ページ上のPDFのうち、リンク文字列に「おたより」を含むものだけを読む（チラシ等を除外。`pdf_label_keyword` で変更可） |
| 取得 | 区の児童館ページからPDFリンクを拾い、PDFを Claude API（`claude-opus-5-5`）で読み取ってJSON化 |
| キャッシュ | `data/jidoukan/extracted/{key}/{PDF名}.json`。PDFの sha256 が変わらない限り再読み取りしない（APIを呼ぶのは新しい号だけ）。誤読はこのJSONを手で直せば、PDFが差し替わるまで残る |
| 出力 | `data/jidoukan/events.json`（フロントが読む）。日付の形式、対象月の外の日付、休館日との重なりを検証し、`warnings` に残す |
| 更新 | GitHub Actions [`jidoukan.yml`](.github/workflows/jidoukan.yml) が毎週月曜 8:17 JST に実行し、`main` にコミット |
| 必要な設定 | リポジトリのシークレット `ANTHROPIC_API_KEY` |

PDFは漢字のふりがな（ルビ）が本文に混ざり、`pdftotext` などでは日付と時刻が崩れるため、テキスト抽出ではなくPDFをそのままモデルに渡しています。

```bash
pip install requests beautifulsoup4 lxml anthropic
ANTHROPIC_API_KEY=... python scrapers/jidoukan/fetch.py   # 取得・読み取り・出力
python scrapers/jidoukan/fetch.py --no-fetch              # キャッシュから events.json だけ作り直す
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
