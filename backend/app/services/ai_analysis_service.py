"""Gemini APIを用いて日記の精神状態を分析するサービス。

requirements.md 8章のプロンプト設計に従い、日記本文をGemini APIに渡し、
mood_score / mood_label / keywords / summary をJSON形式で取得する。
"""

import json
import logging
import re
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
REQUEST_TIMEOUT_SECONDS = 30.0

PROMPT_TEMPLATE = """以下はユーザーが書いた今日の日記です。この内容から精神状態を分析し、
必ず次のJSON形式のみで出力してください。説明文や前置き、Markdownのコードブロック記号は一切含めないでください。

{{
  "mood_score": <-5から5の整数>,
  "mood_label": "<良好/普通/やや不調/不調 のいずれか>",
  "keywords": ["<要因1>", "<要因2>", ...],
  "summary": "<30〜50文字程度の一言コメント>"
}}

日記本文:
\"\"\"
{diary_text}
\"\"\"
"""


@dataclass
class MoodAnalysis:
    """Geminiによる精神状態分析結果。"""

    mood_score: int
    mood_label: str
    keywords: list[str]
    summary: str


def _extract_json(text: str) -> dict:
    """Geminiのレスポンステキストから JSON 部分を取り出す。

    プロンプトでMarkdown記号を含めないよう指定しているが、
    念のためコードブロック(```json ... ```)が付与された場合にも対応する。
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def analyze_mood(diary_text: str) -> MoodAnalysis | None:
    """日記本文をGemini APIに送り、精神状態分析結果を取得する。

    APIキー未設定・通信エラー・レスポンス形式不正などの場合はNoneを返し、
    呼び出し側で「AI分析なしで保存」にフォールバックできるようにする(日記保存自体は妨げない)。
    """
    api_key = get_settings().gemini_api_key
    if not api_key:
        logger.warning("GEMINI_API_KEYが未設定のため、AI分析をスキップしました")
        return None

    prompt = PROMPT_TEMPLATE.format(diary_text=diary_text)

    try:
        response = httpx.post(
            GEMINI_API_URL,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = _extract_json(raw_text)
    except httpx.HTTPStatusError as exc:
        # URLにAPIキーがクエリパラメータで含まれるため、exc_info(トレースバック)は出力しない
        logger.warning("Gemini APIがエラーを返しました(status=%s)", exc.response.status_code)
        return None
    except httpx.HTTPError:
        logger.warning("Gemini APIへの接続に失敗しました")
        return None
    except (KeyError, IndexError, json.JSONDecodeError):
        logger.warning("Gemini APIのレスポンス形式が想定外でした")
        return None

    try:
        return MoodAnalysis(
            mood_score=int(parsed["mood_score"]),
            mood_label=str(parsed["mood_label"]),
            keywords=[str(keyword) for keyword in parsed.get("keywords", [])],
            summary=str(parsed["summary"]),
        )
    except (KeyError, TypeError, ValueError):
        logger.warning("Gemini APIのレスポンス形式が想定外でした(JSONフィールド不足)")
        return None
