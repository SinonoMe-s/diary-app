"""FastAPIアプリケーションのエントリーポイント。"""

from fastapi import FastAPI

from app.database import Base, SessionLocal, engine
from app.routers import ai, entries, settings
from app.services import user_settings_service

# アプリ起動時にテーブルが無ければ作成する(フェーズ1ではAlembic等のマイグレーションは未導入)
Base.metadata.create_all(bind=engine)

# user_settingsが空の場合、.envの値(無ければダミー値)で自宅地域を初期シードする
with SessionLocal() as _db:
    user_settings_service.get_or_create_settings(_db)

app = FastAPI(title="日記×AI精神状態分析アプリ API", version="0.1.0")

app.include_router(entries.router)
app.include_router(settings.router)
app.include_router(ai.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """ヘルスチェック用エンドポイント。"""
    return {"status": "ok"}
