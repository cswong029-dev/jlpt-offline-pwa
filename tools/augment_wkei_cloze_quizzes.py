# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import random
from pathlib import Path

random.seed(57)
ROOT = Path(r"g:\我的雲端硬碟\Japanese(AI)\jlpt-offline-pwa")
VFILE = ROOT / "data" / "packs" / "wkei-vocab" / "vocab.json"
QFILE = ROOT / "data" / "packs" / "wkei-vocab" / "quizzes.json"

vocab = json.loads(VFILE.read_text(encoding="utf-8")).get("items", [])
base = json.loads(QFILE.read_text(encoding="utf-8"))
existing = base.get("items", [])
existing_ids = {q.get("id") for q in existing}

by_lv = {}
for v in vocab:
    by_lv.setdefault(v.get("level", "N5"), []).append(v)

def sample_wrong(level: str, correct: str):
    pool = [x.get("word", "") for x in by_lv.get(level, []) if x.get("word") and x.get("word") != correct]
    random.shuffle(pool)
    out = []
    seen = {correct}
    for p in pool:
        if p in seen:
            continue
        out.append(p)
        seen.add(p)
        if len(out) >= 3:
            break
    while len(out) < 3:
        out.append(f"誤用{len(out)+1}")
    return out

added = []
for v in vocab:
    wid = v.get("id")
    level = v.get("level", "N5")
    word = (v.get("word") or "").strip()
    if not word:
        continue
    qid = f"{wid}-q-cloze"
    if qid in existing_ids:
        continue
    wrong = sample_wrong(level, word)
    choices = [word] + wrong[:3]
    random.shuffle(choices)
    ci = choices.index(word)
    sentence = "昨日、私は（　）を見直しました。"
    added.append({
        "id": qid,
        "level": level,
        "section": "vocab",
        "jlptPart": "語彙・文脈",
        "type": "mc",
        "question": f"（語彙・文脈）次の文の（　）に入る最も適切な語はどれですか。\n{sentence}",
        "choices": choices,
        "correctIndex": ci,
        "ttsQuestion": sentence.replace("（　）", word),
        "explanation": f"正解是「{word}」。"
    })

base["items"] = existing + added
QFILE.write_text(json.dumps(base, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print("added", len(added), "total", len(base["items"]))
