# -*- coding: utf-8 -*-
"""
將 wkei-vocab/vocab.json 的釋義由英文改為繁體中文，並保留原文於 meaningEn。
完成後自動重建語彙測驗（quizzes.json）。

用法（需先 pip install -r tools/requirements-tools.txt）：
  python tools/translate_wkei_to_zh_tw.py
  python tools/translate_wkei_to_zh_tw.py --resume   # 接續未完成的對照表
  python tools/translate_wkei_to_zh_tw.py --max 500  # 僅翻譯前 500 個「唯一釋義」（測試用）

若 Google 暫時阻擋，請稍後再執行 --resume。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "data" / "packs" / "wkei-vocab" / "vocab.json"
MAP_PATH = ROOT / "data" / "packs" / "wkei-vocab" / "_meaning_en_to_zh.json"


def load_translator():
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print("請先執行: pip install -r tools/requirements-tools.txt", file=sys.stderr)
        sys.exit(1)
    return GoogleTranslator(source="en", target="zh-TW")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true", help="從已存對照表接續，只翻譯尚未出現的英文")
    ap.add_argument("--max", type=int, default=0, help="最多處理幾個「唯一英文釋義」（0=全部）")
    args = ap.parse_args()

    if not VOCAB_PATH.exists():
        print(f"找不到 {VOCAB_PATH}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    items = data.get("items") or []

    en_to_zh: dict[str, str] = {}
    if args.resume and MAP_PATH.exists():
        en_to_zh = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    translator = load_translator()

    unique_en: list[str] = []
    seen = set()
    for it in items:
        raw = (it.get("meaningEn") or it.get("meaning") or "").strip()
        if not raw:
            continue
        if raw in seen:
            continue
        seen.add(raw)
        unique_en.append(raw)

    pending = [e for e in unique_en if e not in en_to_zh]
    if args.max > 0:
        pending = pending[: args.max]

    print(f"唯一英文釋義共 {len(unique_en)}；待翻譯 {len(pending)} 筆")

    for i, en in enumerate(pending):
        try:
            zh = translator.translate(en)
            en_to_zh[en] = zh
        except Exception as ex:
            print(f"[{i+1}/{len(pending)}] 失敗：{en[:50]}… → {ex}")
            time.sleep(2.0)
            continue
        if (i + 1) % 20 == 0:
            MAP_PATH.write_text(
                json.dumps(en_to_zh, ensure_ascii=False, indent=0), encoding="utf-8"
            )
            print(f"  已翻譯 {i+1}/{len(pending)}，已寫入檢查點")
        time.sleep(0.12)

    MAP_PATH.write_text(json.dumps(en_to_zh, ensure_ascii=False, indent=0), encoding="utf-8")

    for it in items:
        if not (it.get("meaningEn") or "").strip() and (it.get("meaning") or "").strip():
            it["meaningEn"] = it["meaning"]
        en = (it.get("meaningEn") or "").strip()
        if en and en in en_to_zh:
            it["meaning"] = en_to_zh[en]

    VOCAB_PATH.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"已更新 {VOCAB_PATH}")

    sys.path.insert(0, str(ROOT / "tools"))
    from build_wkei_pack import OUT as WKEI_OUT, build_quizzes

    quiz_items = build_quizzes(items)
    quiz_out = {"version": 1, "packId": "wkei-vocab", "items": quiz_items}
    out_q = WKEI_OUT / "quizzes.json"
    out_q.write_text(
        json.dumps(quiz_out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"已重建 {out_q}（{len(quiz_items)} 題）")


if __name__ == "__main__":
    main()
