"""日記入力画面(チャット形式)。

チャット形式で日記を入力すると、バックエンドAPI(POST /entries)経由で
Gemini APIによる精神状態分析と天気・気圧の自動取得が行われ、その結果を表示する。
"""

import streamlit as st

from api_client import create_entry
from mood_utils import mood_score_to_stars

# 気分ラベルに応じたアイコン(見た目をやわらかくするための簡易マッピング)
MOOD_ICONS = {
    "良好": "😊",
    "普通": "😐",
    "やや不調": "😕",
    "不調": "😞",
}


def render() -> None:
    """日記入力画面を描画する。"""
    st.title("📝 日記 × AI精神状態分析")
    st.caption("今日の出来事や気分を自由に書いてください。送信するとAIが精神状態を分析します。")

    with st.sidebar:
        st.header("詳細オプション")
        st.caption("以下は任意項目です。入力しなくても日記は保存できます。")
        sleep_hours_input = st.number_input(
            "睡眠時間(時間)",
            min_value=0.0,
            max_value=24.0,
            step=0.5,
            value=None,
            placeholder="例: 6.5",
            format="%.1f",
            help="将来的にはApple Health等との自動連携を予定していますが、現在は手動入力です",
        )
        location_name_input = st.text_input(
            "地域名(天気取得用)",
            placeholder="例: 東京都渋谷区",
            help="未入力の場合は設定済みのデフォルト地域の天気・気圧が使われます",
        )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("今日の出来事や気分を書いてください")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AIが分析中..."):
                try:
                    entry = create_entry(
                        diary_text=user_input,
                        sleep_hours=sleep_hours_input,
                        location_name=location_name_input or None,
                    )
                except Exception as exc:  # noqa: BLE001 - 画面表示のためあえて広く捕捉する
                    error_text = f"⚠️ 保存に失敗しました: {exc}"
                    st.error(error_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_text})
                else:
                    mood_label = entry.get("mood_label")
                    icon = MOOD_ICONS.get(mood_label, "🤖")
                    stars = mood_score_to_stars(entry.get("mood_score"))
                    header_line = f"{icon} **{mood_label or '(AI分析結果なし)'}**"
                    if stars:
                        header_line += f"  {stars}"
                    lines = [header_line]

                    if entry.get("ai_summary"):
                        lines.append(entry["ai_summary"])

                    keywords = entry.get("keywords") or []
                    if keywords:
                        tags = " ".join(f"`{keyword}`" for keyword in keywords)
                        lines.append(f"キーワード: {tags}")

                    weather = entry.get("weather")
                    pressure_hpa = entry.get("pressure_hpa")
                    if weather or pressure_hpa is not None:
                        weather_text = weather or "不明"
                        pressure_text = f"{pressure_hpa}hPa" if pressure_hpa is not None else "不明"
                        lines.append(f"🌤️ 天気: {weather_text} / 気圧: {pressure_text}")
                    else:
                        lines.append("🌤️ 天気情報は取得できませんでした")

                    response_text = "\n\n".join(lines)
                    st.markdown(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
