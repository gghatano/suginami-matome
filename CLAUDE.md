# CLAUDE.md

杉並区イベントまとめ（`gghatano/suginami-matome`）。静的サイト2つ（トップの「杉並区イベントまとめ」と `/jidoukan/` の「児童館カレンダー」）と、そのデータを作るスクレイパーのリポジトリ。

**作業の前に `docs/` を読むこと。** 入口は [`docs/README.md`](docs/README.md)。ドキュメントは Diátaxis の4種類（チュートリアル・ハウツー・リファレンス・解説）に分けてある。

- よくある作業の手順：[`docs/howto/`](docs/howto/)（児童館を増やす、取得元を増やす、画面を変える、本番に出す、定期更新を見る・直す、ドキュメントを書く）
- 形式・コマンド・環境の一覧：[`docs/reference/`](docs/reference/)
- 仕組みと理由：[`docs/explanation/`](docs/explanation/)（全体の構成、児童館カレンダーのしくみ、画面づくりの原則、これまでの判断と失敗）
- 言葉の意味：[`docs/glossary.md`](docs/glossary.md)
- 児童館カレンダーの定期更新の手順：[`scrapers/jidoukan/SESSION.md`](scrapers/jidoukan/SESSION.md)

## 守ること

- **ブランチの流れ**：作業ブランチを `develop` から切り、PR は `develop` に向ける。`develop` → `main` で本番に出す。`develop` は消さない
- **データは `main` に直接入る**：`data/items.json`（毎日 23:00 JST、GitHub Actions）と `data/jidoukan/`（月・木、Claude の専用セッション）。コードの変更で `data/` を書き換えない（初期データの登録など意図したものを除く）
- **レイアウトがずれない**：件数や表示の有無で長さが変わる要素は、場所を先に確保する（[`docs/explanation/ui-principles.md`](docs/explanation/ui-principles.md) の 1）
- **ドキュメントも一緒に直す**：仕様を変えたら、同じ PR で `docs/` を更新する。新しいドキュメントを足したら `docs/README.md` の表と `docs/index.html` の `DOCS` に追加する（書き方は [`docs/howto/write-docs.md`](docs/howto/write-docs.md)）
- **判断や失敗は記録する**：設計を決めたり失敗から学んだりしたら [`docs/explanation/history.md`](docs/explanation/history.md) の先頭に足す
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
