"""過去の日記一覧画面。

バックエンドAPI(GET /entries)から日記一覧を日付降順で取得し、
期間フィルタ(直近7日/直近30日/全期間)付きで一覧表示する。
"""

from datetime import date, timedelta

import streamlit as st

from api_client import list_entries
from mood_utils import mood_score_to_stars

MOOD_COLORS = {
    "良好": "green",
    "普通": "blue",
    "やや不調": "orange",
    "不調": "red",
}


def render() -> None:
    """日記一覧画面を描画する。"""
    st.title("📖 日記一覧")

    period_option = st.radio(
        "表示期間",
        options=["直近7日", "直近30日", "全期間"],
        horizontal=True,
    )

    start_date: date | None = None
    if period_option == "直近7日":
        start_date = date.today() - timedelta(days=7)
    elif period_option == "直近30日":
        start_date = date.today() - timedelta(days=30)

    try:
        entries = list_entries(start_date=start_date)
    except Exception as exc:  # noqa: BLE001 - 画面表示のためあえて広く捕捉する
        st.error(f"日記一覧の取得に失敗しました: {exc}")
        entries = []

    if not entries:
        st.info("該当する日記がまだありません。")

    for entry in entries:
        mood_label = entry.get("mood_label")
        stars = mood_score_to_stars(entry.get("mood_score"))
        color = MOOD_COLORS.get(mood_label, "gray")
        header = f"{entry['entry_date']} - :{color}[{mood_label or '未分析'}] {stars or ''}"

        with st.expander(header):
            meta_parts = []
            if entry.get("weather"):
                meta_parts.append(f"🌤️ {entry['weather']}")
            if entry.get("pressure_hpa") is not None:
                meta_parts.append(f"🧭 気圧 {entry['pressure_hpa']}hPa")
            if entry.get("sleep_hours") is not None:
                meta_parts.append(f"💤 睡眠 {entry['sleep_hours']}時間")
            if entry.get("location_name"):
                meta_parts.append(f"📍 {entry['location_name']}")
            if meta_parts:
                st.caption(" / ".join(meta_parts))

            st.write(entry["diary_text"])

            if entry.get("ai_summary"):
                st.markdown(f"**AIの一言コメント:** {entry['ai_summary']}")

            keywords = entry.get("keywords") or []
            if keywords:
                st.markdown("キーワード: " + " ".join(f"`{keyword}`" for keyword in keywords))
