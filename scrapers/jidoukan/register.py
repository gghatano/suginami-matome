"""セッションが読み取ったおたよりの内容を、キャッシュ（data/jidoukan/extracted/）に登録する。

使い方:
    python scrapers/jidoukan/register.py <center_key> <pdf_url> <sha256> <data.json> [--label "リンク文字列"]

data.json は extract.py の SCHEMA と同じ形（year / month / events / closed_days）。
登録前に fetch.py と同じ検証にかけ、警告を表示する（警告があっても登録はする）。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from fetch import cache_path, normalize  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("center")
    ap.add_argument("pdf_url")
    ap.add_argument("sha256")
    ap.add_argument("data_json")
    ap.add_argument("--label", default="")
    ap.add_argument("--method", default="claude-scheduled-session")
    args = ap.parse_args()

    data = json.loads(Path(args.data_json).read_text(encoding="utf-8"))
    for k in ("year", "month", "events", "closed_days"):
        if k not in data:
            print(f"エラー: data.json に {k} がありません", file=sys.stderr)
            return 1
    _, warnings = normalize(data)
    for w in warnings:
        print(f"警告: {w}")

    path = cache_path(args.center, args.pdf_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "pdf_url": args.pdf_url,
        "pdf_label": args.label,
        "sha256": args.sha256,
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": args.method,
        "data": data,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"登録しました: {path}（{len(data['events'])}行事、警告 {len(warnings)}件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
