"""OpenAI gpt-image-1 / DALL-E で歴史シーン用の画像を生成。

いらすとや / Wikipedia で取れないシーン専用画像が欲しい時に使う。

コスト (2026 年時点の OpenAI 料金):
- gpt-image-1: $0.042/枚 (medium 1024x1024)
- gpt-image-1 HD: $0.19/枚 (high 1024x1024)

1 動画 100 枚 medium なら $4.2。Max 契約内で使うなら別 API キー必要。

事前準備:
1. https://platform.openai.com でアカウント作成
2. API キー発行 (sk-...)
3. .env に追加: OPENAI_API_KEY=sk-...
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import requests

from src.config import ASSETS_DIR, env


CACHE_DIR = ASSETS_DIR / "cache"


def _cache_key(prompt: str, size: str, model: str) -> str:
    return hashlib.sha1(f"{model}_{size}_{prompt}".encode("utf-8")).hexdigest()[:16]


# ぷんぷんチャンネル用の共通スタイル指示
STYLE_PREFIX = (
    "Hand-drawn Japanese illustration style, kamishibai storytelling art, "
    "simple flat colors, soft outlines, educational YouTube history video aesthetic, "
    "isolated subject on clean background. "
)


def generate_scene_image(
    prompt: str,
    *,
    size: str = "1024x1024",
    model: str = "gpt-image-1",
    quality: str = "medium",
    use_style_prefix: bool = True,
) -> Path | None:
    """プロンプトから画像を生成。失敗時 None。"""
    api_key = env("OPENAI_API_KEY")
    if not api_key:
        return None

    full_prompt = (STYLE_PREFIX + prompt) if use_style_prefix else prompt
    cache = CACHE_DIR / f"oai_{_cache_key(full_prompt, size, model)}.png"
    if cache.exists():
        return cache

    try:
        r = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "prompt": full_prompt,
                "size": size,
                "quality": quality,
                "n": 1,
            },
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        item = data["data"][0]
        if "b64_json" in item:
            img_bytes = base64.b64decode(item["b64_json"])
        else:
            img_url = item["url"]
            img_bytes = requests.get(img_url, timeout=30).content

        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(img_bytes)
        return cache
    except Exception as e:
        import logging
        logging.warning(f"OpenAI image gen failed: {e}")
        return None


def is_available() -> bool:
    return bool(env("OPENAI_API_KEY"))


# 日本語キーワード → 英語プロンプト変換 (シーンの説明に使う)
KEYWORD_TO_ENGLISH = {
    "戦士": "ancient warriors with armor",
    "王様": "a king sitting on a throne",
    "城": "medieval castle at dusk",
    "戦場": "ancient battlefield with soldiers",
    "処刑": "historical execution scene, dramatic",
    "宮廷": "ornate palace court scene",
    "皇帝": "emperor in royal robes",
    "貴族": "aristocratic nobles in old Europe",
    "農民": "medieval peasants working",
    "商人": "merchants in a historical market",
    "船": "ancient ship sailing",
    "地獄": "hellish underworld, dark atmosphere",
    "戦争": "historical warfare, army clash",
    "反乱": "historical rebellion, protest",
    "愛人": "noble couple in romantic setting",
    "毒殺": "person holding a suspicious drink, dark",
    "謀反": "conspirators whispering in shadows",
    "軍隊": "ancient army formation",
    "暗殺": "assassin in shadows, dramatic",
}


def translate_keyword(jp_keyword: str) -> str:
    """日本語キーワードを画像生成用の英語プロンプトに。
    マッピングに無ければ、シンプルに変換。
    """
    for jp, en in KEYWORD_TO_ENGLISH.items():
        if jp in jp_keyword:
            return en
    # フォールバック: そのまま使う
    return f"historical scene: {jp_keyword}"


if __name__ == "__main__":
    import sys
    if not is_available():
        print("OPENAI_API_KEY 未設定")
        sys.exit(1)
    prompt = sys.argv[1] if len(sys.argv) > 1 else "ancient emperor on throne"
    p = generate_scene_image(prompt)
    print(f"Generated: {p}")
