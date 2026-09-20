"""SQLAlchemyのエンジン・セッション・Baseクラスを定義するモジュール。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLiteはデフォルトで接続をスレッド間で共有できないため、FastAPI(複数リクエスト)から使う場合は無効化する
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """全モデルの基底クラス。"""


def get_db() -> Generator[Session, None, None]:
    """リクエストごとにDBセッションを提供し、処理後に必ずクローズする依存関係関数。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
