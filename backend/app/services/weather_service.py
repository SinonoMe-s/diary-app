"""天気・気圧情報を取得するサービス。

OpenWeatherMapのGeocoding API(地名→緯度経度)とCurrent Weather API(緯度経度→天気・気圧)を
組み合わせて、「地名から天気・気圧を取得する」一連の処理を提供する。

天気取得は日記保存を妨げてはいけないため、APIキー未設定・通信エラー・
想定外のレスポンスなど、失敗しうるケースでは例外を投げずNoneを返す設計にしている。
呼び出し側はNoneの場合、天気・気圧を空のまま保存する。
"""

import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
REQUEST_TIMEOUT_SECONDS = 5.0
FORECAST_SLOT_COUNT = 8  # 3時間ごと×8コマ=次24時間分


@dataclass
class WeatherInfo:
    """取得した天気・気圧情報。"""

    weather: str
    pressure_hpa: float


@dataclass
class ForecastSlot:
    """天気予報の1コマ(3時間区切り)分の情報。"""

    datetime_text: str  # 例: "09/21 15:00"
    weather: str
    temperature: float
    pressure_hpa: float


def geocode_location(location_name: str) -> tuple[float, float] | None:
    """地名から緯度経度を取得する。取得できない場合はNoneを返す。"""
    api_key = get_settings().weather_api_key
    if not api_key:
        logger.warning("WEATHER_API_KEYが未設定のため、ジオコーディングをスキップしました")
        return None

    try:
        response = httpx.get(
            GEOCODING_URL,
            params={"q": location_name, "limit": 1, "appid": api_key},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json()
    except httpx.HTTPStatusError as exc:
        # URLにAPIキーがクエリパラメータで含まれるため、exc_info(トレースバック)は出力しない
        logger.warning("ジオコーディングAPIがエラーを返しました(status=%s)", exc.response.status_code)
        return None
    except httpx.HTTPError:
        logger.warning("ジオコーディングAPIへの接続に失敗しました")
        return None

    if not results:
        logger.warning("地名 '%s' に一致する位置情報が見つかりませんでした", location_name)
        return None

    return float(results[0]["lat"]), float(results[0]["lon"])


def fetch_current_weather(latitude: float, longitude: float) -> WeatherInfo | None:
    """緯度経度から現在の天気・気圧を取得する。取得できない場合はNoneを返す。"""
    api_key = get_settings().weather_api_key
    if not api_key:
        logger.warning("WEATHER_API_KEYが未設定のため、天気取得をスキップしました")
        return None

    try:
        response = httpx.get(
            CURRENT_WEATHER_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "appid": api_key,
                "units": "metric",
                "lang": "ja",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        # URLにAPIキーがクエリパラメータで含まれるため、exc_info(トレースバック)は出力しない
        logger.warning("天気取得APIがエラーを返しました(status=%s)", exc.response.status_code)
        return None
    except httpx.HTTPError:
        logger.warning("天気取得APIへの接続に失敗しました")
        return None

    try:
        weather_description = str(data["weather"][0]["description"])
        pressure_hpa = float(data["main"]["pressure"])
    except (KeyError, IndexError, TypeError):
        logger.warning("天気APIのレスポンス形式が想定外でした")
        return None

    return WeatherInfo(weather=weather_description, pressure_hpa=pressure_hpa)


def fetch_forecast(latitude: float, longitude: float) -> list[ForecastSlot] | None:
    """緯度経度から次24時間分(3時間ごと×8コマ)の天気予報を取得する。

    OpenWeatherMapの無料プランに含まれる「5 day / 3 hour forecast」APIを使用し、
    cntパラメータで先頭8コマ(=24時間分)だけを取得する。
    取得できない場合はNoneを返す(呼び出し側は予報欄を非表示にする想定)。
    """
    api_key = get_settings().weather_api_key
    if not api_key:
        logger.warning("WEATHER_API_KEYが未設定のため、天気予報取得をスキップしました")
        return None

    try:
        response = httpx.get(
            FORECAST_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "appid": api_key,
                "units": "metric",
                "lang": "ja",
                "cnt": FORECAST_SLOT_COUNT,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        # URLにAPIキーがクエリパラメータで含まれるため、exc_info(トレースバック)は出力しない
        logger.warning("天気予報APIがエラーを返しました(status=%s)", exc.response.status_code)
        return None
    except httpx.HTTPError:
        logger.warning("天気予報APIへの接続に失敗しました")
        return None

    try:
        slots = [
            ForecastSlot(
                datetime_text=item["dt_txt"],
                weather=str(item["weather"][0]["description"]),
                temperature=float(item["main"]["temp"]),
                pressure_hpa=float(item["main"]["pressure"]),
            )
            for item in data["list"][:FORECAST_SLOT_COUNT]
        ]
    except (KeyError, IndexError, TypeError):
        logger.warning("天気予報APIのレスポンス形式が想定外でした")
        return None

    return slots or None


def get_weather_info(
    location_name: str | None,
    default_latitude: float,
    default_longitude: float,
) -> WeatherInfo | None:
    """地名が指定されていればその地点、なければデフォルト地点(自宅地域)の天気・気圧を取得する。

    location_nameのジオコーディングに失敗した場合はデフォルト地点にフォールバックする。
    """
    latitude, longitude = default_latitude, default_longitude

    if location_name is not None:
        geocoded = geocode_location(location_name)
        if geocoded is not None:
            latitude, longitude = geocoded
        else:
            logger.warning(
                "'%s' の位置情報が取得できなかったため、デフォルト地点の天気を使用します", location_name
            )

    return fetch_current_weather(latitude, longitude)
