"""児童館カレンダーのエントリポイント。

1. data/jidoukan/sources.json に並べた各児童館のページから、おたよりPDFのリンクを拾う
2. PDFをダウンロードし、まだ読み取っていない（または中身が変わった）ものだけ Claude で読み取る
   読み取り結果は data/jidoukan/extracted/{児童館}/{PDF名}.json に保存する（キャッシュ）
3. キャッシュ全体を検証・整形して data/jidoukan/events.json を作る（フロントが読む）

キャッシュは PDF の sha256 で照合するので、PDFが差し替わらない限り再読み取りしない。
キャッシュの JSON を手で直した場合も、PDFが変わらない限りその修正が残る。
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # scrapers/（base.py）
sys.path.insert(0, str(HERE))

from base import USER_AGENT  # noqa: E402

ROOT = HERE.parent.parent
DATA_DIR = ROOT / "data" / "jidoukan"
SOURCES_PATH = DATA_DIR / "sources.json"
CACHE_DIR = DATA_DIR / "extracted"
OUT_PATH = DATA_DIR / "events.json"

TIMEOUT = 30
SLEEP = 2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jidoukan")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


def http_get(url: str) -> requests.Response:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp


def find_pdf_links(page_url: str, keyword: "str | list[str]" = "おたより") -> list[dict]:
    """児童館ページから、リンク文字列に keyword（複数ならどれか）を含む PDF リンクを拾う。

    同じページに中高生向けチラシなど、おたより以外のPDFが置かれていることがあるため、
    リンク文字列で絞る。ファイル名は号と一致しないことがある（11月号が ...2610.pdf 等）ので使わない。
    """
    resp = http_get(page_url)
    resp.encoding = resp.apparent_encoding if resp.encoding in (None, "ISO-8859-1") else resp.encoding
    soup = BeautifulSoup(resp.text, "lxml")
    seen, out = set(), []
    for a in soup.select('a[href$=".pdf"], a[href$=".PDF"]'):
        url = urljoin(page_url, a["href"])
        label = a.get_text(" ", strip=True)
        keywords = [keyword] if isinstance(keyword, str) else list(keyword)
        if url in seen or (keywords and not any(k in label for k in keywords if k)):
            continue
        seen.add(url)
        out.append({"url": url, "label": label})
    return out


# ---------------------------------------------------------------- 検証・整形

def _valid_date(s: str) -> bool:
    if not isinstance(s, str) or not DATE_RE.match(s):
        return False
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def _norm_time(s: str) -> str:
    """'4:00' のような午後の12時間表記が残っていたら 16:00 に直す。児童館は 9時前に行事がない前提。"""
    m = TIME_RE.match(s or "")
    if not m:
        return ""
    h, mi = int(m.group(1)), int(m.group(2))
    if h < 9:
        h += 12
    if h > 23 or mi > 59:
        return ""
    return f"{h:02d}:{mi:02d}"


def normalize(data: dict) -> tuple[dict, list[str]]:
    """読み取り結果を検証する。おかしな値は落とし、警告を返す。"""
    warnings: list[str] = []
    year, month = data.get("year"), data.get("month")
    prefix = f"{year:04d}-{month:02d}-" if isinstance(year, int) and isinstance(month, int) else None
    if prefix is None:
        warnings.append("対象年月が読み取れていません")

    closed = []
    for c in data.get("closed_days", []):
        if _valid_date(c.get("date", "")):
            closed.append({"date": c["date"], "reason": c.get("reason", "")})
        else:
            warnings.append(f"休館日の日付が不正: {c}")
    closed_dates = {c["date"] for c in closed}

    events = []
    for ev in data.get("events", []):
        sessions = []
        for s in ev.get("sessions", []):
            d = s.get("date", "")
            if not _valid_date(d):
                warnings.append(f"「{ev.get('title')}」の日付が不正: {d}")
                continue
            if prefix and not d.startswith(prefix):
                warnings.append(f"「{ev.get('title')}」の開催日 {d} が対象月の外です（翌月の予告なら正常。残します）")
            if d in closed_dates:
                warnings.append(f"「{ev.get('title')}」の開催日 {d} が休館日と重なっています（落とします）")
                continue
            sessions.append({"date": d, "start": _norm_time(s.get("start", "")), "end": _norm_time(s.get("end", ""))})
        if not sessions:
            warnings.append(f"「{ev.get('title')}」に有効な開催日がありません（落とします）")
            continue
        sessions.sort(key=lambda x: (x["date"], x["start"]))
        e = dict(ev)
        e["sessions"] = sessions
        for k in ("application_start", "application_end"):
            if e.get(k) and not _valid_date(e[k]):
                warnings.append(f"「{ev.get('title')}」の{k}が不正: {e[k]}")
                e[k] = ""
        if e.get("requires_application") and not e.get("application_start"):
            warnings.append(f"「{ev.get('title')}」は申込制ですが受付開始日が読み取れていません")
        events.append(e)

    return {"year": year, "month": month, "events": events, "closed_days": closed}, warnings


# ---------------------------------------------------------------- メイン

def cache_path(center_key: str, pdf_url: str) -> Path:
    return CACHE_DIR / center_key / (Path(pdf_url).stem + ".json")


def process_center(center: dict, client) -> tuple[int, int]:
    """1つの児童館を処理する。(新しく読み取った件数, 読み取れなかった件数) を返す。"""
    key = center["key"]
    extracted = failed = 0
    try:
        links = find_pdf_links(center["page_url"], center.get("pdf_label_keyword", "おたより"))
    except Exception as e:  # noqa: BLE001
        logger.error("[%s] ページ取得失敗: %s", key, e)
        return 0, 1
    logger.info("[%s] PDF %d件: %s", key, len(links), ", ".join(l["label"] for l in links))

    for link in links:
        time.sleep(SLEEP)
        try:
            pdf = http_get(link["url"]).content
        except Exception as e:  # noqa: BLE001
            logger.error("[%s] PDF取得失敗 %s: %s", key, link["url"], e)
            failed += 1
            continue
        sha = hashlib.sha256(pdf).hexdigest()
        path = cache_path(key, link["url"])
        if path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("sha256") == sha:
                logger.info("[%s] 変更なし: %s", key, path.name)
                continue
            logger.info("[%s] PDFが差し替わったので読み直します: %s", key, path.name)

        if client is None:
            logger.error("[%s] ANTHROPIC_API_KEY がないため読み取れません: %s", key, link["url"])
            failed += 1
            continue
        try:
            from extract import extract_newsletter, MODEL
            data = extract_newsletter(client, pdf)
        except Exception as e:  # noqa: BLE001
            logger.error("[%s] 読み取り失敗 %s: %s", key, link["url"], e)
            failed += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "pdf_url": link["url"],
            "pdf_label": link["label"],
            "sha256": sha,
            "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "method": MODEL,
            "data": data,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        extracted += 1
        logger.info("[%s] 読み取り保存: %s（%d行事）", key, path.name, len(data.get("events", [])))
    return extracted, failed


def build_output(centers: list[dict]) -> dict:
    """キャッシュ全体から events.json を組み立てる。"""
    out_events, out_months, all_warnings = [], [], []
    for center in centers:
        key = center["key"]
        for path in sorted((CACHE_DIR / key).glob("*.json")):
            cached = json.loads(path.read_text(encoding="utf-8"))
            data, warnings = normalize(cached["data"])
            for w in warnings:
                logger.warning("[%s/%s] %s", key, path.name, w)
            all_warnings += [f"{center['name']} {path.stem}: {w}" for w in warnings]
            out_months.append({
                "center": key,
                "year": data["year"],
                "month": data["month"],
                "pdf_url": cached["pdf_url"],
                "pdf_label": cached.get("pdf_label", ""),
                "method": cached.get("method", ""),
                "extracted_at": cached.get("extracted_at", ""),
                "closed_days": data["closed_days"],
            })
            for i, ev in enumerate(data["events"]):
                ev = dict(ev)
                ev["id"] = f"{key}-{data['year']}{data['month']:02d}-{i:02d}"
                ev["center"] = key
                ev["pdf_url"] = cached["pdf_url"]
                out_events.append(ev)
    out_months.sort(key=lambda m: (m["year"] or 0, m["month"] or 0, m["center"]))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "centers": centers,
        "months": out_months,
        "events": out_events,
        "warnings": all_warnings,
    }


def list_new(centers: list[dict], pdf_dir: Path) -> list[dict]:
    """まだ読み取っていない（または差し替わった）PDFをダウンロードし、一覧を返す。

    Claude のスケジュール実行（APIキーなし）で使う。読み取りはセッション側が行い、
    結果は register.py でキャッシュに登録する。
    """
    pdf_dir.mkdir(parents=True, exist_ok=True)
    todo = []
    for center in centers:
        key = center["key"]
        try:
            links = find_pdf_links(center["page_url"], center.get("pdf_label_keyword", "おたより"))
        except Exception as e:  # noqa: BLE001
            logger.error("[%s] ページ取得失敗: %s", key, e)
            todo.append({"center": key, "error": f"ページ取得失敗: {e}"})
            continue
        for link in links:
            time.sleep(SLEEP)
            try:
                pdf = http_get(link["url"]).content
            except Exception as e:  # noqa: BLE001
                todo.append({"center": key, "url": link["url"], "error": f"PDF取得失敗: {e}"})
                continue
            sha = hashlib.sha256(pdf).hexdigest()
            path = cache_path(key, link["url"])
            if path.exists() and json.loads(path.read_text(encoding="utf-8")).get("sha256") == sha:
                continue
            local = pdf_dir / f"{key}__{Path(link['url']).name}"
            local.write_bytes(pdf)
            todo.append({
                "center": key, "center_name": center["name"], "url": link["url"], "label": link["label"],
                "sha256": sha, "pdf_path": str(local), "cache_path": str(path.relative_to(ROOT)),
                "replaces_existing": path.exists(),
            })
    return todo


def main() -> int:
    centers = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    if "--list-new" in sys.argv:
        i = sys.argv.index("--list-new")
        pdf_dir = Path(sys.argv[i + 1]) if len(sys.argv) > i + 1 else ROOT / ".jidoukan_pdfs"
        print(json.dumps(list_new(centers, pdf_dir), ensure_ascii=False, indent=2))
        return 0
    client = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic()
    else:
        logger.warning("ANTHROPIC_API_KEY が未設定です。読み取り済みのキャッシュだけで出力を作ります。")

    total_new = total_failed = 0
    if "--no-fetch" not in sys.argv:
        for center in centers:
            n, f = process_center(center, client)
            total_new += n
            total_failed += f

    out = build_output(centers)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logger.info("events.json を出力: %d行事 / %d号分（新規読み取り %d、失敗 %d）",
                len(out["events"]), len(out["months"]), total_new, total_failed)
    # 失敗があれば Actions を赤くして気づけるようにする（出力自体は書き出し済み）
    return 1 if total_failed else 0


if __name__ == "__main__":
    sys.exit(main())
