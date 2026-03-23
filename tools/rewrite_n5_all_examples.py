from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "data" / "packs" / "wkei-vocab" / "vocab.json"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def infer_kind(word: str, meaning_en: str, pos: str) -> str:
    m = (meaning_en or "").lower()
    if "副詞" in pos or any(
        k in m
        for k in [
            "always",
            "often",
            "sometimes",
            "usually",
            "already",
            "still",
            "very",
            "quickly",
            "slowly",
            "tomorrow",
            "yesterday",
            "today",
            "soon",
            "later",
            "again",
        ]
    ):
        return "adverb"
    if m.startswith("to "):
        return "verb"
    if word.endswith("い") or any(
        k in m
        for k in [
            "hot",
            "cold",
            "new",
            "old",
            "big",
            "small",
            "long",
            "short",
            "high",
            "low",
            "busy",
            "cheap",
            "expensive",
            "difficult",
            "easy",
            "beautiful",
            "convenient",
            "narrow",
            "wide",
        ]
    ):
        return "adj"
    return "noun"


def make_pair(word: str, reading: str, meaning_cn: str, meaning_en: str, kind: str, idx: int) -> tuple[str, str, str, str]:
    m = (meaning_en or "").lower()

    color_map = {
        "black": "黒",
        "white": "白",
        "red": "赤",
        "blue": "青",
        "yellow": "黄色",
        "green": "緑",
        "brown": "茶色",
    }
    for k, jp in color_map.items():
        if k in m or jp in word:
            ja1 = f"田中さんは{word}のセーターを着ていて、とてもよく似合っています。"
            ja2 = f"{word}いろのペンで重要なところを印すると、復習しやすくなります。"
            zh1 = f"田中先生穿著{word}毛衣，看起來非常合適。"
            zh2 = f"用{word}色的筆標記重點，複習時會更方便。"
            return ja1, ja2, zh1, zh2

    if any(k in m for k in ["tea", "coffee", "milk", "water", "juice", "drink"]):
        ja1 = f"朝、{word}を飲むと気分が落ち着いて、一日を始めやすいです。"
        ja2 = f"この店の{word}は香りがよく、仕事の合間によく注文します。"
        zh1 = f"早上喝{word}能讓心情平穩，更好開始一天。"
        zh2 = f"這家店的{word}香氣很好，我工作空檔常會點。"
        return ja1, ja2, zh1, zh2

    if any(k in m for k in ["station", "school", "hospital", "company", "park", "library", "kitchen", "room", "house", "office"]):
        ja1 = f"今日は{word}で待ち合わせをして、先に昼ごはんを食べました。"
        ja2 = f"{word}の近くに新しい店ができて、帰り道が少し楽しくなりました。"
        zh1 = f"今天我在{word}碰面，先一起吃了午餐。"
        zh2 = f"{word}附近開了新店，回家的路變得更有趣。"
        return ja1, ja2, zh1, zh2

    if any(k in m for k in ["month", "year", "week", "day", "morning", "night", "hour", "time"]):
        ja1 = f"{word}は学習計画を見直すのにちょうどいいタイミングです。"
        ja2 = f"{word}に目標を決めておくと、毎日の勉強を続けやすくなります。"
        zh1 = f"{word}是重新檢視學習計畫的好時機。"
        zh2 = f"在{word}先設定目標，會更容易持續每天學習。"
        return ja1, ja2, zh1, zh2

    if kind == "verb":
        v1 = [
            f"授業で習った文型を使って、短い文を作ってから{word}練習をしました。",
            f"困ったときは一度深呼吸して、落ち着いて{word}ようにしています。",
            f"会話の流れを聞いて、自然なタイミングで{word}ことが大切です。",
            f"毎日少しずつでも{word}と、だんだん自信がついてきます。",
            f"先生の例をまねして{word}と、使い方が早く身につきます。",
            f"最初は難しく感じても、繰り返し{word}と慣れてきます。",
        ]
        v2 = [
            f"友だちとロールプレイをしながら{word}練習をしたら、発話がスムーズになりました。",
            f"文の前後を確認してから{word}と、意味のずれが少なくなります。",
            f"試験前はよく出る表現を中心に{word}ようにしています。",
            f"実際の場面を想像して{word}と、記憶に残りやすいです。",
            f"毎回同じ間違いをしないように、注意点をメモしてから{word}ようにしました。",
            f"音読と一緒に{word}練習をすると、発音と意味を同時に確認できます。",
        ]
        i1 = idx % len(v1)
        i2 = (idx * 5 + 1) % len(v2)
        ja1, ja2 = v1[i1], v2[i2]
        zh1 = f"我先用課堂學的句型造短句，再練習「{word}」。"
        zh2 = f"和朋友做情境對話練習「{word}」後，說話變得更順。"
        return ja1, ja2, zh1, zh2

    if kind == "adj":
        a1 = [
            f"この説明は{word}ので、初めて学ぶ人にも分かりやすいです。",
            f"今日は{word}ので、上着を一枚多く持っていきました。",
            f"この道は{word}ですが、人通りが少なくて歩きやすいです。",
            f"その店は駅から近くて{word}ので、よく利用しています。",
            f"昨日より{word}ので、今日は早めに家を出ました。",
            f"この課題は思ったより{word}ので、時間内に終わりました。",
        ]
        a2 = [
            f"場面によっては{word}表現のほうが自然に聞こえます。",
            f"{word}と感じた点をノートに残すと、復習がしやすいです。",
            f"先生のアドバイスで、苦手だった部分も少し{word}なりました。",
            f"読む前に背景を理解すると、内容が{word}く感じます。",
            f"毎日続けると、以前より{word}と感じる場面が増えます。",
            f"実際に使ってみると、教科書で見るより{word}と分かります。",
        ]
        i1 = idx % len(a1)
        i2 = (idx * 7 + 2) % len(a2)
        ja1, ja2 = a1[i1], a2[i2]
        zh1 = f"這裡的描述是「{word}」，所以初學者也容易理解。"
        zh2 = f"把你覺得「{word}」的地方記下來，複習會更有效。"
        return ja1, ja2, zh1, zh2

    if kind == "adverb":
        d1 = [
            f"{word}短い音読を続けると、発音が安定しやすくなります。",
            f"{word}授業ノートを見返すだけでも、記憶がかなり定着します。",
            f"{word}先生の説明を意識して聞くと、文型の違いが分かりやすいです。",
            f"{word}例文を声に出して読むと、会話で出やすくなります。",
            f"{word}目標を確認しておくと、学習のペースが崩れにくいです。",
            f"{word}振り返りをすると、次に何を直すべきか見えてきます。",
        ]
        d2 = [
            f"{word}辞書を引くだけでなく、実際の例文も一緒に確認しています。",
            f"{word}練習しているうちに、自然な言い回しが増えてきました。",
            f"{word}一つずつ確かめると、ミスを減らしやすいです。",
            f"{word}時間を決めて学習すると、集中力が続きます。",
            f"{word}使える表現を増やすことで、会話の幅が広がります。",
            f"{word}難しい単語も、文脈で見ると覚えやすくなります。",
        ]
        i1 = idx % len(d1)
        i2 = (idx * 3 + 4) % len(d2)
        ja1, ja2 = d1[i1], d2[i2]
        zh1 = f"{word}做短時間朗讀練習，發音會更穩。"
        zh2 = f"{word}不只查字典，也一起看實際例句。"
        return ja1, ja2, zh1, zh2

    # Noun/default: keep natural context while avoiding absurd direct actions.
    n1 = [
        f"授業で「{word}」という語が出てきたので、すぐに意味を確認しました。",
        f"会話の中で「{word}」を聞いたとき、前後の文から意味を推測しました。",
        f"ノートに「{word}」を書いて、似た言葉との違いを整理しました。",
        f"読解問題で「{word}」を見つけたら、まず文脈を確認するようにしています。",
        f"先生は「{word}」の使い方を具体的な場面で説明してくれました。",
        f"「{word}」を覚えると、似た文の意味も理解しやすくなります。",
        f"「{word}」は日常会話でも見かけるので、先に覚えておくと便利です。",
        f"「{word}」の意味を知っていると、聞き取りの精度が上がります。",
        f"テキストに出た「{word}」を辞書で調べて、例文も一緒に読みました。",
        f"「{word}」は短い文で何度も使うと、自然に覚えられます。",
    ]
    n2 = [
        f"今日は「{word}」を使った文を二つ作って、授業で発表しました。",
        f"友だちと「{word}」を使って会話練習をしたら、理解が深まりました。",
        f"「{word}」を中心に単語カードを作ると、復習がしやすくなります。",
        f"「{word}」の意味を自分の言葉で説明できると、記憶が定着します。",
        f"次のテストまでに「{word}」を例文ごと覚える予定です。",
        f"「{word}」を使う場面を想像すると、実際の会話で出しやすくなります。",
        f"「{word}」を覚えたあとで本文を読むと、内容がすっと入ってきます。",
        f"「{word}」は似た語とセットで覚えると、使い分けがしやすいです。",
        f"授業後に「{word}」を使った練習問題を解いて、理解を確認しました。",
        f"「{word}」を含む短い会話を繰り返すと、実践で使えるようになります。",
    ]
    i1 = idx % len(n1)
    i2 = (idx * 9 + 3) % len(n2)
    ja1, ja2 = n1[i1], n2[i2]
    zh1 = f"課堂中出現「{word}」時，我立刻確認它在語境裡的意思。"
    zh2 = f"我用「{word}」造了兩個句子，讓記憶更穩固。"
    return ja1, ja2, zh1, zh2


def main() -> None:
    data = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    items: list[dict] = data.get("items") or []
    n5 = [it for it in items if it.get("level") == "N5"]

    # Keep first 50 manually curated entries as-is.
    for idx, it in enumerate(n5):
        if idx < 50:
            continue
        word = norm(it.get("word"))
        reading = norm(it.get("reading"))
        meaning_cn = norm(it.get("meaning"))
        meaning_en = norm(it.get("meaningEn")) or meaning_cn
        pos = norm(it.get("pos"))
        kind = infer_kind(word, meaning_en, pos)
        ja1, ja2, zh1, zh2 = make_pair(word, reading, meaning_cn, meaning_en, kind, idx)

        it["exampleJa"] = ja1
        it["exampleReading"] = reading
        it["exampleZh"] = zh1
        it["examples"] = [
            {"ja": ja1, "reading": reading, "zh": zh1, "audioPhrase": ""},
            {"ja": ja2, "reading": reading, "zh": zh2, "audioPhrase": ""},
        ]

    VOCAB_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"N5 total updated (excluding first50 manual): {max(0, len(n5)-50)}")


if __name__ == "__main__":
    main()

