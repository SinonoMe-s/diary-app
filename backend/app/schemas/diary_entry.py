"""日記エントリーのリクエスト/レスポンス用 Pydantic スキーマ。"""

import json
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DiaryEntryCreate(BaseModel):
    """日記保存時のリクエストボディ。

    フェーズ1ではAI分析・天気自動取得を行わないため、
    mood_score等は手動入力できる任意項目としている(フェーズ2以降で自動生成に置き換える)。
    """

    entry_date: date | None = Field(default=None, description="対象日。省略時は当日日付を使用する")
    diary_text: str = Field(min_length=1, description="日記本文")
    mood_score: int | None = Field(default=None, ge=-5, le=5, description="精神状態スコア(-5〜5)")
    mood_label: str | None = Field(default=None, description="簡易ラベル(例: 良好/普通/落ち込み)")
    keywords: list[str] | None = Field(default=None, description="状態に影響していそうなキーワード")
    ai_summary: str | None = Field(default=None, description="AIによる一言コメント")
    weather: str | None = Field(default=None, description="天気(手動指定時は自動取得より優先される)")
    pressure_hpa: float | None = Field(default=None, description="気圧(hPa)(手動指定時は自動取得より優先される)")
    sleep_hours: float | None = Field(default=None, ge=0, description="睡眠時間(時間、小数可)")
    location_name: str | None = Field(
        default=None, description="天気取得地点の地名。省略時はuser_settingsのデフォルト地点を使用する"
    )


class DiaryEntryUpdate(BaseModel):
    """日記編集時のリクエストボディ(部分更新)。

    指定されたフィールドのみを更新する。例: 睡眠時間だけを後から入力する、mood_scoreを手動で補正する、など。
    entry_date は1レコードを一意に識別するキーのため、このAPIでは変更しない。
    """

    diary_text: str | None = Field(default=None, min_length=1, description="日記本文")
    mood_score: int | None = Field(default=None, ge=-5, le=5, description="精神状態スコア(-5〜5)")
    mood_label: str | None = Field(default=None, description="簡易ラベル(例: 良好/普通/落ち込み)")
    keywords: list[str] | None = Field(default=None, description="状態に影響していそうなキーワード")
    ai_summary: str | None = Field(default=None, description="AIによる一言コメント")
    weather: str | None = Field(default=None, description="天気")
    pressure_hpa: float | None = Field(default=None, description="気圧(hPa)")
    sleep_hours: float | None = Field(default=None, ge=0, description="睡眠時間(時間、小数可)")
    location_name: str | None = Field(default=None, min_length=1, description="天気取得地点の地名")


class DiaryEntryResponse(BaseModel):
    """日記エントリーのレスポンス。"""

    id: int
    entry_date: date
    diary_text: str
    mood_score: int | None
    mood_label: str | None
    keywords: list[str]
    ai_summary: str | None
    weather: str | None
    pressure_hpa: float | None
    sleep_hours: float | None
    location_name: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("keywords", mode="before")
    @classmethod
    def parse_keywords(cls, value: object) -> list[str]:
        """DBにはJSON文字列で保存されているため、レスポンス生成時にリストへ変換する。"""
        if value is None:
            return []
        if isinstance(value, str):
            return json.loads(value)
        return value
