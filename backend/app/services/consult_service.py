"""AI相談チャット機能: 直近30日分の日記データをコンテキストとしてGeminiと対話するサービス。

- コンテキストはバックエンド側でDBから取得し、Geminiのsystem_instructionに埋め込む
  (フロントエンドにAPIキーや生データの受け渡しロジックを持たせないため)。
- 会話履歴はフロントエンド(st.session_state)側で保持し、リクエストの度に渡してもらう。
  Geminiのcontents配列にuser/model交互のターンとして渡すことで、マルチターン対話を実現する。
- プロンプトには「診断ではなく参考的な見解であること」を必ず含める。
"""

import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import DEFAULT_USER_ID
from app.models.diary_entry import DiaryEntry

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
REQUEST_TIMEOUT_SECONDS = 30.0
CONTEXT_DAYS = 30

SYSTEM_INSTRUCTION_TEMPLATE = """あなたはユーザーの日記・体調データを踏まえて対話する、心身の調子に関する相談相手です。
以下はユーザーの直近{context_days}日間の記録データです(古い順、記録が無い日は含まれません)。

{context_text}

# 応答時の注意事項
- これは医学的な診断ではなく、あくまで参考的な見解・アドバイスであることを、回答の中で必ず一言明示してください。
- 断定的な診断名や治療方針の提示は行わないでください。
- データから読み取れる傾向を踏まえつつ、やわらかく共感的な言葉遣いで答えてください。
- 深刻な症状が疑われる内容の場合は、医療機関や専門家への相談を勧めてください。
"""


class ConsultRateLimitError(Exception):
    """Gemini APIのレート制限(429)に達した場合に送出する例外。"""


@dataclass
class ChatTurn:
    """会話履歴の1ターン分。"""

    role: str  # "user" または "model"
    content: str


def _build_context_text(entries: list[DiaryEntry]) -> str:
    """直近の日記エントリー群を、Geminiに渡すテキスト形式の要約に変換する。"""
    if not entries:
        return "(直近の日記データはまだ記録されていません)"

    lines: list[str] = []
    for entry in sorted(entries, key=lambda e: e.entry_date):
        try:
            keywords = json.loads(entry.keywords) if entry.keywords else []
        except (json.JSONDecodeError, TypeError):
            keywords = []

        parts = [f"{entry.entry_date.isoformat()}:"]
        parts.append(f"気分スコア={entry.mood_score if entry.mood_score is not None else '不明'}")
        parts.append(f"気分ラベル={entry.mood_label or '不明'}")
        parts.append(f"キーワード={', '.join(keywords) if keywords else 'なし'}")
        parts.append(f"天気={entry.weather or '不明'}")
        parts.append(
            f"気圧={entry.pressure_hpa}hPa" if entry.pressure_hpa is not None else "気圧=不明"
        )
        parts.append(
            f"睡眠時間={entry.sleep_hours}時間" if entry.sleep_hours is not None else "睡眠時間=不明"
        )
        lines.append(" / ".join(parts))

    return "\n".join(lines)


def _fetch_recent_entries(db: Session) -> list[DiaryEntry]:
    """直近CONTEXT_DAYS日分の日記エントリーを取得する。"""
    start_date = date.today() - timedelta(days=CONTEXT_DAYS - 1)
    stmt = select(DiaryEntry).where(
        DiaryEntry.user_id == DEFAULT_USER_ID, DiaryEntry.entry_date >= start_date
    )
    return list(db.execute(stmt).scalars().all())


def generate_reply(db: Session, message: str, history: list[ChatTurn]) -> str:
    """ユーザーからのメッセージに対するAI相談の回答を生成する。

    直近30日分の日記データをsystem_instructionとして付与し、
    historyを会話ターンとしてcontentsに積んだ上でGemini APIを呼び出す。

    Raises:
        ConsultRateLimitError: Gemini APIがレート制限(429)を返した場合。
        RuntimeError: その他の理由で回答を生成できなかった場合。
    """
    api_key = get_settings().gemini_api_key
    if not api_key:
        logger.warning("GEMINI_API_KEYが未設定のため、AI相談を実行できません")
        raise RuntimeError("GEMINI_API_KEYが未設定のため、AI相談機能を利用できません")

    entries = _fetch_recent_entries(db)
    context_text = _build_context_text(entries)
    system_instruction = SYSTEM_INSTRUCTION_TEMPLATE.format(
        context_days=CONTEXT_DAYS, context_text=context_text
    )

    contents = [{"role": turn.role, "parts": [{"text": turn.content}]} for turn in history]
    contents.append({"role": "user", "parts": [{"text": message}]})

    try:
        response = httpx.post(
            GEMINI_API_URL,
            params={"key": api_key},
            json={
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": contents,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        reply_text = str(data["candidates"][0]["content"]["parts"][0]["text"])
    except httpx.HTTPStatusError as exc:
        # URLにAPIキーがクエリパラメータで含まれるため、exc_info(トレースバック)は出力しない
        if exc.response.status_code == 429:
            logger.warning("Gemini APIのレート制限に達しました(status=429)")
            raise ConsultRateLimitError("Gemini APIのレート制限に達しました") from exc
        logger.warning("Gemini APIがエラーを返しました(status=%s)", exc.response.status_code)
        raise RuntimeError("AI相談の回答生成に失敗しました") from exc
    except httpx.HTTPError as exc:
        logger.warning("Gemini APIへの接続に失敗しました")
        raise RuntimeError("AI相談の回答生成に失敗しました") from exc
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("Gemini APIのレスポンス形式が想定外でした")
        raise RuntimeError("AI相談の回答生成に失敗しました") from exc

    return reply_text
