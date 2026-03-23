# -*- coding: utf-8 -*-
"""從 jlpt-vocab-api 的 data-source/db/n*.json 產生 wkei-vocab 擴充包。"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent / "jlpt-vocab-api-main" / "jlpt-vocab-api-main" / "data-source" / "db"
OUT = ROOT / "data" / "packs" / "wkei-vocab"

LEVEL_FILES = [(5, "N5", "n5.json"), (4, "N4", "n4.json"), (3, "N3", "n3.json"), (2, "N2", "n2.json"), (1, "N1", "n1.json")]


def load_rows() -> list[dict]:
    items: list[dict] = []
    for _num, jlpt, fname in LEVEL_FILES:
        path = REPO / fname
        if not path.exists():
            raise SystemExit(f"找不到來源檔：{path}")
        rows = json.loads(path.read_text(encoding="utf-8"))
        for i, row in enumerate(rows, start=1):
            wid = f"wkei-{jlpt}-{i:05d}"
            meaning_en = row.get("meaning") or ""
            items.append(
                {
                    "id": wid,
                    "level": jlpt,
                    "word": row.get("word") or "",
                    "reading": (row.get("furigana") or "").strip(),
                    "meaningEn": meaning_en,
                    "meaning": meaning_en,
                    "pos": "",
                    "audioWord": "",
                    "audioExample": "",
                    "exampleJa": "",
                    "exampleReading": "",
                    "exampleZh": "",
                }
            )
    return items


def build_quizzes(items: list[dict]) -> list[dict]:
    by_level: dict[str, list[dict]] = {}
    for it in items:
        by_level.setdefault(it["level"], []).append(it)

    readings_by_lv = {
        lv: [x["reading"] for x in lst if x.get("reading")]
        for lv, lst in by_level.items()
    }
    meanings_by_lv = {
        lv: [x["meaning"] for x in lst if x.get("meaning")]
        for lv, lst in by_level.items()
    }
    all_readings = [x["reading"] for x in items if x.get("reading")]
    all_meanings = [x["meaning"] for x in items if x.get("meaning")]
    words_by_lv = {lv: [x["word"] for x in lst if x.get("word")] for lv, lst in by_level.items()}

    quizzes: list[dict] = []

    cloze_templates = [
        "毎朝、（　）を確認してから学校へ行きます。",
        "先生の説明を聞いて、（　）の使い方が分かりました。",
        "週末にノートを見返して、（　）を復習しました。",
        "この文では、文脈に合う（　）を選ぶ必要があります。",
        "会話練習では、（　）を入れると意味が自然になります。",
        "読解問題で（　）を見つけたら、前後の文を確認しましょう。",
    ]

    def unique_sample(pool: list[str], correct: str, need: int) -> list[str]:
        out: list[str] = []
        seen = {correct}
        random.shuffle(pool)
        for p in pool:
            if p in seen or p == correct:
                continue
            seen.add(p)
            out.append(p)
            if len(out) >= need:
                break
        return out

    for it in items:
        lv = it["level"]
        wid = it["id"]
        word = it["word"]
        if it.get("reading"):
            correct = it["reading"]
            pool = readings_by_lv.get(lv, [])
            wrong = unique_sample(pool, correct, 3)
            if len(wrong) < 3:
                wrong.extend(unique_sample(all_readings, correct, 3 - len(wrong)))
            choices = [correct] + wrong[:3]
            random.shuffle(choices)
            ci = choices.index(correct)
            mean_line = it.get("meaning") or ""
            quizzes.append(
                {
                    "id": f"{wid}-q-read",
                    "level": lv,
                    "section": "vocab",
                    "jlptPart": "語彙・読み",
                    "type": "mc",
                    "question": f"（語彙・読み）請選出「{word}」的正確讀音。",
                    "choices": choices,
                    "correctIndex": ci,
                    "ttsQuestion": f"{word}",
                    "explanation": f"正解為「{correct}」。中文釋義：{mean_line}",
                }
            )
        if it.get("word"):
            correct = it["word"]
            pool = words_by_lv.get(lv, [])
            wrong = unique_sample(pool, correct, 3)
            if len(wrong) < 3:
                wrong.extend(unique_sample([x["word"] for x in items if x.get("word")], correct, 3 - len(wrong)))
            choices = [correct] + wrong[:3]
            random.shuffle(choices)
            ci = choices.index(correct)
            sentence = cloze_templates[(sum(ord(c) for c in correct) + len(correct)) % len(cloze_templates)]
            quizzes.append(
                {
                    "id": f"{wid}-q-cloze",
                    "level": lv,
                    "section": "vocab",
                    "jlptPart": "語彙・文脈",
                    "type": "mc",
                    "question": f"（語彙・文脈）次の文の（　）に入る最も適切な語はどれですか。\n{sentence}",
                    "choices": choices,
                    "correctIndex": ci,
                    "ttsQuestion": sentence.replace("（　）", correct),
                    "explanation": f"正解是「{correct}」。請先讀完整句子，再用語意判斷最合適詞彙。",
                }
            )
        elif it.get("meaning"):
            correct = it["meaning"]
            pool = meanings_by_lv.get(lv, [])
            wrong = unique_sample(pool, correct, 3)
            if len(wrong) < 3:
                wrong.extend(unique_sample(all_meanings, correct, 3 - len(wrong)))
            choices = [correct] + wrong[:3]
            random.shuffle(choices)
            ci = choices.index(correct)
            quizzes.append(
                {
                    "id": f"{wid}-q-mean",
                    "level": lv,
                    "section": "vocab",
                    "jlptPart": "語彙・語彙",
                    "type": "mc",
                    "question": f"（語彙・語彙）請選出「{word}」的正確意思。",
                    "choices": choices,
                    "correctIndex": ci,
                    "ttsQuestion": word,
                    "explanation": f"「{word}」的意思為：{correct}。",
                }
            )

    return quizzes


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    items = load_rows()
    vocab_out = {"version": 1, "packId": "wkei-vocab", "items": items}
    (OUT / "vocab.json").write_text(
        json.dumps(vocab_out, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    quizzes = build_quizzes(items)
    quiz_out = {"version": 1, "packId": "wkei-vocab", "items": quizzes}
    (OUT / "quizzes.json").write_text(
        json.dumps(quiz_out, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"vocab: {len(items)} 筆 → {OUT / 'vocab.json'}")
    print(f"quizzes: {len(quizzes)} 題 → {OUT / 'quizzes.json'}")
    print("接著請執行：python tools/translate_wkei_to_zh_tw.py（將釋義改為繁中並重建語彙題）")


if __name__ == "__main__":
    main()
