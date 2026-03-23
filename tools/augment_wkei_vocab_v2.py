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

        # Example sentences
        if pos == "副詞":
            ja = f"{word}、わたしはにほんごをべんきょうします。"
        else:
            ja = f"わたしは「{word}」を使います。"

        zh = f"例句翻譯（參考）：{meaning_cn}" if meaning_cn else "例句翻譯（參考）"

        # Fill missing fields only (avoid overwriting any richer future data).
        if not (it.get("exampleJa") or "").strip():
            it["exampleJa"] = ja
            changed += 1
        if not (it.get("exampleReading") or "").strip():
            it["exampleReading"] = reading
        if not (it.get("exampleZh") or "").strip():
            it["exampleZh"] = zh
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

