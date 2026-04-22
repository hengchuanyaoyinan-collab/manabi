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
from src.types import BackgroundType, ImageHint


CACHE_DIR = ASSETS_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

UA = "PunpunChannelBot/0.1 (educational; contact: punpun@example.com)"
HEADERS = {"User-Agent": UA}


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
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
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

    url = IRASUTOYA_SEARCH.format(query=urllib.parse.quote(keyword))
    try:
        time.sleep(1.0)  # rate limit
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
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
    """白地図 (世界) に highlight の国を緑で塗る。
    現状: assets が無ければ単色の代替画像を返す。
    本実装はあとで Pillow + GeoPandas で正確に塗る予定。
    """
    cache = _cache_path("map_world", highlight or "", "png")
    if cache.exists():
        return cache
    img = Image.new("RGB", (1920, 1080), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    msg = f"World Map (highlight: {highlight or '-'})"
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48
        )
    except OSError:
        font = ImageFont.load_default()
    draw.text((40, 40), msg, fill=(60, 60, 60), font=font)
    img.save(cache, "PNG")
    return cache


def make_blank(color: tuple[int, int, int] = (255, 255, 255)) -> Path:
    cache = _cache_path("blank", str(color), "png")
    if cache.exists():
        return cache
    Image.new("RGB", (1920, 1080), color).save(cache, "PNG")
    return cache


# --- 統合インターフェース --------------------------------------------

def fetch_for_hint(hint: ImageHint) -> Path | None:
    """シーンの ImageHint に対応する画像パスを返す。失敗時は blank。"""
    try:
        if hint.type in (BackgroundType.PORTRAIT, BackgroundType.PHOTO):
            p = fetch_wikipedia_image(hint.keyword)
            if p:
                return p
        elif hint.type == BackgroundType.ILLUSTRATION:
            p = fetch_irasutoya(hint.keyword)
            if p:
                return p
        elif hint.type in (
            BackgroundType.MAP_WORLD,
            BackgroundType.MAP_REGION,
            BackgroundType.MAP_HISTORICAL,
        ):
            return make_world_map(hint.highlight or hint.keyword)
        elif hint.type == BackgroundType.BLANK:
            return make_blank()
    except Exception:
        pass
    return make_blank((250, 250, 250))


if __name__ == "__main__":
    import sys
    keyword = sys.argv[1] if len(sys.argv) > 1 else "チンギス・カン"
    p = fetch_wikipedia_image(keyword)
    print(f"Wikipedia: {p}")
    p = fetch_irasutoya("怒る人")
    print(f"いらすとや: {p}")
