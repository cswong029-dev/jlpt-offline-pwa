# -*- coding: utf-8 -*-
"""由 builtin-grammar/grammar.json 產生 JLPT 式文法填空題（quizzes.json）。"""
from __future__ import annotations

import json
import random
import re
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
    token_pool_by_lv: dict[str, list[str]] = defaultdict(list)
    for g in items:
        gid = g["id"]
        lv = g["level"]
        for ex in g.get("examples") or []:
            ja = (ex.get("ja") or "").strip()
            if ja:
                pool_by_lv[lv].append((gid, ja))
        title = (g.get("title") or "").strip()
        token = re.split(r"[／・（(\\s]", title)[0].strip()
        if token:
            token_pool_by_lv[lv].append(token)

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
            token = re.split(r"[／・（(\\s]", title)[0].strip()
            sent = ja
            if token and token in sent:
                sent = sent.replace(token, "（　）", 1)
            elif "。" in sent:
                sent = sent.replace("。", "（　）。", 1)
            else:
                sent = sent + "（　）"

            wrong = []
            pool = token_pool_by_lv.get(lv, [])
            random.shuffle(pool)
            seenw = {token}
            for w in pool:
                w = (w or "").strip()
                if not w or w in seenw:
                    continue
                seenw.add(w)
                wrong.append(w)
                if len(wrong) >= 3:
                    break
            pad = 0
            while len(wrong) < 3:
                pad += 1
                wrong.append(f"誤用{pad}")
            choices = [token] + wrong[:3]
            random.shuffle(choices)
            ci = choices.index(token)
            zh = ex.get("zh") or ""
            qn += 1
            quizzes.append(
                {
                    "id": f"{g['id']}-gq-{qn:04d}",
                    "level": lv,
                    "section": "grammar",
                    "jlptPart": "文法・文の文法形式",
                    "type": "mc",
                    "question": f"（文法・文の文法形式）次の文の（　）に入る最も適切な文法はどれですか。\n{sent}",
                    "choices": choices,
                    "correctIndex": ci,
                    "ttsQuestion": sent.replace("（　）", token),
                    "explanation": f"正解是「{token}」。{zh}",
                }
            )

    out = {"version": 1, "packId": "builtin-grammar", "items": quizzes}
    QFILE.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"文法題 {len(quizzes)} 題 → {QFILE}")


if __name__ == "__main__":
    main()
