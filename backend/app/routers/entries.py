"""/entries エンドポイントを定義するルーター。"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.diary_entry import DiaryEntryCreate, DiaryEntryResponse, DiaryEntryUpdate
from app.services import diary_service

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("", response_model=DiaryEntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(payload: DiaryEntryCreate, db: Session = Depends(get_db)) -> DiaryEntryResponse:
    """日記を保存する。同日の既存エントリーがあれば追記としてまとめる。"""
    entry = diary_service.create_or_append_entry(db, payload)
    return DiaryEntryResponse.model_validate(entry)


@router.get("", response_model=list[DiaryEntryResponse])
def list_entries(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
) -> list[DiaryEntryResponse]:
    """日記一覧を日付降順で取得する。start_date/end_dateクエリパラメータで期間を絞り込める。"""
    entries = diary_service.get_entries(db, start_date=start_date, end_date=end_date)
    return [DiaryEntryResponse.model_validate(entry) for entry in entries]


@router.get("/{entry_id}", response_model=DiaryEntryResponse)
def get_entry(entry_id: int, db: Session = Depends(get_db)) -> DiaryEntryResponse:
    """IDを指定して日記エントリーを1件取得する。"""
    entry = diary_service.get_entry_by_id(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された日記が見つかりません")
    return DiaryEntryResponse.model_validate(entry)


@router.put("/{entry_id}", response_model=DiaryEntryResponse)
def update_entry(entry_id: int, payload: DiaryEntryUpdate, db: Session = Depends(get_db)) -> DiaryEntryResponse:
    """日記エントリーを部分更新する(睡眠時間の後追い入力など)。リクエストで指定したフィールドのみ更新される。"""
    update_data = payload.model_dump(exclude_unset=True)
    entry = diary_service.update_entry(db, entry_id, update_data)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された日記が見つかりません")
    return DiaryEntryResponse.model_validate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db)) -> None:
    """日記エントリーを削除する。"""
    deleted = diary_service.delete_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定された日記が見つかりません")
