"""歴史地図レンダラ。

Natural Earth の現代国境データを元に、歴史上の国家を近似的に
塗り分けて描画する。手動で国名ごとの領域 (geometry) を定義。

対応する時代:
- 1215: モンゴル帝国 (チンギスハン 中都占領時)
- 1250: モンゴル帝国最大期
- 1世紀: 古代ローマ帝国最大期 (五賢帝時代)
- 1550: 戦国時代日本
- etc.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

import cartopy.io.shapereader as shpreader
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

from src.config import ASSETS_DIR

CACHE_DIR = ASSETS_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache
def _world() -> gpd.GeoDataFrame:
    path = shpreader.natural_earth(
        resolution="110m", category="cultural", name="admin_0_countries"
    )
    return gpd.read_file(path)


# -------- 時代別の国家定義 --------

def _union_countries(names: list[str]) -> Polygon | None:
    w = _world()
    rows = w[w["NAME"].isin(names)]
    if len(rows) == 0:
        return None
    return unary_union(rows.geometry)


def _bbox_clip(geom, bbox: tuple[float, float, float, float]):
    """bbox (xmin, ymin, xmax, ymax) でクリップ。"""
    if geom is None:
        return None
    return geom.intersection(box(*bbox))


# 1215 年 モンゴル帝国 (チンギスハン 中都占領時)
#
# 近似領域:
# - モンゴル (茶): 現代モンゴル + 内蒙古 + 中国東北部北部 (バイカル湖周辺)
# - 西夏 (緑): 中国北西部 (寧夏・甘粛)
# - 金 (黄): 中国東北部〜華北
# - 南宋 (薄緑): 中国南部
# - 高麗 (黄): 朝鮮半島
# - 日本 (緑): 日本列島
# - 吐蕃諸王国 (白): チベット
# - 大理 (緑): 雲南
# - パガン (茶): ミャンマー
# - ホラズム (紫): 中央アジア〜イラン
# - 奴隷王朝 (オレンジ): 北インド
# - 大真 (緑): 中国東北部南部 (沿海州)
# - ヴォルガ・ブルガル (ピンク): ロシア南部
# - キエフ大公国 (紫): ウクライナ
# - 神聖ローマ帝国 (ピンク): ドイツ周辺
# - アッバース朝 (緑): 中東
HISTORICAL_MAPS = {
    "1215_mongol_empire": {
        "title": "1215 年 モンゴル帝国と周辺諸国",
        "extent": (40, -10, 155, 70),  # (xmin, ymin, xmax, ymax) アジア〜中東
        "bg_color": "#c8e4f5",
        "land_color": "#f5f0e8",  # 陸地ベース (まだ塗ってない土地)
        "regions": [
            {"name": "モンゴル", "label_xy": (103, 47), "color": "#b8885f",
             "geometry": "union_bbox", "countries": ["Mongolia"], "extras": [("China", (73, 41, 135, 53))]},
            {"name": "西夏", "label_xy": (104, 38), "color": "#9ccc7a",
             "geometry": "bbox", "bbox": (96, 34, 110, 42)},
            {"name": "金", "label_xy": (117, 40), "color": "#e8d76a",
             "geometry": "bbox", "bbox": (110, 34, 127, 45)},
            {"name": "南宋", "label_xy": (112, 28), "color": "#9fd79e",
             "geometry": "bbox", "bbox": (99, 22, 122, 34)},
            {"name": "高麗", "label_xy": (128, 38), "color": "#e8d76a",
             "geometry": "country", "countries": ["North Korea", "South Korea"]},
            {"name": "日本", "label_xy": (138, 36), "color": "#9ccc7a",
             "geometry": "country", "countries": ["Japan"]},
            {"name": "(吐蕃諸王国)", "label_xy": (90, 32), "color": "#ffffff",
             "geometry": "bbox", "bbox": (78, 28, 100, 36)},
            {"name": "大理", "label_xy": (102, 25), "color": "#9fd79e",
             "geometry": "bbox", "bbox": (98, 22, 106, 28)},
            {"name": "パガン", "label_xy": (96, 21), "color": "#c19060",
             "geometry": "country", "countries": ["Myanmar"]},
            {"name": "ホラズム", "label_xy": (62, 38), "color": "#a673b9",
             "geometry": "country",
             "countries": ["Iran", "Turkmenistan", "Uzbekistan", "Afghanistan", "Tajikistan"]},
            {"name": "奴隷王朝", "label_xy": (75, 26), "color": "#d9a06b",
             "geometry": "bbox", "bbox": (67, 20, 88, 32)},
            {"name": "大真", "label_xy": (131, 44), "color": "#9fd79e",
             "geometry": "bbox", "bbox": (125, 42, 135, 48)},
            {"name": "チャンパ", "label_xy": (108, 13), "color": "#c19060",
             "geometry": "country", "countries": ["Vietnam"]},
            {"name": "クメール", "label_xy": (104, 13), "color": "#a673b9",
             "geometry": "country", "countries": ["Cambodia", "Laos", "Thailand"]},
            {"name": "チョーラ", "label_xy": (79, 11), "color": "#d97575",
             "geometry": "country", "countries": ["Sri Lanka"], "extras_bbox": (77, 8, 82, 14)},
            {"name": "アッバース朝", "label_xy": (47, 33), "color": "#9fd79e",
             "geometry": "country",
             "countries": ["Iraq", "Saudi Arabia", "Jordan", "Syria", "Kuwait",
                           "Oman", "Yemen", "United Arab Emirates", "Qatar", "Lebanon"]},
            {"name": "ヴォルガ・ブルガル", "label_xy": (50, 55), "color": "#e8a6c5",
             "geometry": "bbox", "bbox": (46, 52, 60, 60)},
            {"name": "キエフ大公国", "label_xy": (35, 53), "color": "#a673b9",
             "geometry": "country", "countries": ["Ukraine", "Belarus", "Moldova"]},
            {"name": "ハンガリー", "label_xy": (22, 47), "color": "#d97575",
             "geometry": "country", "countries": ["Hungary"]},
            {"name": "クマン", "label_xy": (40, 48), "color": "#e8d76a",
             "geometry": "bbox", "bbox": (32, 44, 50, 52)},
            {"name": "神聖ローマ帝国", "label_xy": (11, 50), "color": "#e8a6c5",
             "geometry": "country",
             "countries": ["Germany", "Austria", "Czechia", "Switzerland", "Slovenia"]},
            {"name": "フランス", "label_xy": (2, 47), "color": "#a673b9",
             "geometry": "country", "countries": ["France"]},
            {"name": "アイユーブ朝", "label_xy": (33, 30), "color": "#9fd79e",
             "geometry": "country", "countries": ["Egypt"]},
            {"name": "マムルーク朝", "label_xy": (31, 24), "color": "#9fd79e",
             "geometry": "bbox", "bbox": (28, 22, 37, 28)},
            {"name": "エチオピア", "label_xy": (40, 9), "color": "#d9a06b",
             "geometry": "country", "countries": ["Ethiopia", "Somalia", "Eritrea"]},
            {"name": "マクリア", "label_xy": (32, 17), "color": "#e8d76a",
             "geometry": "country", "countries": ["Sudan", "South Sudan"]},
            {"name": "カネム帝国", "label_xy": (16, 14), "color": "#e8a6c5",
             "geometry": "country", "countries": ["Chad", "Niger"]},
            {"name": "アロディア", "label_xy": (26, 15), "color": "#e8d76a",
             "geometry": "bbox", "bbox": (26, 12, 36, 17)},
        ],
    },
    # TODO: 他の時代も追加
}


def _resolve_geometry(region: dict, world: gpd.GeoDataFrame):
    g = region.get("geometry", "country")
    if g == "country":
        names = region.get("countries", [])
        rows = world[world["NAME"].isin(names)]
        if len(rows) == 0:
            return None
        geom = unary_union(rows.geometry)
        if "extras_bbox" in region:
            geom = unary_union([geom, box(*region["extras_bbox"])])
        return geom
    if g == "bbox":
        return box(*region["bbox"])
    if g == "union_bbox":
        names = region.get("countries", [])
        rows = world[world["NAME"].isin(names)]
        geoms = [unary_union(rows.geometry)] if len(rows) else []
        for _ctry, bb in region.get("extras", []):
            geoms.append(box(*bb))
        if not geoms:
            return None
        return unary_union(geoms)
    return None


def render_historical_map(
    key: str,
    out_path: Path | None = None,
    size: tuple[int, int] = (1920, 1080),
    dpi: int = 100,
    with_texture: bool = True,
) -> Path:
    """時代キーを指定して歴史地図を描く。"""
    if key not in HISTORICAL_MAPS:
        raise KeyError(f"Unknown historical map key: {key}")
    spec = HISTORICAL_MAPS[key]

    cache_key = f"{key}_{size}_{dpi}_{with_texture}"
    cache = CACHE_DIR / f"histmap_{hashlib.sha1(cache_key.encode()).hexdigest()[:12]}.png"
    if out_path:
        cache = out_path
    if cache.exists() and not out_path:
        return cache

    world = _world()
    extent = spec["extent"]  # (xmin, ymin, xmax, ymax)

    fig_w = size[0] / dpi
    fig_h = size[1] / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.set_facecolor(spec["bg_color"])
    fig.patch.set_facecolor(spec["bg_color"])

    # ベースの陸地 (塗ってない土地用)
    world_clip = world.copy()
    world_clip["geometry"] = world_clip.geometry.intersection(box(*extent))
    world_clip.plot(ax=ax, color=spec["land_color"], edgecolor="#d0c8bd", linewidth=0.6)

    # 日本語フォントを登録
    jp_font = None
    for fp in [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    ]:
        if Path(fp).exists():
            jp_font = fp
            break

    # 歴史国家を塗る
    clip_bbox = box(*extent)
    for region in spec["regions"]:
        geom = _resolve_geometry(region, world)
        if geom is None:
            continue
        clipped = geom.intersection(clip_bbox)
        if clipped.is_empty:
            continue
        gdf = gpd.GeoDataFrame(
            {"name": [region["name"]]}, geometry=[clipped], crs=world.crs
        )
        gdf.plot(ax=ax, color=region["color"], edgecolor="#7a6f5c", linewidth=0.8, alpha=0.90)

        # ラベル
        x, y = region["label_xy"]
        if jp_font:
            from matplotlib import font_manager as fm
            fp = fm.FontProperties(fname=jp_font, size=11)
            ax.text(x, y, region["name"], ha="center", va="center",
                    fontproperties=fp, color="#202020",
                    bbox=None)
        else:
            ax.text(x, y, region["name"], ha="center", va="center", fontsize=9,
                    color="#202020")

    # 範囲
    ax.set_xlim(extent[0], extent[2])
    ax.set_ylim(extent[1], extent[3])
    ax.set_axis_off()
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    cache.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(cache, dpi=dpi, facecolor=spec["bg_color"], bbox_inches="tight", pad_inches=0)
    plt.close(fig)

    # 簡易テクスチャ (少しブラー + セピア)
    if with_texture:
        from PIL import Image, ImageFilter, ImageEnhance
        img = Image.open(cache).convert("RGB")
        # 非常に軽いブラーで手描き感
        img = img.filter(ImageFilter.GaussianBlur(radius=0.4))
        # 彩度を少し下げる
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.92)
        img.save(cache)

    return cache


if __name__ == "__main__":
    p = render_historical_map("1215_mongol_empire", Path("/tmp/test_hist_map.png"))
    print(p)
