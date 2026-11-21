# CLAUDE.md

杉並区イベントまとめ（`gghatano/suginami-matome`）。静的サイト2つ（トップの「杉並区イベントまとめ」と `/jidoukan/` の「児童館カレンダー」）と、そのデータを作るスクレイパーのリポジトリ。

**作業の前に `docs/` を読むこと。** 何がどこにあるかは [`docs/README.md`](docs/README.md) にまとめてある。

- 全体の構成とデータの流れ：[`docs/architecture.md`](docs/architecture.md)
- まとめサイト：[`docs/events-aggregator.md`](docs/events-aggregator.md)
- 児童館カレンダー：[`docs/jidoukan.md`](docs/jidoukan.md)（定期更新の手順は [`scrapers/jidoukan/SESSION.md`](scrapers/jidoukan/SESSION.md)）
- 環境・開発の流れ・定期実行・権限：[`docs/operations.md`](docs/operations.md)
- 画面づくりの決まりごと：[`docs/ui-guidelines.md`](docs/ui-guidelines.md)

## 守ること

- **ブランチの流れ**：作業ブランチを `develop` から切り、PR は `develop` に向ける。`develop` → `main` で本番に出す。`develop` は消さない
- **データは `main` に直接入る**：`data/items.json`（毎日 23:00 JST、GitHub Actions）と `data/jidoukan/`（月・木、Claude の専用セッション）。コードの変更で `data/` を書き換えない（初期データの登録など意図したものを除く）
- **レイアウトがずれない**：件数や表示の有無で長さが変わる要素は、場所を先に確保する（[`docs/ui-guidelines.md`](docs/ui-guidelines.md) の 1）
- **ドキュメントも一緒に直す**：仕様を変えたら、同じ PR で `docs/` を更新する。新しいドキュメントを足したら `docs/README.md` の表と `docs/index.html` の `DOCS` に追加する
- **ユーザーへの返答は日本語**
- 画面を変えたら、PC（1280×800）とスマホ（iPhone 相当）、ライトとダークで確かめる（ローカルで `python -m http.server` して Playwright）

## よく使うコマンド

```bash
pip install -r requirements.txt
python scrapers/fetch.py                          # まとめサイトのデータ更新
python scrapers/jidoukan/fetch.py --list-new .jidoukan_pdfs   # 児童館：未読の号を一覧
python scrapers/jidoukan/fetch.py --no-fetch      # 児童館：events.json を作り直す
python -m http.server 8000                        # http://localhost:8000/ と /jidoukan/ と /docs/
```
