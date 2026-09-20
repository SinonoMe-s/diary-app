"""mood_score(-5〜+5)を画面表示用の星評価に変換するユーティリティ。

DBに保存されているmood_score自体は変更せず、画面表示のみ★1〜★5の星評価に変換する。
バックエンドのAPI・スキーマは変更しない(表示側のみで完結させる)。
"""

MAX_STARS = 5


def mood_score_to_stars(mood_score: int | None) -> str | None:
    """mood_score(-5〜+5)を星評価(★1〜★5)の文字列に変換する。

    変換式: 表示用星数 = round((mood_score + 5) / 2)(四捨五入。例: mood_score=0 → ★3)
    mood_scoreがNone(AI分析結果が無い等)の場合はNoneを返す。
    """
    if mood_score is None:
        return None

    # Python標準のround()は偶数への丸め(銀行丸め)のため、
    # 0.5を加えてint()で切り捨てることで四捨五入(0.5は常に切り上げ)にする。
    # mood_scoreは-5〜5のため (mood_score + 5) / 2 は常に0以上で成立する。
    star_count = int((mood_score + 5) / 2 + 0.5)
    star_count = max(0, min(MAX_STARS, star_count))
    return "★" * star_count + "☆" * (MAX_STARS - star_count)
