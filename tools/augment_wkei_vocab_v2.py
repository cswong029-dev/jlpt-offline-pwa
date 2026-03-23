from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "data" / "packs" / "wkei-vocab" / "vocab.json"
QUIZ_PATH = ROOT / "data" / "packs" / "wkei-vocab" / "quizzes.json"


ADVERB_KEYWORDS = [
    # common adverb/time words in JLPT lists
    "always",
    "often",
    "sometimes",
    "usually",
    "every ",
    "every",
    "sometime",  # just in case
    "probably",
    "maybe",
    "exactly",
    "almost",
    "already",
    "still",
    "again",
    "together",
    "now",
    "today",
    "tomorrow",
    "yesterday",
    "next ",
    "later",
    "soon",
    "quickly",
    "slowly",
    "very",
    "quite",
    "just",
    "still",
    "more",
    "less",
]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def is_likely_adverb(meaning_en: str) -> bool:
    s = norm(meaning_en).lower()
    if not s:
        return False
    return any(k in s for k in ADVERB_KEYWORDS)


def estimate_pitch_accent(reading: str) -> str:
    # Very rough, mora-count based heuristic (offline).
    r = norm(reading)
    if not r:
        return "未標註"

    # Remove small vowels / contracted marks / long mark-ish.
    # This is not a correct pitch-accent algorithm; we label it as 推測.
    mora_like = re.sub(r"[ゃゅょぁぃぅぇぉャュョァィゥェォー]", "", r)
    count = len(mora_like.replace("ー", ""))

    # Treat short readings as low-entropy "single mora" etc.
    if count <= 1:
        return "推測 單拍詞"
    if count == 2:
        return "推測 頭高型(1)"
    return "推測 平板型(0)"


def pick_pair_templates(word: str, meaning_cn: str, meaning_en: str, pos: str) -> tuple[str, str, str, str]:
    key = sum(ord(c) for c in (word + meaning_cn + meaning_en)) % 6
    men = meaning_en.lower()
    mcn = meaning_cn

    if pos == "副詞":
        pairs = [
            (
                f"{word}日本語を勉強しています。",
                f"{word}復習すると、だんだん分かるようになります。",
                f"我{word}在學日文。",
                f"{word}複習的話，會漸漸變得懂。"
            ),
            (
                f"{word}時間があれば、図書館へ行きます。",
                f"先生の話を{word}聞くことが大切です。",
                f"{word}有時間的話我會去圖書館。",
                f"{word}聽老師的說明很重要。"
            ),
            (
                f"{word}この表現は会話でよく使います。",
                f"{word}メモを見返して確認しましょう。",
                f"{word}這個表達在會話裡常用。",
                f"{word}把筆記拿出來再確認吧。"
            ),
            (
                f"{word}練習を続ければ、自然に話せるようになります。",
                f"{word}語彙を増やすと読解が楽になります。",
                f"{word}持續練習就能更自然地說。",
                f"{word}增加詞彙後，閱讀會更輕鬆。"
            ),
            (
                f"{word}先生に質問すると理解が深まります。",
                f"{word}短い文から作ると覚えやすいです。",
                f"{word}向老師提問會加深理解。",
                f"{word}先造短句會比較好記。"
            ),
            (
                f"{word}音読して、発音を確認しましょう。",
                f"{word}聞き取り練習も一緒に行いましょう。",
                f"{word}朗讀並確認發音吧。",
                f"{word}也一起做聽力練習吧。"
            ),
        ]
        return pairs[key]

    # Color / weather-like adjectives
    if "black" in men or "黑" in mcn:
        return (
            "田中先生の髪は黒いです。",
            "このかばんは黒なので、汚れが目立ちません。",
            "田中老師的頭髮是黑色的。",
            "這個包包是黑色的，所以不容易看出髒污。"
        )
    if "white" in men or "白" in mcn:
        return (
            "冬になると山の上は白くなります。",
            "白いシャツは清潔な印象があります。",
            "到了冬天，山上會變白。",
            "白襯衫給人整潔的印象。"
        )
    if "red" in men or "紅" in mcn or "赤" in word:
        return (
            "信号が赤なので、ここで止まりましょう。",
            "赤い花が庭にたくさん咲いています。",
            "紅燈亮了，所以在這裡停下來吧。",
            "庭院裡開了很多紅花。"
        )

    # Time-related nouns/adverbs
    if any(k in men for k in ["morning", "night", "today", "tomorrow", "yesterday", "week", "month", "year"]):
        return (
            f"{word}は図書館で日本語を勉強します。",
            f"{word}、家族といっしょに食事をします。",
            f"{word}我會在圖書館學日文。",
            f"{word}我會和家人一起吃飯。"
        )

    # Place-related
    if any(k in men for k in ["station", "school", "hospital", "company", "park", "library", "kitchen", "room"]):
        return (
            f"今日は{word}で友だちと会います。",
            f"{word}の近くに新しい店ができました。",
            f"今天我會在{word}和朋友見面。",
            f"{word}附近開了一間新店。"
        )

    # Verb-like meanings
    if men.startswith("to "):
        return (
            f"この場面では「{word}」という動詞を使います。",
            f"会話で「{word}」を自然に言えるように練習しましょう。",
            f"在這個情境中會使用動詞「{word}」。",
            f"請練習在會話中自然地說出「{word}」。"
        )

    # Food/drink
    if any(k in men for k in ["tea", "coffee", "milk", "rice", "bread", "meat", "fish", "fruit", "vegetable"]):
        eat_words = ["rice", "bread", "meat", "fish", "fruit", "vegetable", "egg", "curry", "food"]
        is_eat = any(k in men for k in eat_words)
        verb_ja = "食べました" if is_eat else "飲みました"
        verb_zh = "吃了" if is_eat else "喝了"
        return (
            f"朝ごはんに{word}を{verb_ja}。",
            f"この店の{word}はとても人気があります。",
            f"早餐我{verb_zh}{word}。",
            f"這家店的{word}很受歡迎。"
        )

    # Generic but safe (quoted lexical context, avoid absurd actions)
    pairs = [
        (
            f"授業で「{word}」という言葉を習いました。",
            f"先生は「{word}」の意味を例文で説明しました。",
            f"課堂上學到了「{word}」這個詞。",
            f"老師用例句說明了「{word}」的意思。"
        ),
        (
            f"会話の中で「{word}」が出てきました。",
            f"ノートに「{word}」を書いて復習しました。",
            f"對話中出現了「{word}」。",
            f"我把「{word}」寫在筆記上複習。"
        ),
        (
            f"読解問題で「{word}」を見つけました。",
            f"辞書で「{word}」の使い方を確認しました。",
            f"我在閱讀題中看到了「{word}」。",
            f"我用字典確認了「{word}」的用法。"
        ),
        (
            f"「{word}」を覚えると、文の意味が分かりやすくなります。",
            f"次は「{word}」を使って短い文を作ってみましょう。",
            f"記住「{word}」後更容易理解句子。",
            f"下一步試著用「{word}」造短句。"
        ),
        (
            f"先生は「{word}」と似た言葉の違いも教えてくれました。",
            f"「{word}」を声に出して読むと覚えやすいです。",
            f"老師也教了「{word}」和近義詞的差異。",
            f"把「{word}」唸出來會更好記。"
        ),
        (
            f"今日は「{word}」を中心に語彙練習をしました。",
            f"明日は「{word}」を使う会話練習をします。",
            f"今天以「{word}」為中心做了詞彙練習。",
            f"明天會做使用「{word}」的會話練習。"
        ),
    ]
    return pairs[key]


