# 開発者ドキュメント

杉並区イベントまとめ（`gghatano/suginami-matome`）の開発者向けドキュメントです。
人と Claude の両方が読む前提で書いています。Markdown がそのまま正本です。HTML 版（`docs/index.html`）は同じ Markdown をブラウザで整形して表示しているだけなので、編集するのはいつも Markdown です。

- HTML 版：GitHub Pages の https://gghatano.github.io/suginami-matome/docs/
- Claude 向けの入口：リポジトリ直下の [`CLAUDE.md`](../CLAUDE.md)（Claude Code がセッション開始時に自動で読む）

## 何がどこに書いてあるか

| ドキュメント | 内容 | 読むとき |
|---|---|---|
| [architecture.md](architecture.md) | 全体の構成、2つのサイト、データの流れ、ホスティング | 最初に |
| [events-aggregator.md](events-aggregator.md) | 杉並区イベントまとめ（トップページ）：スクレイパー、`items.json`、画面 | まとめサイトを触るとき |
| [jidoukan.md](jidoukan.md) | 児童館カレンダー：おたよりPDFの取得・読み取り、`events.json`、画面、施設の追加手順 | 児童館カレンダーを触るとき |
| [operations.md](operations.md) | 環境（本番・Pages・プレビュー）、開発の流れ、定期更新、権限、困ったとき | 運用・デプロイ・定期実行まわり |
| [ui-guidelines.md](ui-guidelines.md) | 画面づくりの決まりごと（レイアウトがずれない、色、幅の区切り、文言） | 画面を変えるとき |

既存の [`spec.md`](../spec.md) はまとめサイトの最初の仕様書です。データスキーマの細部はそちらが詳しい一方、ホスティングや更新時刻など古くなった記述もあります。食い違ったときは、このドキュメントとコードを正とします。

## ドキュメントの書き方

- 1ファイル1テーマ。見出しで話題を分け、表と箇条書きを使って拾い読みできるようにする
- コードやファイルはリポジトリからの相対パスで書く（例：`scrapers/jidoukan/fetch.py`）
- 「なぜそうしたか」を残す。過去に起きた失敗（ずれ、取りこぼし、権限）は、同じ失敗を防ぐための一番の材料になる
- 仕様を変えたら、同じ PR でドキュメントも直す
- 図は Mermaid（` ```mermaid `）で書く。HTML 版では図として表示され、Claude はテキストとして読める
- 新しいファイルを足したら、この表と `docs/index.html` の目次（`DOCS` 配列）に追加する
