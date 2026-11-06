"""児童館おたよりPDFから行事を構造化データとして読み取る（Claude API）。

おたよりPDFはふりがな（ルビ）が本文に混ざり、段組みも自由なため、
pdftotext 等のテキスト抽出では日付と時刻が崩れる。そこでPDFをそのまま
Claude に渡し、JSONスキーマに沿った形で行事を返させる。
"""

from __future__ import annotations

import base64
import json
import logging

import anthropic

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5-5"

# 返してほしいJSONの形（structured outputs で強制する）
SCHEMA: dict = {
    "type": "object",
    "properties": {
        "year": {"type": "integer", "description": "おたよりの対象年（西暦）"},
        "month": {"type": "integer", "description": "おたよりの対象月（1〜12）"},
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "subtitle": {"type": "string", "description": "事業名などの補足。なければ空文字"},
                    "audience": {"type": "string", "enum": ["kids", "baby", "all"]},
                    "regular": {
                        "type": "boolean",
                        "description": "毎週・毎月の定例プログラムなら true、その月だけの特別行事なら false",
                    },
                    "sessions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string", "description": "YYYY-MM-DD"},
                                "start": {"type": "string", "description": "HH:MM（24時間表記）。不明なら空文字"},
                                "end": {"type": "string", "description": "HH:MM（24時間表記）。不明なら空文字"},
                            },
                            "required": ["date", "start", "end"],
                            "additionalProperties": False,
                        },
                    },
                    "place": {"type": "string"},
                    "target": {"type": "string", "description": "対象（例: 1年生〜、0〜3歳児の親子）"},
                    "capacity": {"type": "string", "description": "定員や参加条件（例: 先着25人、申込不要）。なければ空文字"},
                    "requires_application": {"type": "boolean"},
                    "application_start": {"type": "string", "description": "申込受付開始日 YYYY-MM-DD。申込不要なら空文字"},
                    "application_end": {"type": "string", "description": "申込締切日 YYYY-MM-DD。記載がなければ空文字"},
                    "application_method": {"type": "string", "description": "申込方法。なければ空文字"},
                    "notes": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title", "subtitle", "audience", "regular", "sessions", "place", "target",
                    "capacity", "requires_application", "application_start", "application_end",
                    "application_method", "notes",
                ],
                "additionalProperties": False,
            },
        },
        "closed_days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "reason": {"type": "string"},
                },
                "required": ["date", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["year", "month", "events", "closed_days"],
    "additionalProperties": False,
}

INSTRUCTIONS = """\
これは杉並区立児童館が毎月発行する「おたより」のPDFです。親が「いつ・どの行事があり、いつ申込が始まるか」をカレンダーで確認するためのデータを作ります。PDFに書かれている行事をすべて、指定のJSONスキーマで返してください。

読み取りのルール:
- 漢字の上の小さなふりがな（ルビ）は無視し、本文だけを読む。
- 日付は YYYY-MM-DD にする。年と月はおたよりの見出し（例: 2026 11月）から決める。「7日（土）〜」のように月が省略されていれば、おたよりの対象月とみなす。申込受付やアンケートは前月の日付のこともあるので、「10月22日」のように月が書いてあればその月を使う。
- 時刻は24時間表記の HH:MM にする。おたよりの「4:00〜5:45」「1:15」は午後の意味なので 16:00〜17:45、13:15 と読む。「午前」「午後」が書いてあればそれに従う。
- 複数日に開かれる行事は sessions に1日ずつ入れる。曜日によって時刻が違うものは、日ごとに正しい時刻を入れる。
- 乳幼児向け面の「○月の予定」カレンダーに載っている定例プログラム（のりものタイム、プレイランド等）は、そのカレンダーで丸が付いている日だけを sessions に入れる。時刻は各プログラムの説明欄から取る。
- 「今月のお休み」「館内整理日」「祝日」などの休館日は closed_days に入れ、その日の行事は作らない。
- audience: 小学生以上向け面の行事は kids、乳幼児向け面の行事は baby、両方が対象なら all。
- 申込が必要な行事は requires_application を true にし、受付開始日と締切日（書かれていれば）、申込方法（例: 本人が児童館受付で／窓口または電話）を入れる。「申込みはいりません」と書かれていれば false。
- 「予告」として翌月以降の行事が載っていれば、その日付のまま含める（翌月の行事の申込が今月始まることがあるため）。
- 学童クラブ等の乳幼児向けおたより（ゆうキッズ）も同じ形で読む。乳幼児向けしかない号なら audience は baby、どなたでも参加できる行事は all。
- 利用案内・権利条例の紹介など、日時のある行事でないものは含めない。
- 読み取れない値は推測で埋めず、空文字にする。
"""


def extract_newsletter(client: anthropic.Anthropic, pdf_bytes: bytes) -> dict:
    """PDFのバイト列を渡し、SCHEMA に沿った dict を返す。失敗時は例外を投げる。"""
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("ascii")
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",
            "format": {"type": "json_schema", "schema": SCHEMA},
        },
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64},
                },
                {"type": "text", "text": INSTRUCTIONS},
            ],
        }],
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude が読み取りを断りました: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("出力が上限で途切れました")

    text = next((b.text for b in response.content if b.type == "text"), "")
    logger.info(
        "Claude 読み取り完了 (model=%s, in=%s, out=%s)",
        response.model, response.usage.input_tokens, response.usage.output_tokens,
    )
    return json.loads(text)
