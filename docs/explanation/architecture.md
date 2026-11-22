# 全体の構成

この文書では、このリポジトリが「何を」「どうやって」動かしているかを、図を中心に説明します。細かい形式は [リファレンス](../README.md#リファレンス正確な仕様の一覧) にあります。

## 2つのサイト

| サイト | アドレス | 見せているもの | 読み込むデータ |
|---|---|---|---|
| 杉並区イベントまとめ | `/`（`index.html`） | 区内のイベント情報サイトから毎日集めた記事の一覧とカレンダー | `data/items.json` |
| 児童館カレンダー | `/jidoukan/`（`jidoukan/index.html`） | 児童館などのおたより（PDF）から読み取った行事と、申込の受付開始日 | `data/jidoukan/events.json` |

どちらも「静的サイト」です。サーバー側でプログラムは動いていません。ページを開くと、ブラウザの中の JavaScript がデータ（JSON）を読み込み、画面を組み立てます。

```mermaid
sequenceDiagram
  participant 利用者のブラウザ
  participant サイト as 配信サーバー（Cloudflare / Pages）
  利用者のブラウザ->>サイト: ページを開く（index.html）
  サイト-->>利用者のブラウザ: HTML・CSS・JavaScript
  利用者のブラウザ->>サイト: データを読む（data/items.json など）
  サイト-->>利用者のブラウザ: JSON
  利用者のブラウザ->>利用者のブラウザ: JavaScript が画面を組み立てる
```

## データができるまで

データは2つの別々の仕組みで作られ、どちらも最後は `main` ブランチに入ります。

```mermaid
flowchart TD
  subgraph まとめサイトの記事
    A1[区内のイベント情報サイト 7か所] --> A2[GitHub Actions が毎日 23:00 に<br>scrapers/fetch.py を実行]
    A2 --> A3[(data/items.json)]
  end
  subgraph 児童館カレンダーの行事
    B1[区の施設ページのおたより PDF] --> B2[スケジュールしたタスクが<br>月・木 8:17 に専用セッションへ依頼]
    B2 --> B3[Claude が新しい号を目で読み取る<br>scrapers/jidoukan/]
    B3 --> B4[(data/jidoukan/events.json)]
  end
  A3 --> M[main ブランチに直接コミット]
  B4 --> M
  M --> P1[本番サイト（Cloudflare）が自動で更新]
  M --> P2[GitHub Pages も自動で更新]
```

児童館カレンダーの読み取りの詳しい流れは [児童館カレンダーのしくみ](jidoukan-pipeline.md) にあります。

## コードの変更が本番に届くまで

データとは違い、プログラム（HTML・Python など）の変更は、必ず確認を2回挟んでから本番に出ます。

```mermaid
flowchart TD
  S[develop から作業ブランチを切る] --> E[変更してコミット・push]
  E --> PR1[develop に向けて PR を作る]
  PR1 --> C1{プレビュー URL で確認<br>Cloudflare が PR ごとに作る}
  C1 -->|直す| E
  C1 -->|OK| M1[develop にマージ]
  M1 --> C2{GitHub Pages で確認<br>develop のコード + main の最新データ}
  C2 -->|直す| S
  C2 -->|OK| PR2[develop → main の PR を作ってマージ]
  PR2 --> L[本番に反映]
```

手順は [はじめての変更](../tutorial/first-change.md) と [本番に出す](../howto/release.md) で、実際に手を動かしながら説明しています。

## 3つの公開先

| 公開先 | 中身 | 何に使うか |
|---|---|---|
| 本番（Cloudflare Workers） | `main` | 利用者が見るサイト |
| プレビュー（Cloudflare Workers） | PR のブランチ | PR ごとの見た目の確認 |
| 開発用（GitHub Pages） | `develop` のコード + `main` の最新データ + 開発者ドキュメント | develop に入った変更の確認、このドキュメントを読む |

Pages が「`develop` のコード」に「`main` のデータ」を重ねているのは、データの定期更新が `main` にしか入らないためです。こうしておくと、`develop` のデータが古くても、Pages では最新のデータで確認できます。

```mermaid
flowchart TD
  D[develop ブランチ<br>HTML・Python・ドキュメント] --> W[pages.yml が組み立てる]
  M[main ブランチの data/<br>毎日更新される最新データ] --> W
  W --> G[GitHub Pages]
```

開発者ドキュメントと `CLAUDE.md` は、`.assetsignore` で Cloudflare に出さないようにしています。本番とプレビューには出ず、Pages でだけ読めます。

## フォルダの全体像

```mermaid
flowchart TD
  R[リポジトリ] --> I[index.html<br>まとめサイトの画面]
  R --> J[jidoukan/index.html<br>児童館カレンダーの画面]
  R --> DA[data/<br>データ]
  DA --> DI[items.json]
  DA --> DJ[jidoukan/<br>sources.json・extracted/・events.json]
  R --> SC[scrapers/<br>データを作るプログラム]
  SC --> SCJ[jidoukan/<br>おたよりの取得・登録]
  R --> GH[.github/workflows/<br>自動処理の設定]
  R --> DO[docs/<br>このドキュメント]
  R --> CL[CLAUDE.md<br>Claude 向けの入口]
```

ファイルごとの説明は [ファイルとフォルダ](../reference/files.md) にあります。
