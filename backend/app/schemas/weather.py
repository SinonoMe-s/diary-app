"""天気情報のレスポンス用 Pydantic スキーマ。"""

from pydantic import BaseModel


class WeatherResponse(BaseModel):
    """現在の天気・気圧情報のレスポンス。"""

    weather: str
    pressure_hpa: float


class ForecastSlotResponse(BaseModel):
    """天気予報の1コマ(3時間区切り)分のレスポンス。"""

    datetime_text: str
    weather: str
    temperature: float
    pressure_hpa: float


class ForecastResponse(BaseModel):
    """次24時間分(3時間ごと)の天気予報レスポンス。"""

    slots: list[ForecastSlotResponse]
