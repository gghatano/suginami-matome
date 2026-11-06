# 児童館カレンダーの週次更新手順（Claude のスケジュール実行用）

APIキーを使わず、スケジュールで起動した Claude のセッションがおたよりPDFを読み取ってデータを更新する手順。
リポジトリの持ち主の判断により、**結果は `main` に直接 push してよい**（PRは作らない）。

## 手順

1. 最新の `main` を取得する（`git fetch origin main && git checkout main && git pull origin main`）。
2. 新しい号を一覧にする。
   ```bash
   pip install -q requests beautifulsoup4 lxml
   python scrapers/jidoukan/fetch.py --list-new .jidoukan_pdfs
   ```
   出力は JSON 配列。空 `[]` なら新しい号はないので、何もコミットせずに終了する。
   `error` を持つ要素は取得に失敗したもの。最後の報告に含める。
3. 一覧の各PDF（`pdf_path`）を読む。ページを画像にして目で読むのが確実（`pdftoppm -r 120 -png <pdf> <prefix>` → 画像を読む）。
   細かい日付は `-r 220` で拡大するか、`pdftotext -layout` の出力と照らし合わせる。
   - 読み取りのルールと、返すJSONの形は [`extract.py`](extract.py) の `INSTRUCTIONS` と `SCHEMA` に従う。
   - 原本の中で日付が食い違っていたら、曜日やほかの行事との整合から正しい方を選び、その判断を該当行事の `notes` に1行で残す。
4. 読み取った内容をJSONファイルに書き、キャッシュに登録する。
   ```bash
   python scrapers/jidoukan/register.py <center> <url> <sha256> <data.json> --label "<label>"
   ```
   警告が出たら内容を見直す。直せるものは直して登録し直す。
5. `python scrapers/jidoukan/fetch.py --no-fetch` で `data/jidoukan/events.json` を作り直す。
6. `data/jidoukan/` だけをコミットして `main` に push する。
   コミットメッセージは `chore: update jidoukan calendar YYYY-MM-DD（<館名> <月>月号）`。
   `.jidoukan_pdfs/` と画像はコミットしない。
7. 最後に、読み取った号、申込制の行事の数、判断に迷った箇所（あれば）を短く報告する。

## してはいけないこと

- `data/jidoukan/` 以外のファイルを変更しない。
- 読み取れなかった値を推測で埋めない（空文字にする）。
- キャッシュ済みの号（`--list-new` に出てこない号）を読み直さない。
