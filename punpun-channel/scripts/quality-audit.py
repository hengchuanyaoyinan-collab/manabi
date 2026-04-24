"""台本品質監査。

docs/strategy/06-quality-standards.md の基準を満たしているかチェック。
100 点満点でスコア化し、70 点未満は投稿禁止と判定。

使い方:
    python scripts/quality-audit.py test_data/チンギスハン.json

複数まとめて:
    python scripts/quality-audit.py test_data/*.json
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import VideoScript


# スコア配点 (合計 100)
WEIGHTS = {
    "hook_first_30s": 20,   # 冒頭 30 秒のフック
    "image_diversity": 15,  # 画像ヒントの多様性
    "emotion_variety": 10,  # 感情の変化
    "scene_length": 10,     # セリフ平均長
    "chapter_structure": 10,  # 章構成
    "metadata": 10,         # タイトル・概要欄
    "content_depth": 15,    # 具体数字・固有名詞
    "no_blank_overload": 10,  # blank が少ない
}


def _score_hook(script: VideoScript) -> tuple[int, list[str]]:
    """冒頭 30 秒内のフック品質。"""
    issues: list[str] = []
    # 最初の 3〜5 シーン程度が 30 秒想定
    early = script.scenes[:5]
    if not early:
        return 0, ["シーン無し"]

    first_text = " ".join(s.text for s in early)
    score = 0
    # 衝撃感情の存在
    if any(s.emotion in ("shock", "think") for s in early[:3]):
        score += 7
    else:
        issues.append("冒頭 3 シーン内に shock/think 感情なし")
    # 数字の存在
    import re
    if re.search(r"\d", first_text):
        score += 7
    else:
        issues.append("冒頭に数字なし (具体性不足)")
    # 疑問投げかけ
    if any(w in first_text for w in ("?", "？", "でしょうか", "知ってます", "どう思")):
        score += 6
    else:
        issues.append("冒頭に疑問投げかけなし")
    return min(score, WEIGHTS["hook_first_30s"]), issues


def _score_image_diversity(script: VideoScript) -> tuple[int, list[str]]:
    """画像タイプのバランス。"""
    issues: list[str] = []
    types = Counter(s.image_hint.type.value for s in script.scenes)
    total = len(script.scenes)
    if total == 0:
        return 0, ["シーン無し"]

    score = 0
    blank_ratio = types.get("blank", 0) / total
    if blank_ratio <= 0.05:
        score += 5
    elif blank_ratio <= 0.15:
        score += 3
    else:
        issues.append(f"blank 過多 ({blank_ratio:.1%})")

    # 多様性ボーナス
    distinct_types = len([t for t, c in types.items() if c >= 2])
    score += min(distinct_types * 2, 10)
    if distinct_types < 3:
        issues.append(f"画像タイプが {distinct_types} 種類しかない (3+ 推奨)")
    return min(score, WEIGHTS["image_diversity"]), issues


def _score_emotion_variety(script: VideoScript) -> tuple[int, list[str]]:
    issues: list[str] = []
    emotions = [s.emotion for s in script.scenes]
    if not emotions:
        return 0, ["シーン無し"]

    unique = set(emotions)
    score = min(len(unique) * 2, 10)
    if len(unique) < 4:
        issues.append(f"感情が {len(unique)} 種類しかない (4+ 推奨)")

    # 同じ感情の連続チェック
    max_run = 1
    cur = 1
    for i in range(1, len(emotions)):
        if emotions[i] == emotions[i - 1]:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 1
    if max_run >= 6:
        score -= 3
        issues.append(f"同じ感情が {max_run} シーン連続")
    return max(score, 0), issues


def _score_scene_length(script: VideoScript) -> tuple[int, list[str]]:
    issues: list[str] = []
    lens = [len(s.text) for s in script.scenes]
    if not lens:
        return 0, ["シーン無し"]

    avg = sum(lens) / len(lens)
    score = 0
    if 15 <= avg <= 30:
        score = 10
    elif 10 <= avg <= 40:
        score = 7
    elif avg > 40:
        score = 3
        issues.append(f"平均セリフ長 {avg:.0f} 字 (長すぎ)")
    else:
        score = 3
        issues.append(f"平均セリフ長 {avg:.0f} 字 (短すぎ)")
    return score, issues


def _score_chapter_structure(script: VideoScript) -> tuple[int, list[str]]:
    issues: list[str] = []
    if not script.chapters:
        return 0, ["章情報なし"]
    n = len(script.chapters)
    if n == 7:
        return 10, []
    if n in (6, 8):
        return 7, [f"章数 {n} (7 推奨)"]
    if n in (5, 9, 10):
        return 4, [f"章数 {n}"]
    return 2, [f"章数 {n} が異常"]


def _score_metadata(script: VideoScript) -> tuple[int, list[str]]:
    issues: list[str] = []
    score = 0
    # タイトル
    t = script.title or ""
    if 25 <= len(t) <= 50:
        score += 3
    else:
        issues.append(f"タイトル長 {len(t)} 字 (25-50 推奨)")
    if any(w in t for w in ("衝撃", "狂気", "やばい", "最悪", "地獄", "やばすぎ", "悲劇")):
        score += 2
    else:
        issues.append("タイトルに煽りワードなし")
    import re
    if re.search(r"\d", t):
        score += 2
    # 概要欄
    d = script.description or ""
    if len(d) >= 200:
        score += 2
    else:
        issues.append(f"概要欄 {len(d)} 字 (200+ 推奨)")
    # タグ
    if len(script.tags) >= 10:
        score += 1
    else:
        issues.append(f"タグ {len(script.tags)} 個 (10+ 推奨)")
    return min(score, WEIGHTS["metadata"]), issues


def _score_content_depth(script: VideoScript) -> tuple[int, list[str]]:
    """具体数字・固有名詞の濃度。"""
    import re
    issues: list[str] = []
    all_text = " ".join(s.text for s in script.scenes)
    if not all_text:
        return 0, ["本文無し"]

    # 具体数字 (西暦・人数等)
    numbers = re.findall(r"\d+", all_text)
    num_density = len(numbers) / max(len(script.scenes), 1)
    score = min(int(num_density * 10), 8)
    if num_density < 0.3:
        issues.append(f"数字が少ない (密度 {num_density:.2f})")

    # カタカナ固有名詞 (人名・地名想定)
    katakana = re.findall(r"[゠-ヿ]{3,}", all_text)
    if len(set(katakana)) >= 8:
        score += 7
    elif len(set(katakana)) >= 4:
        score += 4
    else:
        issues.append(f"固有名詞 (カタカナ) {len(set(katakana))} 種類 (8+ 推奨)")
    return min(score, WEIGHTS["content_depth"]), issues


def _score_no_blank(script: VideoScript) -> tuple[int, list[str]]:
    issues: list[str] = []
    if not script.scenes:
        return 0, ["シーン無し"]
    blank_count = sum(
        1 for s in script.scenes if s.image_hint.type.value == "blank"
    )
    ratio = blank_count / len(script.scenes)
    if ratio <= 0.05:
        return 10, []
    if ratio <= 0.10:
        return 7, [f"blank ratio {ratio:.0%}"]
    if ratio <= 0.20:
        return 4, [f"blank ratio {ratio:.0%} 多め"]
    return 1, [f"blank ratio {ratio:.0%} 深刻"]


SCORE_FNS = {
    "hook_first_30s": _score_hook,
    "image_diversity": _score_image_diversity,
    "emotion_variety": _score_emotion_variety,
    "scene_length": _score_scene_length,
    "chapter_structure": _score_chapter_structure,
    "metadata": _score_metadata,
    "content_depth": _score_content_depth,
    "no_blank_overload": _score_no_blank,
}


def audit(script: VideoScript) -> dict:
    breakdown = {}
    all_issues: list[str] = []
    total_score = 0
    for k, fn in SCORE_FNS.items():
        s, issues = fn(script)
        breakdown[k] = {"score": s, "max": WEIGHTS[k], "issues": issues}
        total_score += s
        all_issues.extend([f"[{k}] {i}" for i in issues])

    verdict = (
        "投稿 OK" if total_score >= 85
        else "手動レビュー推奨" if total_score >= 70
        else "投稿禁止 / 再生成"
    )
    return {
        "total_score": total_score,
        "verdict": verdict,
        "breakdown": breakdown,
        "issues": all_issues,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+", help="台本 JSON ファイル")
    p.add_argument("--json", action="store_true", help="JSON 出力")
    args = p.parse_args()

    paths: list[Path] = []
    for f in args.files:
        paths.extend(Path(p) for p in glob.glob(f))

    results = []
    for path in paths:
        if not path.exists():
            print(f"❌ {path} 無し")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            script = VideoScript.model_validate(data)
        except Exception as e:
            print(f"❌ {path.name}: parse fail: {e}")
            continue

        report = audit(script)
        results.append({"file": path.name, "title": script.title, **report})

        if args.json:
            continue

        # Human output
        total = report["total_score"]
        color = "\033[32m" if total >= 85 else "\033[33m" if total >= 70 else "\033[31m"
        reset = "\033[0m"
        print(f"\n=== {path.name} ===")
        print(f"タイトル: {script.title}")
        print(f"{color}スコア: {total}/100  [{report['verdict']}]{reset}")
        print("内訳:")
        for k, v in report["breakdown"].items():
            mark = "✅" if v["score"] == v["max"] else "🟡" if v["score"] >= v["max"] * 0.7 else "❌"
            print(f"  {mark} {k}: {v['score']}/{v['max']}")
        if report["issues"]:
            print("改善ポイント:")
            for i in report["issues"][:8]:
                print(f"  - {i}")

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))

    # 失敗スコアのみで exit code
    if any(r["total_score"] < 70 for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
