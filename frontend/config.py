"""フロントエンドの設定を管理するモジュール。"""

import os

from dotenv import load_dotenv

load_dotenv()

# バックエンド(FastAPI)のベースURL
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
