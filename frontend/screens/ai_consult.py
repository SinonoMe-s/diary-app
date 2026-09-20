"""「AI相談」タブ(チャット形式)。

ユーザーが自由入力で質問・相談を送ると、バックエンドAPI(POST /ai/consult)経由で
直近30日分の日記データをコンテキストとしたGeminiの回答を取得する。
会話履歴はst.session_stateで保持し、同じセッション内では会話を続けられる。
"""

import requests
import streamlit as st

from api_client import consult_ai

DISCLAIMER = "⚠️ この機能はあくまで参考的な見解を提供するものであり、医学的な診断ではありません。"


def render() -> None:
    """AI相談タブを描画する。"""
    st.title("💬 AI相談")
    st.caption("直近30日分の日記データをもとに、AIが調子について一緒に考えます。気になることを聞いてみましょう。")
    st.info(DISCLAIMER)

    if "consult_history" not in st.session_state:
        st.session_state.consult_history = []

    for message in st.session_state.consult_history:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(message["content"])

    user_input = st.chat_input("例: 最近調子が悪い理由は?")

    if user_input:
        st.session_state.consult_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AIが回答を考えています..."):
                # 直前のメッセージ(今回のuser_input)を除いた、これまでの会話履歴を渡す
                history = st.session_state.consult_history[:-1]
                try:
                    reply = consult_ai(user_input, history)
                except requests.HTTPError as exc:
                    if exc.response is not None and exc.response.status_code == 429:
                        st.error(
                            "Gemini APIのレート制限に達しました。しばらく時間をおいてから再度お試しください。"
                        )
                    else:
                        st.error(f"回答の取得に失敗しました: {exc}")
                except Exception as exc:  # noqa: BLE001 - 画面表示のためあえて広く捕捉する
                    st.error(f"回答の取得に失敗しました: {exc}")
                else:
                    st.markdown(reply)
                    st.session_state.consult_history.append({"role": "model", "content": reply})
