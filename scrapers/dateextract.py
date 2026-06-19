"""記事のタイトル・概要から「イベント開催日」を抽出するユーティリティ。

日本語の告知文に頻出する以下の表記からイベント日（ISO形式 YYYY-MM-DD）を抽出する。

- 2026年6月27日 / 2026年6月27日(土)
- 6月27日 / 6月27日(土)          ← 年は基準日から推定
- 2026/6/27, 2026-06-27
- 6月27日〜6月29日 / 6月27日〜29日  ← 期間（日付を展開）

抽出結果は最大件数で打ち切り、誤検出を抑えるため年や月日の妥当性を検証する。
"""

from __future__ import annotations

import re
from datetime import date, timedelta

# 期間表記で展開する最大日数（長すぎる範囲は誤検出の可能性が高いので打ち切る）
MAX_RANGE_DAYS = 31
# 1記事から抽出する日付の最大件数
MAX_DATES = 20

_SEP = r"[〜～~\-－ー–—]"  # 期間表記の区切り（各種ダッシュ・波ダッシュ）

# 2026年6月27日（年あり）
_RE_YMD_JP = re.compile(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日")
# 6月27日〜6月29日（月またぎの期間）
_RE_MD_RANGE_FULL = re.compile(
    r"(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*" + _SEP + r"\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
)
# 6月27日〜29日（同月内の期間）
_RE_MD_RANGE_SAME = re.compile(
    r"(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*" + _SEP + r"\s*(\d{1,2})\s*日"
)
# 6月27日（年なし・単発）
_RE_MD_JP = re.compile(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日")
# 2026/6/27 または 2026-06-27
_RE_YMD_SLASH = re.compile(r"(20\d{2})\s*[/\-]\s*(\d{1,2})\s*[/\-]\s*(\d{1,2})")


def _valid(y: int, m: int, d: int) -> date | None:
    """妥当な日付なら date を返す。範囲外なら None。"""
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _infer_year(month: int, day: int, ref: date) -> date | None:
    """年が省略された月日について、基準日に最も近い年を推定する。"""
    best: date | None = None
    best_diff = None
    for y in (ref.year - 1, ref.year, ref.year + 1):
        cand = _valid(y, month, day)
        if cand is None:
            continue
        diff = abs((cand - ref).days)
        if best_diff is None or diff < best_diff:
            best, best_diff = cand, diff
    return best


def _ref_date(reference: str | None) -> date:
    """基準日文字列（ISO）を date に変換。不正なら今日。"""
    if reference:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", reference)
        if m:
            got = _valid(int(m[1]), int(m[2]), int(m[3]))
            if got:
                return got
    return date.today()


def extract_event_dates(text: str, reference: str | None = None) -> list[str]:
    """テキストからイベント日（ISO日付）を抽出して昇順ユニークで返す。

    reference: 年推定の基準となる日付（通常は published_at / fetched_at）。
    """
    if not text:
        return []
    ref = _ref_date(reference)
    found: set[date] = set()

    # 年あり（年月日 / スラッシュ）
    for mo in _RE_YMD_JP.finditer(text):
        dt = _valid(int(mo[1]), int(mo[2]), int(mo[3]))
        if dt:
            found.add(dt)
    for mo in _RE_YMD_SLASH.finditer(text):
        dt = _valid(int(mo[1]), int(mo[2]), int(mo[3]))
        if dt:
            found.add(dt)

    # 期間（月またぎ）: 6月27日〜7月2日
    consumed: list[tuple[int, int]] = []
    for mo in _RE_MD_RANGE_FULL.finditer(text):
        start = _infer_year(int(mo[1]), int(mo[2]), ref)
        end_md = _valid(start.year, int(mo[3]), int(mo[4])) if start else None
        if start and end_md:
            # 終わりが始まりより前なら翌年（年またぎ）
            end = end_md if end_md >= start else _valid(start.year + 1, int(mo[3]), int(mo[4]))
            _add_range(found, start, end)
            consumed.append(mo.span())

    # 期間（同月内）: 6月27日〜29日
    for mo in _RE_MD_RANGE_SAME.finditer(text):
        start = _infer_year(int(mo[1]), int(mo[2]), ref)
        end = _valid(start.year, int(mo[1]), int(mo[3])) if start else None
        if start and end:
            _add_range(found, start, end)
            consumed.append(mo.span())

    # 単発の月日（既に期間として消費した範囲は二重カウントしないよう、
    # 個別 finditer のスパンが consumed と重なるものはスキップ）
    for mo in _RE_MD_JP.finditer(text):
        if any(s <= mo.start() < e for s, e in consumed):
            continue
        dt = _infer_year(int(mo[1]), int(mo[2]), ref)
        if dt:
            found.add(dt)

    return sorted(d.isoformat() for d in list(found)[:MAX_DATES])


def _add_range(acc: set[date], start: date, end: date | None) -> None:
    if end is None:
        acc.add(start)
        return
    if end < start:
        start, end = end, start
    span = (end - start).days
    if span > MAX_RANGE_DAYS:
        # 異常に長い範囲は端点のみ採用（誤検出の被害を抑える）
        acc.add(start)
        acc.add(end)
        return
    for i in range(span + 1):
        acc.add(start + timedelta(days=i))


def event_dates_for_item(item: dict) -> list[str]:
    """アイテム辞書からタイトル＋概要を使ってイベント日を抽出する。"""
    text = f"{item.get('title', '')}　{item.get('summary', '')}"
    reference = item.get("published_at") or item.get("fetched_at") or ""
    return extract_event_dates(text, reference)
