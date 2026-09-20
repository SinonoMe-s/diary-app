"""地域設定画面。

バックエンドの GET/PUT /settings をUIから操作できるようにする。
地名のみ入力すればバックエンド側で緯度経度が自動的にジオコーディングされる。
緯度経度を直接指定したい場合は「詳細設定」から入力できる。
"""

import streamlit as st

from api_client import get_settings, update_settings


def render() -> None:
    """設定画面を描画する。"""
    st.title("⚙️ 設定")
    st.caption("日記保存時・ホーム画面表示時に天気・気圧を自動取得するデフォルト地域を設定します。")

    try:
        current_settings = get_settings()
    except Exception as exc:  # noqa: BLE001 - 画面表示のためあえて広く捕捉する
        st.error(f"設定の取得に失敗しました: {exc}")
        return

    st.subheader("現在の設定")
    col1, col2, col3 = st.columns(3)
    col1.metric("地域名", current_settings["location_name"])
    col2.metric("緯度", current_settings["latitude"])
    col3.metric("経度", current_settings["longitude"])

    st.divider()
    st.subheader("地域名から変更")
    st.caption("地名を入力して保存すると、緯度経度は自動で取得されます。")
    with st.form("update_by_name"):
        new_location_name = st.text_input("地域名", placeholder="例: 大阪市")
        submitted = st.form_submit_button("この地域名で更新")
        if submitted:
            if not new_location_name:
                st.warning("地域名を入力してください。")
            else:
                try:
                    updated = update_settings(location_name=new_location_name)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"更新に失敗しました: {exc}")
                else:
                    st.success(
                        f"「{updated['location_name']}」に更新しました"
                        f"(緯度: {updated['latitude']}, 経度: {updated['longitude']})"
                    )
                    st.rerun()

    with st.expander("詳細設定: 緯度・経度を直接指定する"):
        with st.form("update_by_latlon"):
            manual_location_name = st.text_input(
                "地域名(表示用ラベル)", value=current_settings["location_name"]
            )
            manual_latitude = st.number_input(
                "緯度",
                min_value=-90.0,
                max_value=90.0,
                value=float(current_settings["latitude"]),
                format="%.4f",
            )
            manual_longitude = st.number_input(
                "経度",
                min_value=-180.0,
                max_value=180.0,
                value=float(current_settings["longitude"]),
                format="%.4f",
            )
            manual_submitted = st.form_submit_button("緯度経度を直接保存")
            if manual_submitted:
                try:
                    updated = update_settings(
                        location_name=manual_location_name,
                        latitude=manual_latitude,
                        longitude=manual_longitude,
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"更新に失敗しました: {exc}")
                else:
                    st.success(f"「{updated['location_name']}」に更新しました")
                    st.rerun()
