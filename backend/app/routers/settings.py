"""/settings エンドポイントを定義するルーター。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user_settings import UserSettingsResponse, UserSettingsUpdate
from app.schemas.weather import ForecastResponse, ForecastSlotResponse, WeatherResponse
from app.services import user_settings_service, weather_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=UserSettingsResponse)
def get_settings_endpoint(db: Session = Depends(get_db)) -> UserSettingsResponse:
    """現在のユーザー設定(自宅地域)を取得する。レコードが無い場合は初期値で自動作成する。"""
    settings_row = user_settings_service.get_or_create_settings(db)
    return UserSettingsResponse.model_validate(settings_row)


@router.put("", response_model=UserSettingsResponse)
def update_settings_endpoint(
    payload: UserSettingsUpdate, db: Session = Depends(get_db)
) -> UserSettingsResponse:
    """ユーザー設定を更新する。location_nameのみ指定した場合は緯度経度を自動でジオコーディングする。"""
    update_data = payload.model_dump(exclude_unset=True)
    try:
        settings_row = user_settings_service.update_settings(db, update_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserSettingsResponse.model_validate(settings_row)


@router.get("/weather", response_model=WeatherResponse)
def get_current_weather_for_default_location(db: Session = Depends(get_db)) -> WeatherResponse:
    """設定済みデフォルト地域(user_settings)の現在の天気・気圧を取得する。

    フロントエンドのホーム画面表示用。日記エントリーとは独立して、呼び出し時点の最新情報を返す。
    """
    settings_row = user_settings_service.get_or_create_settings(db)
    weather_info = weather_service.fetch_current_weather(settings_row.latitude, settings_row.longitude)
    if weather_info is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="天気情報を取得できませんでした"
        )
    return WeatherResponse(weather=weather_info.weather, pressure_hpa=weather_info.pressure_hpa)


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast_for_default_location(db: Session = Depends(get_db)) -> ForecastResponse:
    """設定済みデフォルト地域(user_settings)の次24時間分(3時間ごと)の天気予報を取得する。

    フロントエンドのホーム画面表示用。OpenWeatherMap無料プランのForecast APIを利用する。
    """
    settings_row = user_settings_service.get_or_create_settings(db)
    slots = weather_service.fetch_forecast(settings_row.latitude, settings_row.longitude)
    if slots is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="天気予報を取得できませんでした"
        )
    return ForecastResponse(
        slots=[
            ForecastSlotResponse(
                datetime_text=slot.datetime_text,
                weather=slot.weather,
                temperature=slot.temperature,
                pressure_hpa=slot.pressure_hpa,
            )
            for slot in slots
        ]
    )
