# ファイルとフォルダ

| パス | 役割 | 誰が変えるか |
|---|---|---|
| `index.html` | まとめサイトの画面（HTML・CSS・JS を1ファイルに同梱） | 開発（PR） |
| `jidoukan/index.html` | 児童館カレンダーの画面（同上） | 開発（PR） |
| `assets/icons/` | まとめサイトの取得元アイコン | 開発（PR） |
| `data/items.json` | まとめサイトの記事データ。最大500件 | 毎日の定期更新（GitHub Actions） |
| `data/jidoukan/sources.json` | 児童館カレンダーの対象施設 | 開発（PR）。施設を足すとき |
| `data/jidoukan/extracted/<施設>/<PDF名>.json` | おたより1号ぶんの読み取り結果（キャッシュ） | 定期更新（専用セッション）。誤りは手で直してよい |
| `data/jidoukan/events.json` | 児童館カレンダーの画面が読むデータ | 定期更新（`fetch.py --no-fetch` が生成）。手で直さない |
| `scrapers/fetch.py` | まとめサイトのデータ更新の入口 | 開発（PR） |
| `scrapers/base.py` | スクレイパーの共通の型（`Item`、`BaseScraper`） | 開発（PR） |
| `scrapers/<取得元>.py` | 取得元ごとのスクレイパー | 開発（PR） |
| `scrapers/dateextract.py` | 記事の文章からイベント開催日を取り出す | 開発（PR） |
| `scrapers/httputil.py` | HTML の取得、og:image の取得 | 開発（PR） |
| `scrapers/jidoukan/fetch.py` | 児童館：PDF の一覧（`--list-new`）、検証、`events.json` の生成（`--no-fetch`）、API 版の読み取り | 開発（PR） |
| `scrapers/jidoukan/register.py` | 児童館：読み取り結果をキャッシュに登録（`--skip-past` で省略） | 開発（PR） |
| `scrapers/jidoukan/extract.py` | 児童館：読み取りのルール（`INSTRUCTIONS`）と形式（`SCHEMA`）、API 版の読み取り | 開発（PR） |
| `scrapers/jidoukan/SESSION.md` | 児童館：定期更新のセッションが従う手順書 | 開発（PR）。`main` に入ると次の回から反映 |
| `.github/workflows/fetch.yml` | 毎日 23:00 の記事集め | 開発（PR） |
| `.github/workflows/pages.yml` | GitHub Pages の公開 | 開発（PR）。早めに `main` へ |
| `.github/workflows/jidoukan.yml` | 児童館の API 版の読み取り（手動のみ） | 開発（PR） |
| `wrangler.jsonc` | Cloudflare Workers の設定（リポジトリ直下をそのまま配信） | 開発（PR） |
| `.assetsignore` | Cloudflare に出さないファイル（`docs/`、`CLAUDE.md`、`.claude/`） | 開発（PR） |
| `docs/` | このドキュメント（Markdown が正本）と閲覧ページ `docs/index.html` | 開発（PR） |
| `docs/slides.md`・`docs/slides.html` | 5分でわかるスライドの原本と、その表示ページ | 開発（PR） |
| `CLAUDE.md` | Claude Code の入口 | 開発（PR） |
| `.claude/settings.json` | Claude Code のプロジェクト設定（応答言語を日本語に固定） | 開発（PR） |
| `README.md` | リポジトリの概要 | 開発（PR） |
| `spec.md` | 最初の仕様書（古い記述あり） | 原則そのまま |
| `requirements.txt` | Python の依存ライブラリ | 開発（PR） |
