"""シーンの背景画像を集める。

- portrait/photo: Wikipedia / Wikimedia Commons から取得
- map_world/region/historical: ローカルの白地図 SVG をベースに描画
- illustration: いらすとや スクレイピング
- blank: 単色画像

取得した画像は assets/cache/ にキャッシュ。
"""
from __future__ import annotations

import hashlib
import io
import re
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

from src.config import ASSETS_DIR
from src.models import BackgroundType, ImageHint


CACHE_DIR = ASSETS_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

UA = "PunpunChannelBot/0.1 (educational; contact: punpun@example.com)"
HEADERS = {"User-Agent": UA}


# 同一 run 内で一度失敗したキーワードは再試行しない (速度対策)
_FAILED_KEYWORDS: set[str] = set()


def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def _cache_path(prefix: str, key: str, ext: str) -> Path:
    return CACHE_DIR / f"{prefix}_{_hash(key)}.{ext}"


# --- Wikipedia ---------------------------------------------------------

WIKI_API = "https://ja.wikipedia.org/w/api.php"


def fetch_wikipedia_image(keyword: str) -> Path | None:
    """日本語 Wikipedia から人物の代表画像を取得して PNG で保存。"""
    cache = _cache_path("wiki", keyword, "png")
    if cache.exists():
        return cache
    fail_key = f"wiki:{keyword}"
    if fail_key in _FAILED_KEYWORDS:
        return None

    # Step 1: ページ情報を取得
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "original",
        "titles": keyword,
        "redirects": 1,
    }
    try:
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=3)
        r.raise_for_status()
        data = r.json()
    except Exception:
        _FAILED_KEYWORDS.add(fail_key)
        return None

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return None
    page = next(iter(pages.values()))
    original = page.get("original")
    if not original:
        return None
    src = original.get("source")
    if not src:
        return None

    # Step 2: 画像をダウンロード
    try:
        r = requests.get(src, headers=HEADERS, timeout=20)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        # 高さ 1080 まで縮小 (大きい画像対策)
        if img.height > 1080:
            ratio = 1080 / img.height
            img = img.resize((int(img.width * ratio), 1080), Image.LANCZOS)
        img.save(cache, "PNG")
        return cache
    except Exception:
        return None


# --- いらすとや -------------------------------------------------------

IRASUTOYA_BASE = "https://www.irasutoya.com"
IRASUTOYA_SEARCH = "https://www.irasutoya.com/search?q={query}"


