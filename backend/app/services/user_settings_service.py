"""ユーザー設定(自宅地域)に関するDB操作をまとめたサービス層。

個人利用アプリのため、設定レコードは常にid=1の1件のみを扱うシングルトンとする。
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.constants import DEFAULT_USER_ID
from app.models.user_settings import UserSettings
from app.services import weather_service

SETTINGS_ID = 1

# .envで自宅地域が未設定の場合に使う仮の初期値(東京都庁)。
# 個人情報をコードにハードコードしないため、実際の自宅地域は起動後にPUT /settingsで変更する想定。
DEFAULT_LOCATION_NAME = "東京都庁(初期値・要変更)"
DEFAULT_LATITUDE = 35.6895
DEFAULT_LONGITUDE = 139.6917


def get_or_create_settings(db: Session) -> UserSettings:
    """設定レコードを取得する。存在しない場合は.envの値、無ければダミー値で初期シードする。"""
    settings_row = db.get(UserSettings, SETTINGS_ID)
    if settings_row is not None:
        return settings_row

    app_settings = get_settings()
    now = datetime.now()
    settings_row = UserSettings(
        id=SETTINGS_ID,
        user_id=DEFAULT_USER_ID,
        location_name=app_settings.home_location_name or DEFAULT_LOCATION_NAME,
        latitude=app_settings.home_latitude if app_settings.home_latitude is not None else DEFAULT_LATITUDE,
        longitude=app_settings.home_longitude if app_settings.home_longitude is not None else DEFAULT_LONGITUDE,
        created_at=now,
        updated_at=now,
    )
    db.add(settings_row)
    db.commit()
    db.refresh(settings_row)
    return settings_row


def update_settings(db: Session, update_data: dict[str, object]) -> UserSettings:
    """設定を更新する。

    location_nameのみが指定され、latitude/longitudeが指定されない場合は、
    weather_serviceのジオコーディングで緯度経度を自動補完する。
    ジオコーディングに失敗した場合はValueErrorを送出する(呼び出し側で400エラーに変換する想定)。
    """
    settings_row = get_or_create_settings(db)

    new_location_name = update_data.get("location_name")
    if new_location_name is not None and "latitude" not in update_data and "longitude" not in update_data:
        geocoded = weather_service.geocode_location(new_location_name)
        if geocoded is None:
            raise ValueError(
                f"地名 '{new_location_name}' の位置情報を取得できませんでした。緯度経度を直接指定してください。"
            )
        update_data = dict(update_data)
        update_data["latitude"], update_data["longitude"] = geocoded

    for field, value in update_data.items():
        setattr(settings_row, field, value)
    settings_row.updated_at = datetime.now()
    db.commit()
    db.refresh(settings_row)
    return settings_row
