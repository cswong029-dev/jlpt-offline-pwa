from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOCAB_PATH = ROOT / "data" / "packs" / "wkei-vocab" / "vocab.json"
OUT_TXT = ROOT / "n5_151_350_examples_review.txt"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def kind_of(word: str, meaning_en: str, pos: str) -> str:
    m = meaning_en.lower()
    if "副詞" in pos or any(k in m for k in ["always", "often", "sometimes", "usually", "already", "still", "very", "quickly", "slowly", "today", "tomorrow", "yesterday", "again", "soon", "later"]):
        return "adverb"
    if m.startswith("to "):
        return "verb"
    if word.endswith("い") or any(k in m for k in ["hot", "cold", "new", "old", "big", "small", "long", "short", "high", "low", "difficult", "easy", "beautiful", "convenient", "narrow", "wide", "cheap", "expensive"]):
        return "adj"
    return "noun"


NOUN_JA_A = [
    "授業で「{w}」という語を扱ったので、ノートに用法を整理しました。",
    "読解問題に「{w}」が出たとき、前後の文から意味を推測しました。",
    "会話で「{w}」を聞いたあと、辞書でニュアンスを確認しました。",
    "「{w}」を含む例文を二つ作ると、記憶に残りやすくなります。",
    "先生は「{w}」の使い方を、実際の場面と一緒に説明してくれました。",
    "今日の復習では「{w}」を中心に関連語もまとめました。",
    "「{w}」を覚えたあとで本文を読むと、内容がつながって見えました。",
    "「{w}」の意味を自分の言葉で言い換える練習をしました。",
    "授業後に「{w}」を使った短文を作って、発音も確認しました。",
    "「{w}」を見かけたら、まず品詞を意識して読むようにしています。",
    "単語カードに「{w}」を書き、例文とセットで覚えました。",
    "「{w}」の近い表現との違いを、先生に質問して整理しました。",
    "本文中の「{w}」が文全体の意味を決めるポイントでした。",
    "「{w}」を使う場面を想像すると、実際の会話でも出しやすいです。",
    "発表の前に「{w}」の使い方を確認して、言い間違いを防ぎました。",
]

NOUN_JA_B = [
    "次のテストでは「{w}」を使った問題が出そうなので、重点的に復習します。",
    "友だちと「{w}」を使ってロールプレイをしたら、理解が深まりました。",
    "「{w}」を含む文を音読すると、意味とリズムを同時に覚えられます。",
    "「{w}」は短い文より、少し長い文で練習すると定着しやすいです。",
    "「{w}」を覚えたことで、似たテーマの文章が読みやすくなりました。",
    "「{w}」に関連する単語を並べると、語彙のつながりが見えてきます。",
    "「{w}」を会話で使うときは、前後の敬語表現にも注意しています。",
    "「{w}」を覚えてから聞き取り練習をすると、反応が速くなりました。",
    "文脈の中で「{w}」を確認すると、単体で覚えるより忘れにくいです。",
    "「{w}」を使った質問文を作ると、実践でも使いやすくなります。",
    "教材の「{w}」を自分の生活に置き換えて覚えるようにしています。",
    "「{w}」を覚えると、同じ段落の内容理解が一気に進みました。",
    "復習時に「{w}」の例文を比較すると、使い分けが明確になります。",
    "「{w}」の意味を説明できるか確認すると、理解度を測りやすいです。",
    "「{w}」を話す練習を続けると、言い直しが減ってきました。",
]

VERB_JA_A = [
    "会話練習では、場面を決めてから「{w}」を使うようにしています。",
    "急いでいるときほど、落ち着いて「{w}」ことを意識しています。",
    "先生の例をまねしながら「{w}」と、使い方が早く身につきます。",
    "間違いを記録してから「{w}」練習をすると、改善が見えやすいです。",
    "毎日少しずつ「{w}」ことで、苦手意識が減ってきました。",
    "実際の状況を想像して「{w}」と、表現が自然になります。",
    "発音を確認してから「{w}」練習をすると、伝わり方がよくなります。",
    "短い文で何度も「{w}」と、会話で出しやすくなります。",
    "最初に意味を確認してから「{w}」と、文が作りやすいです。",
    "文の前後を理解して「{w}」ことが、正確さにつながります。",
]

VERB_JA_B = [
    "ロールプレイで「{w}」練習をしたら、実践での反応が速くなりました。",
    "一度に完璧を目指さず、まずは「{w}」回数を増やしています。",
    "「{w}」ときは、相手の反応を見て言い方を調整するようにしています。",
    "例文を書き換えて「{w}」練習をすると、応用力がつきます。",
    "学んだ文型を使って「{w}」と、記憶が長く残ります。",
    "毎回同じミスをしないよう、注意点を決めて「{w}」ようにしました。",
    "聞き取りのあとに「{w}」練習をすると、理解が定着します。",
    "場面に合う語を選んで「{w}」ことを、授業で繰り返しました。",
    "「{w}」前にキーワードを確認すると、話が組み立てやすいです。",
    "「{w}」練習を録音して聞き返すと、改善点がはっきり分かります。",
]

