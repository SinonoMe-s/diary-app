"""アプリケーション設定を管理するモジュール。

.env ファイルから環境変数を読み込み、型安全な設定オブジェクトとして提供する。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数から読み込むアプリケーション設定。"""

    database_url: str = "sqlite:///./diary.db"
    gemini_api_key: str | None = None
    weather_api_key: str | None = None
    home_location_name: str | None = None
    home_latitude: float | None = None
    home_longitude: float | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,  # .envで未設定(空文字)の項目はNone扱いにする
    )


@lru_cache
def get_settings() -> Settings:
    """設定オブジェクトをキャッシュして返す。"""
    return Settings()
