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
| 対象の児童館 | [`data/jidoukan/sources.json`](data/jidoukan/sources.json) に1館ずつ追加する（`key` / `name` / `short`（カレンダーに出す短い名前）/ `page_url` / `address` / `tel`）。児童館以外（学童クラブのゆうキッズ等）も同じ形で追加できる。ページ上のPDFのうち、リンク文字列に「おたより」を含むものだけを読む（チラシ等を除外。`pdf_label_keyword` で変更可。文字列か、どれかを含めばよい文字列の配列） |
| 取得 | 区の児童館ページからPDFリンクを拾い、新しい号だけを読み取ってJSON化する。週次の読み取りは Claude のスケジュールしたタスクが行う（手順は [`scrapers/jidoukan/SESSION.md`](scrapers/jidoukan/SESSION.md)、APIキー不要）。Claude API（`claude-opus-5-5`）で読み取る手動実行用の経路も残している |
| キャッシュ | `data/jidoukan/extracted/{key}/{PDF名}.json`。PDFの sha256 が変わらない限り再読み取りしない（APIを呼ぶのは新しい号だけ）。誤読はこのJSONを手で直せば、PDFが差し替わるまで残る |
| 出力 | `data/jidoukan/events.json`（フロントが読む）。日付の形式、対象月の外の日付、休館日との重なりを検証し、`warnings` に残す |
| 更新 | 毎週月曜の朝に Claude のスケジュールしたタスクが実行し、`main` に直接 push する。API経由で読み取る場合は [`jidoukan.yml`](.github/workflows/jidoukan.yml) を手動実行（シークレット `ANTHROPIC_API_KEY` が必要） |

URLパラメータで表示を指定できます（画面で選択を変えるとアドレス欄のURLも変わるので、そのまま共有できます）。パラメータが1つでもあれば、ブラウザに保存した選択より優先し、書かれていない項目は初期値になります。

| パラメータ | 値 | 例 |
|---|---|---|
| `center` | 児童館の `key`（`sources.json`）。複数はカンマ区切り。省略時は全館 | `center=honan` |
| `target` | `kids`（小学生以上）／`baby`（乳幼児親子）。省略時はすべて | `target=baby` |
| `regular` | `1` で毎日・毎週のプログラムも表示 | `regular=1` |
| `month` | 表示する月 | `month=2026-11` |

例：方南児童館の乳幼児向けだけ → `/jidoukan/?center=honan&target=baby`

PDFは漢字のふりがな（ルビ）が本文に混ざり、`pdftotext` などでは日付と時刻が崩れるため、テキスト抽出ではなくPDFをそのままモデルに渡しています。

```bash
pip install requests beautifulsoup4 lxml anthropic
python scrapers/jidoukan/fetch.py --list-new .jidoukan_pdfs  # 未読の号をダウンロードして一覧表示
python scrapers/jidoukan/register.py <center> <url> <sha256> data.json  # 読み取り結果を登録
ANTHROPIC_API_KEY=... python scrapers/jidoukan/fetch.py   # APIで取得・読み取り・出力
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
