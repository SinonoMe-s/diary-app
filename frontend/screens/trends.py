"""「傾向」タブ。

期間フィルタ(直近7日/直近30日/全期間)を適用した上で、
- mood_scoreの推移を折れ線グラフ
- 気圧・睡眠時間とmood_scoreの相関を散布図
- keywordsの出現頻度をランキング形式(棒グラフ)
で可視化する。

グラフ描画はStreamlit標準のst.line_chart/st.scatter_chart/st.bar_chartのみを使い、
matplotlib等の追加ライブラリは使わない方針とする。集計にはpandasを利用する。
"""

from collections import Counter
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from api_client import list_entries


def _to_dataframe(entries: list[dict]) -> pd.DataFrame:
    """API取得結果(dictのlist)をpandas DataFrameに変換する。entry_dateはdatetime化する。"""
    if not entries:
        return pd.DataFrame(
            columns=["entry_date", "mood_score", "pressure_hpa", "sleep_hours", "keywords"]
        )
    df = pd.DataFrame(entries)
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df = df.sort_values("entry_date")
    return df


def _render_mood_trend(df: pd.DataFrame) -> None:
    """mood_scoreの推移を折れ線グラフで表示する。"""
    st.subheader("📈 気分スコアの推移")
    mood_df = df.dropna(subset=["mood_score"])
    if mood_df.empty:
        st.caption("表示できる気分スコアのデータがまだありません。")
        return
    chart_df = mood_df.set_index("entry_date")[["mood_score"]]
    st.line_chart(chart_df, y="mood_score")


def _render_correlation(df: pd.DataFrame) -> None:
    """気圧・睡眠時間とmood_scoreの相関を散布図で表示する。"""
    st.subheader("🔍 気圧・睡眠時間との相関")

    col1, col2 = st.columns(2)

    with col1:
        st.caption("気圧 × 気分スコア")
        pressure_df = df.dropna(subset=["mood_score", "pressure_hpa"])
        if pressure_df.empty:
            st.caption("表示できるデータがまだありません。")
        else:
            st.scatter_chart(pressure_df, x="pressure_hpa", y="mood_score")

    with col2:
        st.caption("睡眠時間 × 気分スコア")
        sleep_df = df.dropna(subset=["mood_score", "sleep_hours"])
        if sleep_df.empty:
            st.caption("表示できるデータがまだありません。")
        else:
            st.scatter_chart(sleep_df, x="sleep_hours", y="mood_score")


def _render_keyword_ranking(df: pd.DataFrame) -> None:
    """keywordsの出現頻度をランキング形式(棒グラフ)で表示する。"""
    st.subheader("🏷️ キーワード出現ランキング")

    counter: Counter[str] = Counter()
    for keywords in df["keywords"]:
        if isinstance(keywords, list):
            counter.update(keywords)

    if not counter:
        st.caption("表示できるキーワードのデータがまだありません。")
        return

    ranking_df = (
        pd.DataFrame(counter.most_common(15), columns=["キーワード", "出現回数"])
        .set_index("キーワード")
    )
    st.bar_chart(ranking_df, y="出現回数", horizontal=True)


def render() -> None:
    """傾向タブを描画する。"""
    st.title("📊 傾向")

    period_option = st.radio(
        "表示期間",
        options=["直近7日", "直近30日", "全期間"],
        horizontal=True,
        index=1,
    )

    start_date: date | None = None
    if period_option == "直近7日":
        start_date = date.today() - timedelta(days=7)
    elif period_option == "直近30日":
        start_date = date.today() - timedelta(days=30)

    try:
        entries = list_entries(start_date=start_date)
    except Exception as exc:  # noqa: BLE001 - 画面表示のためあえて広く捕捉する
        st.error(f"日記データの取得に失敗しました: {exc}")
        entries = []

    df = _to_dataframe(entries)

    if df.empty:
        st.info("該当する日記がまだありません。")
        return

    _render_mood_trend(df)
    st.divider()
    _render_correlation(df)
    st.divider()
    _render_keyword_ranking(df)
