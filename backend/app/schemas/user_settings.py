"""ユーザー設定(自宅地域)のリクエスト/レスポンス用 Pydantic スキーマ。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserSettingsUpdate(BaseModel):
    """設定更新時のリクエストボディ(部分更新)。

    location_nameのみを指定した場合、緯度経度はジオコーディングにより自動補完される。
    latitude/longitudeを直接指定した場合はその値がそのまま使われる。
    """

    location_name: str | None = Field(default=None, min_length=1, description="自宅地域の地名")
    latitude: float | None = Field(default=None, ge=-90, le=90, description="緯度")
    longitude: float | None = Field(default=None, ge=-180, le=180, description="経度")


class UserSettingsResponse(BaseModel):
    """ユーザー設定のレスポンス。"""

    id: int
    location_name: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
