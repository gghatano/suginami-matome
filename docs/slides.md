# 5分でわかる 杉並区イベントまとめ

開発に加わる人が最初に知っておくことだけ

<small>← → キーかクリックで進む。詳しくは各スライドのリンク先へ</small>

---

## 何を作っているか

- **杉並区イベントまとめ**（トップ）：区内7か所の情報を1つに
- **児童館カレンダー**（`/jidoukan/`）：おたより PDF の行事と申込開始日
- サーバーで動くプログラムは**ない**。JSON を定期的に作り直し、ページが読むだけ

→ [全体の構成](explanation/architecture.md)

---

## データは自動で `main` に入る

| データ | いつ | だれが |
|---|---|---|
| `data/items.json` | 毎日 23:00 | GitHub Actions |
| `data/jidoukan/` | 月・木の朝 | Claude の専用セッション |

- コードの変更で `data/` を書き換えない
- 止まったら → [定期更新を見る・直す](howto/weekly-update.md)

---

## ブランチの流れ

```mermaid
flowchart LR
  W[作業ブランチ] -->|PR| D[develop] -->|PR| M[main = 本番]
```

- 作業ブランチは `develop` から切り、PR は `develop` に向ける
- **`develop` は消さない**。`develop` → `main` のマージで自動削除されないか注意

→ [本番に出す](howto/release.md)

---

## 3つの公開先

| 公開先 | 中身 | 用途 |
|---|---|---|
| 本番（Cloudflare） | `main` | 利用者が見る |
| プレビュー | PR のブランチ | PR ごとの確認 |
| GitHub Pages | `develop` ＋ `main` のデータ ＋ ドキュメント | 本番前の確認 |

→ [環境と自動処理](reference/environments.md)

---

## 守ること

1. **画面がずれない**：件数や表示の有無で長さが変わるものは、場所を先に確保する
2. **ドキュメントも同じ PR で直す**
3. **判断と失敗は記録する**：[これまでの判断と失敗](explanation/history.md) の先頭へ
4. **画面を変えたら**：PC とスマホ、ライトとダークで確かめる

---

## よくある作業は手順書がある

| やりたいこと | 手順書 |
|---|---|
| 児童館を増やす | [児童館を増やす](howto/add-jidoukan.md) |
| 情報源を増やす | [取得元を増やす](howto/add-event-source.md) |
| 画面を変える | [画面を変える](howto/change-screen.md) |
| 本番に出す | [本番に出す](howto/release.md) |

---

## ドキュメントの決まり

- **原本は Markdown**（`docs/*.md`）。人も Claude も同じものを読む
- HTML（このスライドと閲覧ページ）は Markdown を読んで表示するだけ。**HTML に本文を書かない**
- このスライドの原本も `docs/slides.md`

→ [ドキュメントを書く](howto/write-docs.md)

---

## 次に読む

1. [用語集](glossary.md)：ブランチ・PR・マージ
2. [全体の構成](explanation/architecture.md)
3. [はじめての変更](tutorial/first-change.md)：手元で動かして本番に出すまで

[ドキュメントの入口へ](README.md)
