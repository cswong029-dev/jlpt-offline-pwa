from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "data" / "packs" / "wkei-vocab" / "vocab.json"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def infer_kind(word: str, meaning_en: str, pos: str) -> str:
    m = meaning_en.lower()
    if "副詞" in pos or any(k in m for k in ["always", "often", "sometimes", "usually", "already", "still", "very", "quickly", "slowly", "tomorrow", "yesterday", "today"]):
        return "adverb"
    if m.startswith("to "):
        return "verb"
    if word.endswith("い") or any(k in m for k in ["hot", "cold", "new", "old", "big", "small", "long", "short", "high", "low", "busy", "cheap", "expensive", "difficult", "easy"]):
        return "adj"
    return "noun"


def make_examples(word: str, meaning_cn: str, meaning_en: str, kind: str, idx: int) -> tuple[str, str, str, str]:
    # Rich sentence banks with multiple contexts; choose by deterministic index.
    noun_ja_1 = [
        f"駅の近くで{word}を買って、家で使いました。",
        f"先生は授業で{word}について説明しました。",
        f"週末に{word}を準備して、旅行に出かけました。",
        f"友だちに{word}を見せたら、とても喜んでくれました。",
        f"家族と相談して、{word}を新しくしました。",
        f"店員さんに聞いて、{word}の選び方が分かりました。",
        f"朝、かばんの中に{word}が入っているか確認しました。",
        f"図書館で{word}に関する本を借りました。",
    ]
    noun_ja_2 = [
        f"会話で{word}という言葉が出てきたので、すぐメモしました。",
        f"{word}があると、毎日の生活がもっと便利になります。",
        f"昨日なくしたと思った{word}が、机の下で見つかりました。",
        f"必要なときに{word}が見つからないと困ります。",
        f"{word}の使い方を覚えてから、作業が速くなりました。",
        f"この店の{word}は品質が良くて、値段も手ごろです。",
        f"{word}を使ったら、思っていたより簡単にできました。",
        f"旅行の前日に、忘れずに{word}をかばんに入れました。",
    ]
    noun_zh_1 = [
        f"我在車站附近買了{word}，回家後就用了。",
        f"老師在課堂上說明了{word}。",
        f"週末我準備了{word}，然後去旅行。",
        f"我把{word}給朋友看，他很高興。",
        f"和家人討論後，我把{word}換新了。",
        f"我問店員後，懂得怎麼挑{word}了。",
        f"早上我先確認包包裡有沒有{word}。",
        f"我在圖書館借了和{word}相關的書。",
    ]
    noun_zh_2 = [
        f"對話中出現了{word}這個詞，我立刻記下來。",
        f"有了{word}，日常生活會更方便。",
        f"昨天以為弄丟的{word}，在桌子下找到了。",
        f"需要時找不到{word}會很困擾。",
        f"學會{word}的用法後，做事變快了。",
        f"這家店的{word}品質好，價格也合理。",
        f"用了{word}後，發現比想像中容易。",
        f"旅行前一天，我把{word}放進包包避免忘記。",
    ]

    verb_ja_1 = [
        f"朝早く起きて、駅まで歩いてから{word}。".replace("。", ""),
        f"先生の質問に答える前に、もう一度考えて{word}。".replace("。", ""),
        f"授業のあとで友だちと日本語で{word}。".replace("。", ""),
        f"間違えたところをノートで確認してから{word}。".replace("。", ""),
        f"週末は家でゆっくり{word}。".replace("。", ""),
        f"困ったときは先生に相談して{word}。".replace("。", ""),
    ]
    verb_ja_2 = [
        f"毎日少しずつ練習すれば、自然に{word}ようになります。",
        f"この場面では、丁寧な言い方で{word}のが大切です。",
        f"会話の流れを聞いて、タイミングよく{word}と伝えましょう。",
        f"急がず落ち着いて{word}と、意味がはっきり伝わります。",
        f"例文を音読して、実際の会話でも{word}練習をしました。",
        f"相手の反応を見ながら{word}と、会話がスムーズになります。",
    ]
    verb_zh_1 = [
        f"我早起後走到車站，再來{meaning_cn or word}。",
        f"回答老師前，我先想一想再{meaning_cn or word}。",
        f"下課後我和朋友用日文{meaning_cn or word}。",
        f"先用筆記確認錯的地方再{meaning_cn or word}。",
        f"週末我在家慢慢{meaning_cn or word}。",
        f"遇到困難時我會先請教老師再{meaning_cn or word}。",
    ]
    verb_zh_2 = [
        f"每天一點一點練習，就會自然地{meaning_cn or word}。",
        f"這個情境裡，用禮貌方式去{meaning_cn or word}很重要。",
        f"先聽懂對話流程，再抓時機{meaning_cn or word}。",
        f"不要急，冷靜地{meaning_cn or word}，意思會更清楚。",
        f"我先朗讀例句，再把{meaning_cn or word}用到實際會話。",
        f"觀察對方反應再{meaning_cn or word}，對話會更順。",
    ]

    adj_ja_1 = [
        f"この部屋は{word}ので、窓を開けました。",
        f"今日は{word}天気だから、散歩に行きたいです。",
        f"その説明は{word}ので、すぐ理解できました。",
        f"この道は夜になると{word}から、気をつけてください。",
        f"新しいかばんは軽くて、持ち歩くと{word}です。",
        f"この問題は思ったより{word}ので安心しました。",
    ]
    adj_ja_2 = [
        f"先生は{word}表現と普通の表現の違いを教えてくれました。",
        f"朝より夜のほうが{word}と感じます。",
        f"この店は駅から近くて、値段も{word}です。",
        f"今日は昨日より{word}ので、厚い服を着ました。",
        f"その映画は評判どおり{word}かったです。",
        f"練習を続けたら、苦手な部分も{word}なりました。",
    ]
    adj_zh_1 = [
        f"這個房間很{meaning_cn or word}，所以我打開了窗戶。",
        f"今天天氣很{meaning_cn or word}，我想去散步。",
        f"那個說明很{meaning_cn or word}，我馬上就懂了。",
        f"這條路晚上會很{meaning_cn or word}，請小心。",
        f"新包包很輕，帶著走很{meaning_cn or word}。",
        f"這題比想像中{meaning_cn or word}，我放心了。",
    ]
    adj_zh_2 = [
        f"老師教了我們{meaning_cn or word}表達和普通表達的差別。",
        f"我覺得晚上比早上更{meaning_cn or word}。",
        f"這家店離車站近，價格也很{meaning_cn or word}。",
        f"今天比昨天更{meaning_cn or word}，所以我穿了厚衣服。",
        f"那部電影和評價一樣，真的很{meaning_cn or word}。",
        f"持續練習後，不擅長的部分也變得{meaning_cn or word}了。",
    ]

    adverb_ja_1 = [
        f"{word}日本語の音読をしています。",
        f"{word}復習すれば、語彙はしっかり定着します。",
        f"{word}先生の話を聞くようにしています。",
        f"{word}短い文を作って練習しています。",
        f"{word}辞書を確認してから答えます。",
        f"{word}落ち着いて話すと、発音がよくなります。",
    ]
    adverb_ja_2 = [
        f"{word}時間がある日は、図書館で勉強します。",
        f"{word}会話練習を続けると、表現力が伸びます。",
        f"{word}聞き取りをすると、自然な言い回しが覚えやすいです。",
        f"{word}ノートを見直すと、間違いが減ります。",
        f"{word}目標を決めて勉強すると、やる気が続きます。",
        f"{word}声に出して読むと、意味をつかみやすいです。",
    ]
    adverb_zh_1 = [
        f"我{meaning_cn or word}都會做日文朗讀練習。",
        f"{meaning_cn or word}複習的話，詞彙會記得更牢。",
        f"我{meaning_cn or word}都會專心聽老師說明。",
        f"我{meaning_cn or word}都會用短句練習。",
        f"我{meaning_cn or word}先查字典再作答。",
        f"{meaning_cn or word}冷靜地說話，發音會更好。",
    ]
    adverb_zh_2 = [
        f"{meaning_cn or word}有時間時，我會去圖書館學習。",
        f"{meaning_cn or word}持續做會話練習，表達能力會提升。",
        f"{meaning_cn or word}做聽力練習更容易記住自然說法。",
        f"{meaning_cn or word}複習筆記會減少錯誤。",
        f"{meaning_cn or word}先定好目標，學習動力比較能持續。",
        f"{meaning_cn or word}把句子唸出來，更容易抓到意思。",
    ]

    if kind == "verb":
        i1 = idx % len(verb_ja_1)
        i2 = (idx * 3 + 1) % len(verb_ja_2)
        ja1 = verb_ja_1[i1] + "。"
        ja2 = verb_ja_2[i2]
        zh1 = verb_zh_1[i1]
        zh2 = verb_zh_2[i2]
        return ja1, ja2, zh1, zh2
    if kind == "adj":
        i1 = idx % len(adj_ja_1)
        i2 = (idx * 5 + 2) % len(adj_ja_2)
        return adj_ja_1[i1], adj_ja_2[i2], adj_zh_1[i1], adj_zh_2[i2]
    if kind == "adverb":
        i1 = idx % len(adverb_ja_1)
        i2 = (idx * 7 + 3) % len(adverb_ja_2)
        return adverb_ja_1[i1], adverb_ja_2[i2], adverb_zh_1[i1], adverb_zh_2[i2]

    i1 = idx % len(noun_ja_1)
    i2 = (idx * 11 + 1) % len(noun_ja_2)
    ja1 = noun_ja_1[i1]
    ja2 = noun_ja_2[i2]
    zh1 = noun_zh_1[i1]
    zh2 = noun_zh_2[i2]
    return ja1, ja2, zh1, zh2


def main() -> None:
    data = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    items: list[dict] = data.get("items") or []

    n5 = [it for it in items if it.get("level") == "N5"]
    for i, it in enumerate(n5):
        word = norm(it.get("word"))
        meaning_cn = norm(it.get("meaning"))
        meaning_en = norm(it.get("meaningEn")) or meaning_cn
        pos = norm(it.get("pos"))
        kind = infer_kind(word, meaning_en, pos)
        ja1, ja2, zh1, zh2 = make_examples(word, meaning_cn, meaning_en, kind, i)
        reading = norm(it.get("reading"))

        it["exampleJa"] = ja1
        it["exampleReading"] = reading
        it["exampleZh"] = zh1
        it["examples"] = [
            {"ja": ja1, "reading": reading, "zh": zh1, "audioPhrase": ""},
            {"ja": ja2, "reading": reading, "zh": zh2, "audioPhrase": ""},
        ]

    VOCAB_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"N5 updated: {len(n5)} items")


if __name__ == "__main__":
    main()

