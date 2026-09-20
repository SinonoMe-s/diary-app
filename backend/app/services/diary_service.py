"""日記エントリーに関するDB操作をまとめたサービス層。"""

import json
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import DEFAULT_USER_ID
from app.models.diary_entry import DiaryEntry
from app.schemas.diary_entry import DiaryEntryCreate
from app.services import ai_analysis_service, user_settings_service, weather_service


def _resolve_mood_analysis(
    payload: DiaryEntryCreate,
) -> tuple[int | None, str | None, list[str] | None, str | None]:
    """保存する精神状態分析結果を決定する。

    mood_score等が1つでも手動指定されていれば、そちらを優先しGemini分析は行わない。
    すべて未指定の場合のみ、Gemini APIで自動分析する。
    """
    if any(
        value is not None
        for value in (payload.mood_score, payload.mood_label, payload.keywords, payload.ai_summary)
    ):
        return payload.mood_score, payload.mood_label, payload.keywords, payload.ai_summary

    analysis = ai_analysis_service.analyze_mood(payload.diary_text)
    if analysis is None:
        return None, None, None, None
    return analysis.mood_score, analysis.mood_label, analysis.keywords, analysis.summary


def _resolve_weather(db: Session, payload: DiaryEntryCreate) -> tuple[str | None, float | None]:
    """保存する天気・気圧を決定する。

    payloadで手動指定されていればそれを優先する。
    どちらも未指定の場合のみ、location_name(無ければuser_settingsのデフォルト地点)から自動取得する。
    自動取得に失敗した場合はNoneのまま(=空欄で保存)とし、日記保存自体は妨げない。
    """
    if payload.weather is not None or payload.pressure_hpa is not None:
        return payload.weather, payload.pressure_hpa

    settings_row = user_settings_service.get_or_create_settings(db)
    weather_info = weather_service.get_weather_info(
        location_name=payload.location_name,
        default_latitude=settings_row.latitude,
        default_longitude=settings_row.longitude,
    )
    if weather_info is None:
        return None, None
    return weather_info.weather, weather_info.pressure_hpa


def create_or_append_entry(db: Session, payload: DiaryEntryCreate) -> DiaryEntry:
    """日記を保存する。

    同日の既存エントリーがあれば diary_text を追記としてまとめ、
    mood_score等その他の項目は指定があれば上書きする。
    存在しなければ新規レコードを作成する。
    天気・気圧、およびmood_score等のAI分析結果は、payloadで手動指定が無ければ自動取得する。
    """
    target_date = payload.entry_date or date.today()
    now = datetime.now()
    weather, pressure_hpa = _resolve_weather(db, payload)
    mood_score, mood_label, keywords, ai_summary = _resolve_mood_analysis(payload)

    existing = db.execute(
        select(DiaryEntry).where(
            DiaryEntry.entry_date == target_date, DiaryEntry.user_id == DEFAULT_USER_ID
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.diary_text = f"{existing.diary_text}\n\n---\n\n{payload.diary_text}"
        if mood_score is not None:
            existing.mood_score = mood_score
        if mood_label is not None:
            existing.mood_label = mood_label
        if keywords is not None:
            existing.keywords = json.dumps(keywords, ensure_ascii=False)
        if ai_summary is not None:
            existing.ai_summary = ai_summary
        if weather is not None:
            existing.weather = weather
        if pressure_hpa is not None:
            existing.pressure_hpa = pressure_hpa
        if payload.sleep_hours is not None:
            existing.sleep_hours = payload.sleep_hours
        if payload.location_name is not None:
            existing.location_name = payload.location_name
        existing.updated_at = now
        db.commit()
        db.refresh(existing)
        return existing

    new_entry = DiaryEntry(
        user_id=DEFAULT_USER_ID,
        entry_date=target_date,
        diary_text=payload.diary_text,
        mood_score=mood_score,
        mood_label=mood_label,
        keywords=json.dumps(keywords, ensure_ascii=False) if keywords is not None else None,
        ai_summary=ai_summary,
        weather=weather,
        pressure_hpa=pressure_hpa,
        sleep_hours=payload.sleep_hours,
        location_name=payload.location_name,
        created_at=now,
        updated_at=now,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def get_entries(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[DiaryEntry]:
    """日記一覧を日付降順で取得する。start_date/end_dateで期間を絞り込める。"""
    stmt = select(DiaryEntry).where(DiaryEntry.user_id == DEFAULT_USER_ID)
    if start_date is not None:
        stmt = stmt.where(DiaryEntry.entry_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(DiaryEntry.entry_date <= end_date)
    stmt = stmt.order_by(DiaryEntry.entry_date.desc())
    return list(db.execute(stmt).scalars().all())


def get_entry_by_id(db: Session, entry_id: int) -> DiaryEntry | None:
    """IDを指定して日記エントリーを1件取得する。"""
    return db.get(DiaryEntry, entry_id)


def update_entry(db: Session, entry_id: int, update_data: dict[str, object]) -> DiaryEntry | None:
    """日記エントリーを部分更新する。

    update_data に含まれるフィールドのみを更新し、含まれないフィールドは変更しない
    (例: sleep_hoursだけを後から入力する、といった使い方を想定)。
    該当レコードが無い場合はNoneを返す。
    """
    entry = db.get(DiaryEntry, entry_id)
    if entry is None:
        return None

    for field, value in update_data.items():
        if field == "keywords":
            entry.keywords = json.dumps(value, ensure_ascii=False) if value is not None else None
        else:
            setattr(entry, field, value)

    entry.updated_at = datetime.now()
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry_id: int) -> bool:
    """日記エントリーを削除する。削除できた場合はTrue、該当レコードが無い場合はFalseを返す。"""
    entry = db.get(DiaryEntry, entry_id)
    if entry is None:
        return False
    db.delete(entry)
    db.commit()
    return True
