# コマンド

## 準備

```bash
git clone https://github.com/gghatano/suginami-matome.git
cd suginami-matome
pip install -r requirements.txt
```

## 手元で表示する

| コマンド | すること |
|---|---|
| `python -m http.server 8000` | リポジトリ直下を配信する。`http://localhost:8000/`（まとめ）、`/jidoukan/`（児童館）、`/docs/`（ドキュメント） |

## まとめサイト

| コマンド | すること |
|---|---|
| `python scrapers/fetch.py` | 全取得元を読みに行き、`data/items.json` に新しい記事を足す。試しただけなら `git checkout -- data/items.json` で戻す |

## 児童館カレンダー

| コマンド | すること |
|---|---|
| `python scrapers/jidoukan/fetch.py --list-new <フォルダ>` | 未読の号の PDF をフォルダにダウンロードし、一覧を JSON で出す。各項目に `center`、`url`、`label`、`sha256`、`pdf_path`、`likely_past`、`label_month` |
| `python scrapers/jidoukan/register.py <key> <url> <sha256> <data.json> --label "<リンク文字列>"` | 読み取った結果をキャッシュに登録する。`--method manual` で人が登録したことを記録 |
| `python scrapers/jidoukan/register.py <key> <url> <sha256> --skip-past YYYY-MM --label "..."` | 終わった月の号を、読まずに省略済みとして登録する |
| `python scrapers/jidoukan/fetch.py --no-fetch` | キャッシュ全体から `data/jidoukan/events.json` を作り直す。警告も出す |
| `ANTHROPIC_API_KEY=... python scrapers/jidoukan/fetch.py` | API で取得・読み取り・出力までを一度に行う（手動用） |
| `pdftoppm -r 120 -png <pdf> <名前>` | PDF のページを画像にする（読み取り用）。細かい日付は `-r 220` |
| `pdftoppm -r 60 -f 1 -l 1 -png <pdf> <名前>` | 1ページ目だけを小さく画像にする（表紙の年月の確認用） |

## Git

| コマンド | すること |
|---|---|
| `git checkout develop && git pull` | 最新の `develop` に切り替える |
| `git checkout -b <ブランチ名>` | 作業ブランチを切る |
| `git add <ファイル> && git commit -m "<説明>"` | 変更を記録する |
| `git push -u origin <ブランチ名>` | GitHub に送る |
