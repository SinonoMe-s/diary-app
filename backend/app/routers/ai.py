"""/ai エンドポイントを定義するルーター(AI相談チャット機能)。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.consult import ConsultRequest, ConsultResponse
from app.services import consult_service
from app.services.consult_service import ChatTurn, ConsultRateLimitError

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/consult", response_model=ConsultResponse)
def consult(payload: ConsultRequest, db: Session = Depends(get_db)) -> ConsultResponse:
    """直近30日分の日記データをコンテキストとして、Geminiに相談メッセージを送り回答を取得する。"""
    history = [ChatTurn(role=turn.role, content=turn.content) for turn in payload.history]
    try:
        reply = consult_service.generate_reply(db, payload.message, history)
    except ConsultRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Gemini APIのレート制限に達しました。しばらく時間をおいてから再度お試しください。",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return ConsultResponse(reply=reply)
