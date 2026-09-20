"""AI相談チャット機能のリクエスト/レスポンス用 Pydantic スキーマ。"""

from pydantic import BaseModel, Field


class ConsultChatMessage(BaseModel):
    """会話履歴の1メッセージ(フロントエンドのst.session_stateから渡される)。"""

    role: str = Field(description="'user' または 'model'")
    content: str


class ConsultRequest(BaseModel):
    """AI相談のリクエスト。"""

    message: str = Field(min_length=1, description="ユーザーからの質問・相談内容")
    history: list[ConsultChatMessage] = Field(default_factory=list, description="これまでの会話履歴")


class ConsultResponse(BaseModel):
    """AI相談のレスポンス。"""

    reply: str