ADJ_JA_A = [
    "この場面では「{w}」という感覚が伝わると、文意が自然になります。",
    "昨日より「{w}」と感じたので、予定を少し早めました。",
    "説明が「{w}」と、初めての人でも理解しやすいです。",
    "天気が「{w}」ときは、体調管理に気をつけています。",
    "この道は「{w}」ので、歩く速度を落としたほうが安全です。",
    "価格だけでなく品質も見て、「{w}」かどうか判断します。",
    "文章が「{w}」と感じたら、主語と述語を先に確認します。",
    "学習計画は「{w}」より、続けやすいことを優先しています。",
]

ADJ_JA_B = [
    "「{w}」という印象を持った理由を説明できると、理解が深まります。",
    "先生は「{w}」表現と似た言い回しの違いも教えてくれました。",
    "例文を比べると、どの場面で「{w}」が自然か分かります。",
    "読む前に背景を知ると、内容が「{w}」く感じられます。",
    "練習を続けると、前より「{w}」と感じる瞬間が増えます。",
    "日常の出来事に当てはめると、「{w}」という語感がつかみやすいです。",
    "会話では文末の調整で、「{w}」印象が大きく変わります。",
    "「{w}」かどうか迷ったら、具体例で確認すると判断しやすいです。",
]

ADV_JA_A = [
    "「{w}」復習する習慣を作ると、忘れにくくなります。",
    "「{w}」短い音読を続けるだけでも、発音は安定してきます。",
    "「{w}」目標を見直すと、勉強の方向がぶれにくいです。",
    "「{w}」先生の説明を意識して聞くと、理解が速くなります。",
    "「{w}」例文を声に出すと、会話で使いやすくなります。",
    "「{w}」ノートを整理すると、復習の時間を短縮できます。",
    "「{w}」確認する手順を決めると、ミスを減らせます。",
    "「{w}」時間を区切って学ぶと、集中しやすいです。",
]

ADV_JA_B = [
    "「{w}」辞書だけでなく、実際の例文も一緒に見るようにしています。",
    "「{w}」一つずつ確認すると、理解の抜けが見つかりやすいです。",
    "「{w}」会話練習を入れると、覚えた語が定着しやすいです。",
    "「{w}」振り返りをすると、次の改善点がはっきりします。",
    "「{w}」聞き取り練習をすると、自然な言い回しが増えてきます。",
    "「{w}」優先順位を決めると、学習の効率が上がります。",
    "「{w}」短い文で試すと、新しい語でも使いやすいです。",
    "「{w}」チェック項目を決めておくと、作業が安定します。",
]


def main():
    data = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    items = data["items"]
    n5 = [it for it in items if it.get("level") == "N5"]
    target = n5[150:350]  # 151-350

    for idx, it in enumerate(target, 151):
        w = norm(it.get("word"))
        rd = norm(it.get("reading"))
        mcn = norm(it.get("meaning"))
        men = norm(it.get("meaningEn")) or mcn
        pos = norm(it.get("pos"))
        k = kind_of(w, men, pos)

        if k == "verb":
            ja1 = VERB_JA_A[idx % len(VERB_JA_A)].format(w=w)
            ja2 = VERB_JA_B[(idx * 3 + 1) % len(VERB_JA_B)].format(w=w)
        elif k == "adj":
            ja1 = ADJ_JA_A[idx % len(ADJ_JA_A)].format(w=w)
            ja2 = ADJ_JA_B[(idx * 5 + 2) % len(ADJ_JA_B)].format(w=w)
        elif k == "adverb":
            ja1 = ADV_JA_A[idx % len(ADV_JA_A)].format(w=w)
            ja2 = ADV_JA_B[(idx * 7 + 3) % len(ADV_JA_B)].format(w=w)
        else:
            ja1 = NOUN_JA_A[idx % len(NOUN_JA_A)].format(w=w)
            ja2 = NOUN_JA_B[(idx * 11 + 4) % len(NOUN_JA_B)].format(w=w)

        zh1 = f"例句一：{mcn}（語境練習）"
        zh2 = f"例句二：{mcn}（應用練習）"

        it["exampleJa"] = ja1
        it["exampleReading"] = rd
        it["exampleZh"] = zh1
        it["examples"] = [
            {"ja": ja1, "reading": rd, "zh": zh1, "audioPhrase": ""},
            {"ja": ja2, "reading": rd, "zh": zh2, "audioPhrase": ""},
        ]

    VOCAB_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    lines = ["N5 151-350 例句檢查\n"]
    for i, it in enumerate(target, 151):
        ex = it.get("examples") or [{}, {}]
        e1 = ex[0] if len(ex) > 0 else {}
        e2 = ex[1] if len(ex) > 1 else {}
        lines.append(f"{i:03d}. {it.get('word','')} ({it.get('reading','')}) - {it.get('meaning','')}")
        lines.append(f"  例句1(日): {e1.get('ja','')}")
        lines.append(f"  例句1(中): {e1.get('zh','')}")
        lines.append(f"  例句2(日): {e2.get('ja','')}")
        lines.append(f"  例句2(中): {e2.get('zh','')}")
        lines.append("")
    OUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print("updated 151-350 and wrote:", OUT_TXT)


if __name__ == "__main__":
    main()

