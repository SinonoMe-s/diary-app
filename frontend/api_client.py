"""バックエンド(FastAPI)との通信をまとめるモジュール。

画面側(app.py・pages/以下)はこのモジュールの関数を呼ぶだけにし、
HTTP通信の詳細を意識しなくてよいようにする。
"""

from datetime import date
from typing import Any

import requests

from config import API_BASE_URL

REQUEST_TIMEOUT_SECONDS = 30


def create_entry(
    diary_text: str,
    sleep_hours: float | None = None,
    location_name: str | None = None,
) -> dict[str, Any]:
    """日記を保存する。AI分析(Gemini)・天気取得はバックエンド側で自動実行される。"""
    payload: dict[str, Any] = {"diary_text": diary_text}
    if sleep_hours is not None:
        payload["sleep_hours"] = sleep_hours
    if location_name:
        payload["location_name"] = location_name

    response = requests.post(f"{API_BASE_URL}/entries", json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def list_entries(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    """日記一覧を取得する(日付降順)。start_date/end_dateで期間を絞り込める。"""
    params: dict[str, str] = {}
    if start_date is not None:
        params["start_date"] = start_date.isoformat()
    if end_date is not None:
        params["end_date"] = end_date.isoformat()

    response = requests.get(f"{API_BASE_URL}/entries", params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def get_settings() -> dict[str, Any]:
    """現在のユーザー設定(自宅地域)を取得する。"""
    response = requests.get(f"{API_BASE_URL}/settings", timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def update_settings(
    location_name: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict[str, Any]:
    """ユーザー設定(自宅地域)を更新する。

    location_nameのみ指定した場合、バックエンド側で緯度経度が自動でジオコーディングされる。
    """
    payload: dict[str, Any] = {}
    if location_name is not None:
        payload["location_name"] = location_name
    if latitude is not None:
        payload["latitude"] = latitude
    if longitude is not None:
        payload["longitude"] = longitude

    response = requests.put(f"{API_BASE_URL}/settings", json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def get_current_weather() -> dict[str, Any] | None:
    """設定済みデフォルト地域の現在の天気を取得する。取得できない場合はNoneを返す。"""
    response = requests.get(f"{API_BASE_URL}/settings/weather", timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code != 200:
        return None
    return response.json()


def get_forecast() -> list[dict[str, Any]] | None:
    """設定済みデフォルト地域の次24時間分(3時間ごと)の天気予報を取得する。取得できない場合はNoneを返す。"""
    response = requests.get(f"{API_BASE_URL}/settings/forecast", timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code != 200:
        return None
    return response.json()["slots"]


def consult_ai(message: str, history: list[dict[str, str]]) -> str:
    """AI相談チャットにメッセージを送信し、回答を取得する。

    レート制限(429)を含むエラー時は requests.HTTPError を送出する
    (呼び出し側の画面でst.error表示する想定)。
    """
    payload = {"message": message, "history": history}
    # バックエンド側のGemini呼び出しタイムアウト(30秒)より少し長めに待つ
    response = requests.post(f"{API_BASE_URL}/ai/consult", json=payload, timeout=45)
    response.raise_for_status()
    return response.json()["reply"]
