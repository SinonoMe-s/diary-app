# 日記×AI精神状態分析アプリ

日々の日記をAI(Gemini)が分析し、気分・天気・気圧などのデータから心身の傾向を振り返れるアプリです。

## 構成

- `backend/`: FastAPI(API・DB・AI分析・天気取得)
- `frontend/`: Streamlit(ホーム・日記・一覧・傾向・AI相談・設定の各画面)

## 起動方法

### バックエンド(FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # .envを作成し、下記の環境変数を設定
uvicorn app.main:app --reload --port 8000
```

### フロントエンド(Streamlit)

```bash
cd frontend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # .envを作成し、下記の環境変数を設定
streamlit run app.py
```

## 環境変数

### backend/.env

| キー名 | 用途 |
|---|---|
| `DATABASE_URL` | SQLiteのDB接続文字列 |
| `GEMINI_API_KEY` | Gemini APIキー(日記のAI分析・AI相談で使用) |
| `WEATHER_API_KEY` | OpenWeatherMap APIキー(天気・気圧・天気予報の取得で使用) |
| `HOME_LOCATION_NAME` | 自宅地域の初期値(地名) |
| `HOME_LATITUDE` | 自宅地域の初期値(緯度) |
| `HOME_LONGITUDE` | 自宅地域の初期値(経度) |

### frontend/.env

| キー名 | 用途 |
|---|---|
| `API_BASE_URL` | バックエンド(FastAPI)のベースURL |
