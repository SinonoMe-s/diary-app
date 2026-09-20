"""ホーム画面。

- 本日すでに記録済みなら気分・一言コメント・天気をカード表示。未記入なら日記画面への導線を表示する
- 直近14日間を横並びの簡易カレンダーで表示し、気分に応じて色分けする
- ルールベースの「AIひとことフィードバック」を表示する
- 設定済みデフォルト地域の次24時間分(3時間ごと)の天気予報を表示する
"""

from datetime import date, timedelta
from typing import Any

import streamlit as st

from api_client import get_forecast, list_entries
from feedback_utils import generate_home_feedback
from mood_utils import mood_score_to_stars

CALENDAR_DAYS = 14

# 気分ラベルに応じたカレンダーの色分け(ダークテーマ想定の配色)
MOOD_COLORS = {
    "良好": "#2e7d32",  # 緑
    "普通": "#1565c0",  # 青
    "やや不調": "#ef6c00",  # オレンジ
    "不調": "#616161",  # グレー(暗め)
}
NO_ENTRY_COLOR = "#333333"  # 記録なしの薄いグレー

LEGEND_ITEMS = [
    ("🟩", "良好"),
    ("🟦", "普通"),
    ("🟧", "やや不調"),
    ("⬛", "不調"),
    ("⬜", "記録なし"),
]


def _fetch_recent_entries() -> dict[str, dict[str, Any]]:
    """直近CALENDAR_DAYS日分の日記を取得し、日付文字列(YYYY-MM-DD)をキーにした辞書にする。"""
    start = date.today() - timedelta(days=CALENDAR_DAYS - 1)
    entries = list_entries(start_date=start)
    return {entry["entry_date"]: entry for entry in entries}


def _render_today_card(entries_by_date: dict[str, dict[str, Any]], diary_page: st.Page) -> None:
    """本日の記録カード、または未記入時は日記画面への導線を表示する。"""
    st.subheader("今日の記録")
    today_entry = entries_by_date.get(date.today().isoformat())

    if today_entry is None:
        st.info("まだ今日の日記が記録されていません。")
        st.page_link(diary_page, label="日記タブへ", icon="📝")
        return

    mood_label = today_entry.get("mood_label")
    stars = mood_score_to_stars(today_entry.get("mood_score"))

    with st.container(border=True):
        cols = st.columns([1, 2])
        with cols[0]:
            st.markdown(f"#### {mood_label or '未分析'}")
            if stars:
                st.markdown(f"### {stars}")
        with cols[1]:
            if today_entry.get("ai_summary"):
                st.write(today_entry["ai_summary"])
            weather = today_entry.get("weather")
            pressure_hpa = today_entry.get("pressure_hpa")
            if weather or pressure_hpa is not None:
                pressure_text = f"{pressure_hpa}hPa" if pressure_hpa is not None else "不明"
                st.caption(f"🌤️ {weather or '不明'} / 気圧 {pressure_text}")


def _render_calendar(entries_by_date: dict[str, dict[str, Any]]) -> None:
    """直近CALENDAR_DAYS日分を横並びの簡易カレンダーとして気分で色分け表示する。"""
    st.subheader(f"直近{CALENDAR_DAYS}日間の気分カレンダー")

    days = [date.today() - timedelta(days=offset) for offset in range(CALENDAR_DAYS - 1, -1, -1)]
    columns = st.columns(len(days))

    for col, day in zip(columns, days):
        entry = entries_by_date.get(day.isoformat())
        mood_label = entry.get("mood_label") if entry else None
        color = MOOD_COLORS.get(mood_label, NO_ENTRY_COLOR)
        with col:
            st.markdown(
                f"""
                <div style="
                    background-color:{color};
                    border-radius:6px;
                    text-align:center;
                    padding:6px 0;
                    color:white;
                    font-size:12px;
                ">
                    {day.day}
                </div>
                """,
                unsafe_allow_html=True,
            )

    legend_text = "  ".join(f"{icon}{label}" for icon, label in LEGEND_ITEMS)
    st.caption(legend_text)


def _render_ai_feedback(entries_by_date: dict[str, dict[str, Any]]) -> None:
    """ルールベースのAIひとことフィードバックを表示する(天気・気圧×直近3日の調子)。"""
    st.subheader("💬 AIからのひとこと")
    feedback = generate_home_feedback(entries_by_date)
    if feedback is None:
        st.caption("直近の記録が少ないため、まだコメントを表示できません。")
        return
    st.info(feedback)


def _format_forecast_time(datetime_text: str) -> str:
    """'2026-09-21 15:00:00' のような文字列から 'HH:00' 部分だけを取り出す。"""
    try:
        return datetime_text.split(" ")[1][:5]
    except IndexError:
        return datetime_text


def _render_forecast() -> None:
    """設定済みデフォルト地域の次24時間分(3時間ごと・8コマ)の天気予報を表示する。"""
    st.subheader("設定地域の天気予報(次24時間)")
    st.caption("※ OpenWeatherMapの3時間ごと予報を、直近8コマ(24時間分)表示しています。")

    try:
        slots = get_forecast()
    except Exception as exc:  # noqa: BLE001 - 画面表示のためあえて広く捕捉する
        st.caption(f"天気予報の取得中にエラーが発生しました: {exc}")
        return

    if not slots:
        st.caption("天気予報を取得できませんでした(APIキー未設定・通信エラー等の可能性があります)")
        return

    columns = st.columns(len(slots))
    for col, slot in zip(columns, slots):
        with col:
            st.markdown(f"**{_format_forecast_time(slot['datetime_text'])}**")
            st.caption(slot["weather"])
            st.write(f"{slot['temperature']:.0f}℃")
            st.caption(f"{slot['pressure_hpa']:.0f}hPa")


def render(diary_page: st.Page) -> None:
    """ホーム画面を描画する。

    Args:
        diary_page: 「日記タブへ」の導線用に、日記入力画面のst.Pageを受け取る。
    """
    st.title("🏠 ホーム")

    try:
        entries_by_date = _fetch_recent_entries()
    except Exception as exc:  # noqa: BLE001 - 画面表示のためあえて広く捕捉する
        st.error(f"日記データの取得に失敗しました: {exc}")
        entries_by_date = {}

    _render_today_card(entries_by_date, diary_page)
    st.divider()
    _render_ai_feedback(entries_by_date)
    st.divider()
    _render_calendar(entries_by_date)
    st.divider()
    _render_forecast()