def fetch_irasutoya(keyword: str) -> Path | None:
    """いらすとや検索で先頭の画像を取得。
    注意: スクレイピングは利用規約・robots.txt を尊重し、節度ある回数に留める。
    """
    cache = _cache_path("iras", keyword, "png")
    if cache.exists():
        return cache
    fail_key = f"iras:{keyword}"
    if fail_key in _FAILED_KEYWORDS:
        return None

    url = IRASUTOYA_SEARCH.format(query=urllib.parse.quote(keyword))
    try:
        time.sleep(0.5)  # rate limit
        r = requests.get(url, headers=HEADERS, timeout=3)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        _FAILED_KEYWORDS.add(fail_key)
        return None

    # 検索結果の最初の記事リンクを取得
    article = soup.select_one("article.hentry a, .boxim a")
    if not article:
        return None
    page_url = article.get("href")
    if not page_url:
        return None
    if page_url.startswith("/"):
        page_url = IRASUTOYA_BASE + page_url

    # 詳細ページで画像 URL を取得
    try:
        time.sleep(1.0)
        r = requests.get(page_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        return None

    img_tag = soup.select_one(".entry img, article img")
    if not img_tag or not img_tag.get("src"):
        return None
    img_url = img_tag["src"]

    try:
        time.sleep(0.5)
        r = requests.get(img_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        img.save(cache, "PNG")
        return cache
    except Exception:
        return None


# --- Maps ---------------------------------------------------------------

WORLD_BLANK = ASSETS_DIR / "backgrounds" / "world_blank.png"
ASIA_BLANK = ASSETS_DIR / "backgrounds" / "asia_blank.png"


def make_world_map(highlight: str | None = None) -> Path:
    """白地図 (世界) に highlight の国を緑で塗る。"""
    from src.video.map_renderer import render_world_map
    return render_world_map(highlight=highlight)


def make_asia_map(highlight: str | None = None) -> Path:
    from src.video.map_renderer import render_asia_map
    return render_asia_map(highlight=highlight)


def make_europe_map(highlight: str | None = None) -> Path:
    from src.video.map_renderer import render_europe_map
    return render_europe_map(highlight=highlight)


def make_blank(color: tuple[int, int, int] = (255, 255, 255)) -> Path:
    cache = _cache_path("blank", str(color), "png")
    if cache.exists():
        return cache
    Image.new("RGB", (1920, 1080), color).save(cache, "PNG")
    return cache


# パステル背景 (blank よりマシに見える代替)
_BLANK_PALETTE = [
    (252, 239, 225),   # クリーム
    (230, 242, 253),   # 淡い空色
    (245, 235, 245),   # ラベンダー
    (232, 245, 232),   # ミント
    (253, 236, 230),   # ピンク
]


def make_themed_blank(seed: str = "") -> Path:
    """単なる白よりマシな、淡い色のグラデーション背景。キーワードごとに色が決まる。"""
    import hashlib
    from PIL import ImageFilter
    import numpy as np
    idx = int(hashlib.sha1(seed.encode("utf-8")).hexdigest(), 16) % len(_BLANK_PALETTE)
    base_color = _BLANK_PALETTE[idx]
    cache = _cache_path("grad", f"{idx}_{base_color}", "png")
    if cache.exists():
        return cache

    # 縦方向グラデーション (明→同色)
    w, h = 1920, 1080
    r, g, b = base_color
    top = (min(255, r + 15), min(255, g + 15), min(255, b + 15))
    bot = (max(0, r - 10), max(0, g - 10), max(0, b - 10))
    gradient = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        t = y / (h - 1)
        gradient[y, :, 0] = int(top[0] + (bot[0] - top[0]) * t)
        gradient[y, :, 1] = int(top[1] + (bot[1] - top[1]) * t)
        gradient[y, :, 2] = int(top[2] + (bot[2] - top[2]) * t)
    img = Image.fromarray(gradient).filter(ImageFilter.GaussianBlur(radius=1))
    img.save(cache, "PNG")
    return cache


# --- 統合インターフェース --------------------------------------------

def _find_historical_map_key(keyword: str) -> str | None:
    """「モンゴル帝国1215年」等のキーワードから歴史地図キーを推定。"""
    kw = (keyword or "").lower()
    if "1215" in kw or "チンギス" in keyword or "モンゴル帝国" in keyword:
        return "1215_mongol_empire"
    # TODO: 他の時代
    return None


def _resolve_main(hint: ImageHint) -> Path | None:
    """overlay を考えずにメイン背景だけ取る。
    優先順位:
        1. OpenAI gpt-image-1 (API キーあり時、illustration 用)
        2. Wikipedia (portrait/photo 用)
        3. いらすとや (illustration フォールバック)
        4. 地図レンダラ
    """
    if hint.type in (BackgroundType.PORTRAIT, BackgroundType.PHOTO):
        p = fetch_wikipedia_image(hint.keyword)
        if p:
            return p
    elif hint.type == BackgroundType.ILLUSTRATION:
        # OpenAI API キーあれば優先
        try:
            from src.video.openai_image import (
                is_available as oai_available,
                generate_scene_image,
                translate_keyword,
            )
            if oai_available():
                prompt = translate_keyword(hint.keyword)
                p = generate_scene_image(prompt)
                if p:
                    return p
        except ImportError:
            pass
        # フォールバック: いらすとや
        p = fetch_irasutoya(hint.keyword)
        if p:
            return p
    elif hint.type == BackgroundType.MAP_WORLD:
        return make_world_map(hint.highlight or hint.keyword)
    elif hint.type == BackgroundType.MAP_REGION:
        kw = hint.highlight or hint.keyword or ""
        if any(w in kw for w in ("中国", "モンゴル", "日本", "韓国", "朝鮮", "アジア", "唐", "宋", "明", "清", "元")):
            return make_asia_map(hint.highlight or hint.keyword)
        if any(w in kw for w in ("ハンガリー", "ヨーロッパ", "ドイツ", "フランス", "イタリア", "オーストリア", "ローマ", "ロシア", "イギリス")):
            return make_europe_map(hint.highlight or hint.keyword)
        return make_world_map(hint.highlight or hint.keyword)
    elif hint.type == BackgroundType.MAP_HISTORICAL:
        key = _find_historical_map_key(hint.keyword or hint.highlight or "")
        if key:
            from src.video.historical_maps import render_historical_map
            return render_historical_map(key)
        return make_world_map(hint.highlight or hint.keyword)
    elif hint.type == BackgroundType.BLANK:
        return make_blank()
    return None


def _compose_overlay(main_path: Path, overlay_keyword: str) -> Path:
    """main 画像の上に overlay (肖像/イラスト) を右上あたりに小さく合成。"""
    try:
        overlay_path = fetch_wikipedia_image(overlay_keyword) or fetch_irasutoya(overlay_keyword)
        if not overlay_path:
            return main_path
        base = Image.open(main_path).convert("RGBA")
        ovl = Image.open(overlay_path).convert("RGBA")
        # サイズ: 横 30% 程度
        target_w = int(base.width * 0.30)
        ratio = target_w / ovl.width
        ovl = ovl.resize((target_w, int(ovl.height * ratio)), Image.LANCZOS)
        # 位置: 右上 (10% マージン)
        x = base.width - ovl.width - int(base.width * 0.08)
        y = int(base.height * 0.08)
        base.alpha_composite(ovl, (x, y))
        cache = CACHE_DIR / f"compose_{_hash(str(main_path) + overlay_keyword)}.png"
        base.convert("RGB").save(cache, "PNG")
        return cache
    except Exception:
        return main_path


def fetch_for_hint(hint: ImageHint) -> Path | None:
    """シーンの ImageHint に対応する画像パスを返す。失敗時は themed blank。"""
    try:
        main = _resolve_main(hint)
        if main is None:
            return make_themed_blank(hint.keyword or hint.type.value)
        if hint.overlay_keyword:
            return _compose_overlay(main, hint.overlay_keyword)
        return main
    except Exception:
        pass
    return make_themed_blank(hint.keyword or "blank")


if __name__ == "__main__":
    import sys
    keyword = sys.argv[1] if len(sys.argv) > 1 else "チンギス・カン"
    p = fetch_wikipedia_image(keyword)
    print(f"Wikipedia: {p}")
    p = fetch_irasutoya("怒る人")
    print(f"いらすとや: {p}")
