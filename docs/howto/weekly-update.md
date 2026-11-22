# 定期更新を見る・直す

児童館カレンダーの定期更新（毎週 月・木 8:17）がうまく動いているかを確かめ、止まっていたら直す手順です。しくみは [児童館カレンダーのしくみ](../explanation/jidoukan-pipeline.md) にあります。

## 登場するもの

```mermaid
sequenceDiagram
  participant T as スケジュールしたタスク<br>児童館カレンダー更新（月・木）
  participant S as 専用セッション<br>児童館カレンダー週次更新（専用）
  participant K as 区のサイト
  participant G as GitHub（main）
  T->>S: 月・木 8:17 に依頼を送る
  S->>G: main を最新にして SESSION.md を読む
  S->>K: 各施設のページと PDF を取得
  K-->>S: PDF
  S->>S: 新しい号を読み取り、キャッシュに登録
  S->>G: data/jidoukan/ を push
  G-->>G: 本番と Pages が自動で更新
  S->>S: 結果を会話に報告
```

## 結果を見る

結果は、claude.ai/code の「児童館カレンダー週次更新（専用）」セッションの会話に残ります（スマホへの通知はありません）。毎回、次の内容を報告する決まりです。

- 読み取った号・省略した号
- 申込制の行事の数
- 判断に迷った箇所
- 各施設のページで見つかった PDF のリンク数

GitHub の `main` のコミット履歴に `chore: update jidoukan calendar ...` があれば、更新が入っています。新しい号がない回は、コミットはありません。

## うまく動いていないとき

```mermaid
flowchart TD
  A[カレンダーに新しい号が出ない] --> B{区のページに<br>新しい号は出ている？}
  B -->|まだ出ていない| Z[待つ<br>月末の25日ごろが多い]
  B -->|出ている| C{専用セッションの<br>最新の報告は？}
  C -->|PDF リンク数が 0件の館がある| D[区のページの作りが変わった<br>→ fetch.py の find_pdf_links を直す]
  C -->|push が 403 で拒否された| E[セッションの権限の問題<br>→ 環境と自動処理の「権限」を見る]
  C -->|区のサイトに接続できない| F[ネットワークの設定<br>www.city.suginami.tokyo.jp が許可されているか]
  C -->|報告がない・動いていない| G[スケジュールしたタスクが<br>有効になっているか確かめる]
  C -->|読み取った と報告がある| H{main にコミットはある？}
  H -->|ない| E
  H -->|ある| I[本番のデプロイを確かめる<br>Cloudflare / Pages]
```

### 同じ号が毎回「未読」に出る

読み取った結果をキャッシュに登録していないか、終わった月の号を省略として登録していません。`register.py`（または `--skip-past`）で登録します。手順は [児童館を増やす](add-jidoukan.md) の 3 と 3' と同じです。

### 読み取りが間違っていた

`data/jidoukan/extracted/<施設>/<PDF名>.json` を直してから、`python scrapers/jidoukan/fetch.py --no-fetch` で `events.json` を作り直し、`main` に入れます。PDF が差し替わらない限り、その修正が残ります。

### 手順そのものを変えたい

`scrapers/jidoukan/SESSION.md` を直して、`main` に入れます。専用セッションは毎回これを読み直すので、次の回から反映されます。
