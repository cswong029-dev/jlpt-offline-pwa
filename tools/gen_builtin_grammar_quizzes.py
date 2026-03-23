# -*- coding: utf-8 -*-
"""由 builtin-grammar/grammar.json 產生 JLPT 式文法選句題（quizzes.json）。"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

random.seed(43)

ROOT = Path(__file__).resolve().parents[1]
GFILE = ROOT / "data" / "packs" / "builtin-grammar" / "grammar.json"
QFILE = ROOT / "data" / "packs" / "builtin-grammar" / "quizzes.json"


def main() -> None:
    data = json.loads(GFILE.read_text(encoding="utf-8"))
    items = data.get("items") or []

    pool_by_lv: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for g in items:
        gid = g["id"]
        lv = g["level"]
        for ex in g.get("examples") or []:
            ja = (ex.get("ja") or "").strip()
            if ja:
                pool_by_lv[lv].append((gid, ja))

    all_ja = [(g["id"], g["level"], ex.get("ja", "").strip()) for g in items for ex in (g.get("examples") or [])]
    all_ja = [(a, b, c) for a, b, c in all_ja if c]

    quizzes: list[dict] = []
    qn = 0
    for g in items:
        lv = g["level"]
        title = g.get("title") or ""
        for ex in g.get("examples") or []:
            ja = (ex.get("ja") or "").strip()
            if not ja:
                continue
            wrong_src = [t[1] for t in pool_by_lv[lv] if t[0] != g["id"] and t[1] != ja]
            if len(wrong_src) < 3:
                wrong_src = [x[2] for x in all_ja if x[0] != g["id"] and x[2] != ja]
            random.shuffle(wrong_src)
            wrong = []
            seenw = {ja}
            for w in wrong_src:
                if w in seenw:
                    continue
                seenw.add(w)
                wrong.append(w)
                if len(wrong) >= 3:
                    break
            pad = 0
            while len(wrong) < 3:
                pad += 1
                w = ja.replace("。", "…") + "（誤" + str(pad) + "）"
                if w not in seenw:
                    seenw.add(w)
                    wrong.append(w)
            choices = [ja] + wrong[:3]
            random.shuffle(choices)
            ci = choices.index(ja)
            zh = ex.get("zh") or ""
            qn += 1
            quizzes.append(
                {
                    "id": f"{g['id']}-gq-{qn:04d}",
                    "level": lv,
                    "section": "grammar",
                    "jlptPart": "文法・文の文法形式",
                    "type": "mc",
                    "question": f"（文法・文の文法形式）【{title}】請選出正確的句子。",
                    "choices": choices,
                    "correctIndex": ci,
                    "ttsQuestion": ja,
                    "explanation": f"正解反映「{title}」的用法。例句說明：{zh}",
                }
            )

    out = {"version": 1, "packId": "builtin-grammar", "items": quizzes}
    QFILE.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"文法題 {len(quizzes)} 題 → {QFILE}")


if __name__ == "__main__":
    main()
