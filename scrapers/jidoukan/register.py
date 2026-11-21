"""セッションが読み取ったおたよりの内容を、キャッシュ（data/jidoukan/extracted/）に登録する。

使い方:
    python scrapers/jidoukan/register.py <center_key> <pdf_url> <sha256> <data.json> [--label "リンク文字列"]
    python scrapers/jidoukan/register.py <center_key> <pdf_url> <sha256> --skip-past 2026-10 [--label "リンク文字列"]

--skip-past は、対象の月が終わった号を読み取らずに「省略済み」として登録する。
キャッシュに sha256 が残るので、次回から --list-new に出てこない。カレンダーにも出ない。

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
    ap.add_argument("data_json", nargs="?")
    ap.add_argument("--skip-past", metavar="YYYY-MM", help="対象の月が終わった号として、読み取らずに登録する")
    ap.add_argument("--label", default="")
    ap.add_argument("--method", default="claude-scheduled-session")
    args = ap.parse_args()

    skipped = ""
    if args.skip_past:
        try:
            y, m = (int(x) for x in args.skip_past.split("-"))
            assert 1 <= m <= 12
        except Exception:  # noqa: BLE001
            print("エラー: --skip-past は YYYY-MM の形で指定してください", file=sys.stderr)
            return 1
        data = {"year": y, "month": m, "events": [], "closed_days": []}
        skipped = "対象の月が終わっているため読み取りを省略"
        args.method = "skipped-past"
    elif args.data_json:
        data = json.loads(Path(args.data_json).read_text(encoding="utf-8"))
    else:
        print("エラー: data.json か --skip-past のどちらかを指定してください", file=sys.stderr)
        return 1
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
        **({"skipped": skipped} if skipped else {}),
        "data": data,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"登録しました: {path}（{len(data['events'])}行事、警告 {len(warnings)}件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
