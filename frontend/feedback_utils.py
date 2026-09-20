"""ホーム画面の「AIひとことフィードバック」用ロジック。

Gemini API等は呼ばず、直近3日間の気分傾向 × 天気・気圧の状況を組み合わせた
ルールベース(3パターン × 4パターン = 12パターン)の固定文言を返す。
テキストのみで表示し、画像・マスコットは扱わない。
"""

from datetime import date, timedelta
from typing import Any

# 気圧低下とみなす閾値(hPa)。直近2件の記録を比較し、これ以上下がっていれば「気圧低下」とする。
PRESSURE_DROP_THRESHOLD_HPA = 3.0

# 好調/普通/不調の判定閾値(mood_scoreは-5〜5)
MOOD_GOOD_THRESHOLD = 2
MOOD_BAD_THRESHOLD = -2

FEEDBACK_MESSAGES: dict[tuple[str, str], str] = {
    ("good", "pressure_drop"): "絶好調のようですね!ただ気圧が下がり気味なので、無理せずマイペースに過ごしましょう。",
    ("good", "rain"): "調子は良さそうです。雨の日ですが、この調子を保てそうですね。",
    ("good", "clear"): "良い調子が続いていますね!晴れの日を活かして気分転換もよさそうです。",
    ("good", "other"): "順調に過ごせているようです。この調子を大切にしてくださいね。",
    ("normal", "pressure_drop"): "気圧が下がり気味です。頭痛や倦怠感が出やすい時期なので、こまめに休憩を挟んでみてください。",
    ("normal", "rain"): "雨の日は気分が沈みやすいもの。温かい飲み物でも一息ついてみては。",
    ("normal", "clear"): "穏やかに過ごせているようです。晴れの日の散歩もおすすめです。",
    ("normal", "other"): "いつも通りのペースで過ごせているようですね。",
    ("bad", "pressure_drop"): "気圧の変化で調子を崩しやすいタイミングかもしれません。無理せず休息を優先してくださいね。",
    ("bad", "rain"): "ここ数日調子が優れないようです。雨の日は特に、心身を労わる時間を作ってみましょう。",
    ("bad", "clear"): "少し調子が落ち気味のようです。晴れの日に軽く外の空気を吸うのもおすすめです。",
    ("bad", "other"): "無理せず、自分のペースを大切にしてくださいね。",
}

RECENT_DAYS = 3


def _judge_mood_trend(entries_by_date: dict[str, dict[str, Any]]) -> str | None:
    """直近RECENT_DAYS日間のmood_score平均から好調/普通/不調を判定する。

    対象日にmood_scoreが1件も無い場合はNoneを返す(フィードバック非表示の判断に使う)。
    """
    scores: list[int] = []
    for offset in range(RECENT_DAYS):
        day = date.today() - timedelta(days=offset)
        entry = entries_by_date.get(day.isoformat())
        if entry and entry.get("mood_score") is not None:
            scores.append(entry["mood_score"])

    if not scores:
        return None

    average = sum(scores) / len(scores)
    if average >= MOOD_GOOD_THRESHOLD:
        return "good"
    if average <= MOOD_BAD_THRESHOLD:
        return "bad"
    return "normal"


def _judge_weather_factor(entries_by_date: dict[str, dict[str, Any]]) -> str:
    """最新2件の気圧記録の差、および直近の天気テキストから気圧低下/雨/晴れ/その他を判定する。"""
    recent_entries = []
    for offset in range(RECENT_DAYS):
        day = date.today() - timedelta(days=offset)
        entry = entries_by_date.get(day.isoformat())
        if entry:
            recent_entries.append(entry)

    # 気圧低下判定: 直近2件の気圧記録がある場合、最新が直前より一定以上下がっていれば「気圧低下」
    pressures = [e["pressure_hpa"] for e in recent_entries if e.get("pressure_hpa") is not None]
    if len(pressures) >= 2 and (pressures[1] - pressures[0]) >= PRESSURE_DROP_THRESHOLD_HPA:
        return "pressure_drop"

    # 天気判定: 最新の記録の天気テキストを見る
    latest_weather = next((e.get("weather") for e in recent_entries if e.get("weather")), None)
    if latest_weather:
        if "雨" in latest_weather:
            return "rain"
        if "晴" in latest_weather:
            return "clear"

    return "other"


def generate_home_feedback(entries_by_date: dict[str, dict[str, Any]]) -> str | None:
    """ホーム画面に表示するAIひとことフィードバックを生成する。

    直近3日間にmood_scoreの記録が無い場合はNoneを返す(呼び出し側で非表示にする)。
    """
    mood_trend = _judge_mood_trend(entries_by_date)
    if mood_trend is None:
        return None

    weather_factor = _judge_weather_factor(entries_by_date)
    return FEEDBACK_MESSAGES[(mood_trend, weather_factor)]
