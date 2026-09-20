# プロジェクトルール

## 概要
チャット形式で日記を書くと、AI(Gemini)が精神状態を分析し、天気・気圧・睡眠時間などのコンディション情報と一緒に記録するWebアプリ。
詳細要件は requirements.md、参考UI/UXは reference_mitate.md を参照すること。

## 技術スタック(固定)
- バックエンド: FastAPI (Python)
- DB: SQLite + SQLAlchemy(またはSQLModel)
- AI分析: Gemini API
- 天気・気圧取得: 気象庁API または OpenWeatherMap API
- フロントエンド: 初期はStreamlit、または将来的にReact等
- 個人利用専用。認証機能・課金機能は実装しない

## コーディング規約
- コメント・docstringは日本語で書く
- 変数名・関数名は英語(スネークケース)
- 型ヒントを必ず付ける
- 1ファイルが肥大化しないよう、機能単位でファイルを分ける(例: routers/, models/, services/)
- .envファイルでAPIキー(Gemini APIキー、天気APIキー)を管理し、コードに直書きしない

## 開発の進め方
- requirements.mdの「開発フェーズ」に従い、フェーズごとに実装する
- 1フェーズ完了ごとに、簡単な動作確認手順を示す
- 大きな変更や新規ファイル作成の前に、まず実装方針を簡潔に説明してから着手する
- 不明な仕様があれば、勝手に決めずに確認を挟む

## データモデル(参考)
requirements.mdの diary_entries テーブル定義に準拠すること。
- mood_score, mood_label, keywords, ai_summary は Gemini API のレスポンスから生成する
- weather, pressure_hpa は外部APIから自動取得する
- sleep_hours は当面手動入力とする