def main() -> None:
    if not VOCAB_PATH.exists():
        raise SystemExit(f"找不到 {VOCAB_PATH}")

    data = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    items: list[dict] = data.get("items") or []

    changed = 0

    for it in items:
        word = norm(it.get("word", ""))
        reading = norm(it.get("reading", ""))
        meaning_cn = norm(it.get("meaning", ""))
        meaning_en = norm(it.get("meaningEn", "")) or meaning_cn

        pos = "副詞" if is_likely_adverb(meaning_en) else (it.get("pos") or "")

        # Two useful example sentences per vocab.
        ja1, ja2, zh1, zh2 = pick_pair_templates(word, meaning_cn, meaning_en, pos)
        examples = [
            {
                "ja": ja1,
                "reading": reading,
                "zh": zh1,
                "audioPhrase": "",
            },
            {
                "ja": ja2,
                "reading": reading,
                "zh": zh2,
                "audioPhrase": "",
            },
        ]

        # Overwrite bland placeholders with meaningful examples.
        ex_old = (it.get("exampleJa") or "").strip()
        if (not ex_old) or ("「" in ex_old and "使います" in ex_old):
            it["exampleJa"] = ja1
            it["exampleReading"] = reading
            it["exampleZh"] = zh1
            changed += 1
        it["examples"] = examples
        changed += 1

        if not (it.get("pos") or "").strip() and pos:
            it["pos"] = pos
            changed += 1

        # Accent (rough estimate). Store explicitly so UI can show it.
        if not (it.get("pitchAccent") or "").strip() and (reading or word):
            it["pitchAccent"] = estimate_pitch_accent(reading or word)
            changed += 1

    VOCAB_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("updated vocab items (heuristic fill):", changed)

    # Rebuild quizzes using the existing build_quizzes() logic.
    # Import from the existing generator script for consistent question format.
    import sys

    sys.path.insert(0, str(ROOT / "tools"))
    from build_wkei_pack import build_quizzes  # type: ignore

    quiz_items = build_quizzes(items)
    QUIZ_PATH.write_text(json.dumps({"version": 1, "packId": "wkei-vocab", "items": quiz_items}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("rebuilt quizzes:", len(quiz_items))


if __name__ == "__main__":
    main()

