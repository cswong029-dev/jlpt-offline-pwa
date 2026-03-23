# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(r"g:\我的雲端硬碟\Japanese(AI)\jlpt-offline-pwa")
RFILE = ROOT / "data" / "packs" / "graded-reading" / "reading.json"

obj = json.loads(RFILE.read_text(encoding="utf-8"))
items = obj.get("items", [])
ids = {x.get("id") for x in items}

def mk(level: str, i: int):
    if level == "N5":
        ja = f"きょうは いい てんき です。わたし は がっこう で にほんご を べんきょう します。ともだち と はなします。({i})"
        rd = f"きょうは いい てんき です。わたし は がっこう で にほんご を べんきょう します。ともだち と はなします。({i})"
        zh = f"今天天氣很好。我在學校學日文，也和朋友聊天。（N5-{i}）"
        q = {
            "question": "文中提到在哪裡學日文？",
            "choices": ["學校", "車站", "家裡", "公園"],
            "correctIndex": 0,
            "explanation": "句中有「がっこうで」。"
        }
        return {
            "id": f"gr-n5-auto-{i:03d}",
            "level": "N5",
            "title": f"N5 短文練習 {i}",
            "passageJa": ja,
            "passageReading": rd,
            "passageZh": zh,
            "questions": [q]
        }
    ja = f"来月の試験に向けて、私は毎日計画を立てて勉強しています。授業のあと図書館で復習し、分からない点は先生に質問するようにしています。週末には一週間の学習内容をまとめ、次の目標を確認します。({i})"
    rd = f"らいげつのしけんにむけて、わたしはまいにちけいかくをたててべんきょうしています。じゅぎょうのあととしょかんでふくしゅうし、わからないてんはせんせいにしつもんするようにしています。しゅうまつにはいっしゅうかんのがくしゅうないようをまとめ、つぎのもくひょうをかくにんします。({i})"
    zh = f"為了下個月考試，我每天規劃並學習。下課後在圖書館複習，不懂就問老師。週末整理一週內容並確認下個目標。（N4-{i}）"
    q = {
        "question": "作者週末會做什麼？",
        "choices": ["整理一週學習內容", "整天睡覺", "只看電影", "不讀書"],
        "correctIndex": 0,
        "explanation": "文中寫到週末會整理學習內容。"
    }
    return {
        "id": f"gr-n4-auto-{i:03d}",
        "level": "N4",
        "title": f"N4 閱讀練習 {i}",
        "passageJa": ja,
        "passageReading": rd,
        "passageZh": zh,
        "questions": [q]
    }

# add N5 up to 100 autos
for i in range(1, 101):
    nid = f"gr-n5-auto-{i:03d}"
    if nid not in ids:
        items.append(mk("N5", i))
        ids.add(nid)

# add N4 up to 50 autos
for i in range(1, 51):
    nid = f"gr-n4-auto-{i:03d}"
    if nid not in ids:
        items.append(mk("N4", i))
        ids.add(nid)

obj["items"] = items
RFILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("reading items:", len(items))
