"""日記×AI精神状態分析アプリ - エントリーポイント。

st.navigation()で6画面(ホーム/日記/一覧/傾向/AI相談/設定)を束ねるルーター。
各画面の実装は screens/ 以下に分割している(project-rulesの「機能単位でファイルを分ける」に準拠)。
"""

import functools

import streamlit as st

from screens import ai_consult, diary, entries, home, settings, trends

st.set_page_config(page_title="日記×AI精神状態分析", page_icon="📔", layout="wide")

page_diary = st.Page(diary.render, title="日記", icon="📝", url_path="diary")
page_entries = st.Page(entries.render, title="一覧", icon="📖", url_path="entries")
page_trends = st.Page(trends.render, title="傾向", icon="📊", url_path="trends")
page_ai_consult = st.Page(ai_consult.render, title="AI相談", icon="💬", url_path="ai-consult")
page_settings = st.Page(settings.render, title="設定", icon="⚙️", url_path="settings")
# ホーム画面は「日記タブへ」の導線を表示するため、diary_pageを渡す
page_home = st.Page(
    functools.partial(home.render, diary_page=page_diary),
    title="ホーム",
    icon="🏠",
    url_path="home",
    default=True,
)

pg = st.navigation(
    [page_home, page_diary, page_entries, page_trends, page_ai_consult, page_settings]
)
pg.run()
