from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "data" / "packs" / "wkei-vocab" / "vocab.json"


def norm(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def skeleton(s: str) -> str:
    """Rough near-duplicate detector: normalize punctuation/quotes/numbers."""
    s = norm(s)
    s = re.sub(r"[「」『』（）\(\)\[\]【】]", "", s)
    s = re.sub(r"[、。,.!?！？:：;；]", "", s)
    s = re.sub(r"\d+", "#", s)
    return s


def load_n5_items():
    data = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    return [it for it in data.get("items", []) if it.get("level") == "N5"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, required=True, help="N5 起始編號（1-based）")
    ap.add_argument("--end", type=int, required=True, help="N5 結束編號（1-based, inclusive）")
    args = ap.parse_args()

    n5 = load_n5_items()
    start = max(1, args.start)
    end = min(len(n5), args.end)
    batch = n5[start - 1 : end]

    exact_map: dict[str, list[str]] = defaultdict(list)
    skel_map: dict[str, list[str]] = defaultdict(list)
    same_word_pair = []

    for i, it in enumerate(batch, start):
        word = it.get("word", "")
        ex = it.get("examples") or []
        ja = [norm((ex[j].get("ja") if j < len(ex) else "") or "") for j in range(2)]

        if ja[0] and ja[0] == ja[1]:
            same_word_pair.append((i, word, ja[0]))

        for sent in ja:
            if not sent:
                continue
            exact_map[sent].append(f"{i:03d}:{word}")
            skel_map[skeleton(sent)].append(f"{i:03d}:{word}")

    exact_dupes = {k: v for k, v in exact_map.items() if len(v) > 1}
    near_dupes = {k: v for k, v in skel_map.items() if len(v) > 1}

    print(f"Range N5 {start}-{end}")
    print(f"Items: {len(batch)}")
    print(f"Same sentence within one word pair: {len(same_word_pair)}")
    print(f"Exact duplicate sentences across batch: {len(exact_dupes)}")
    print(f"Near-duplicate sentence skeletons: {len(near_dupes)}")
    print("----")

    if same_word_pair:
        print("[Same pair]")
        for idx, word, s in same_word_pair[:20]:
            print(f"- {idx:03d} {word}: {s}")

    if exact_dupes:
        print("[Exact duplicates]")
        n = 0
        for sent, refs in exact_dupes.items():
            print(f"- refs={', '.join(refs)}")
            print(f"  {sent}")
            n += 1
            if n >= 20:
                break

    if near_dupes:
        print("[Near duplicates]")
        n = 0
        for sk, refs in near_dupes.items():
            # skip exact duplicates already shown
            uniq_refs = sorted(set(refs))
            if len(uniq_refs) <= 1:
                continue
            print(f"- refs={', '.join(uniq_refs[:8])}")
            n += 1
            if n >= 20:
                break


if __name__ == "__main__":
    main()

