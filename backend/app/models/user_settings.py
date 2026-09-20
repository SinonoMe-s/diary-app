"""user_settings テーブルに対応する SQLAlchemy モデル。

個人利用アプリのため、設定は常に1レコード(id=1)のみを保持するシングルトンとして扱う。
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserSettings(Base):
    """自宅地域(デフォルトの天気取得地点)を保持する設定モデル。

    user_id は将来のマルチユーザー対応に備えたカラム(ログイン機能は未実装のため、
    現時点では固定値1のみを使用する)。
    """

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    location_name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
