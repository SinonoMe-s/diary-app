"""diary_entries テーブルに対応する SQLAlchemy モデル。"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DiaryEntry(Base):
    """1日分の日記エントリーを表すモデル。

    requirements.md のテーブル設計に準拠する。
    keywords は JSON文字列(配列)として TEXT カラムに保存する。
    1日1レコードを基本とし、同日の追記は diary_text の結合で表現する。

    user_id は将来のマルチユーザー対応に備えたカラム(ログイン機能は未実装のため、
    現時点では固定値1のみを使用する)。一意制約も(user_id, entry_date)の組で持たせる。
    """

    __tablename__ = "diary_entries"
    __table_args__ = (UniqueConstraint("user_id", "entry_date", name="uq_diary_entries_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    diary_text: Mapped[str] = mapped_column(Text, nullable=False)
    mood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mood_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    weather: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pressure_hpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
