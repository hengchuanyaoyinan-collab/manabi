"""Natural Earth ベースの地図レンダラ。

世界/アジア地図に指定国を緑で塗り、過去動画と同じスタイルを再現する。
Cartopy が持ってる Natural Earth 110m データを使う。
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cartopy.io.shapereader as shpreader
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from src.config import ASSETS_DIR

CACHE_DIR = ASSETS_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache
def _world() -> gpd.GeoDataFrame:
    path = shpreader.natural_earth(
        resolution="110m", category="cultural", name="admin_0_countries"
    )
    return gpd.read_file(path)


# ---- 日本語 -> 国名 (NAME_JA がある場合は優先) ----
COUNTRY_ALIASES = {
    # 日本語 → NAME (英語)
    "ハンガリー": "Hungary",
    "モンゴル": "Mongolia",
    "中国": "China",
    "日本": "Japan",
    "韓国": "South Korea",
    "ロシア": "Russia",
    "フランス": "France",
    "ドイツ": "Germany",
    "イタリア": "Italy",
    "スペイン": "Spain",
    "イギリス": "United Kingdom",
    "アメリカ": "United States of America",
    "カナダ": "Canada",
    "メキシコ": "Mexico",
    "ブラジル": "Brazil",
    "アルゼンチン": "Argentina",
    "エジプト": "Egypt",
    "トルコ": "Turkey",
    "イラン": "Iran",
    "イラク": "Iraq",
    "サウジアラビア": "Saudi Arabia",
    "インド": "India",
    "パキスタン": "Pakistan",
    "インドネシア": "Indonesia",
    "フィリピン": "Philippines",
    "タイ": "Thailand",
    "ベトナム": "Vietnam",
    "オーストラリア": "Australia",
    "ニュージーランド": "New Zealand",
    "ポーランド": "Poland",
    "オランダ": "Netherlands",
    "ベルギー": "Belgium",
    "オーストリア": "Austria",
    "スイス": "Switzerland",
    "ポルトガル": "Portugal",
    "ギリシャ": "Greece",
    "ノルウェー": "Norway",
    "スウェーデン": "Sweden",
    "フィンランド": "Finland",
    "ウクライナ": "Ukraine",
    "ルーマニア": "Romania",
    "チェコ": "Czechia",
    "スロバキア": "Slovakia",
    # 旧国名・別名
    "古代ローマ": "Italy",
    "ローマ": "Italy",
    "ローマ帝国": "Italy",
    "神聖ローマ帝国": "Germany",
    "唐": "China",
    "宋": "China",
    "明": "China",
    "清": "China",
    "元": "Mongolia",
    "オスマン帝国": "Turkey",
    "ペルシア": "Iran",
    "ビザンチン帝国": "Turkey",
    "ソ連": "Russia",
    "ソビエト連邦": "Russia",
    "プロイセン": "Germany",
    "ウィーン": "Austria",
}


def _find_country_row(world: gpd.GeoDataFrame, keyword: str) -> gpd.GeoSeries | None:
    """日本語 or 英語名で country 行を探す。"""
    if not keyword:
        return None

    # Try NAME_JA first (exact match)
    if "NAME_JA" in world.columns:
        m = world[world["NAME_JA"] == keyword]
        if len(m):
            return m.iloc[0]
        # partial
        m = world[world["NAME_JA"].str.contains(keyword, na=False, regex=False)]
        if len(m):
            return m.iloc[0]

    # Try aliases
    english = COUNTRY_ALIASES.get(keyword)
    if english:
        m = world[world["NAME"] == english]
        if len(m):
            return m.iloc[0]

    # Try direct English match
    m = world[world["NAME"] == keyword]
    if len(m):
        return m.iloc[0]

    # Partial English
    m = world[world["NAME"].str.contains(keyword, na=False, regex=False)]
    if len(m):
        return m.iloc[0]

    return None


def render_world_map(
    highlight: str | None = None,
    *,
    extent: tuple[float, float, float, float] | None = None,
    out_path: Path | None = None,
    fill_color: str = "#4ade80",          # 鮮やかな緑
    other_color: str = "#ffffff",
    ocean_color: str = "#eef5fb",
    border_color: str = "#b5b5b5",
    size: tuple[int, int] = (1920, 1080),
    dpi: int = 100,
    label: bool = True,
) -> Path:
    """白地図ベースで highlight 国を緑で塗る。

    Args:
        highlight: 強調する国 (日本語 or 英語名)
        extent: (xmin, xmax, ymin, ymax) 地図の範囲。None は世界全体
    """
    import hashlib
    key = f"{highlight}_{extent}_{fill_color}_{size}"
    cache = CACHE_DIR / f"map_{hashlib.sha1(key.encode()).hexdigest()[:12]}.png"
    if out_path:
        cache = out_path
    if cache.exists() and not out_path:
        return cache

    world = _world()
    highlight_row = _find_country_row(world, highlight) if highlight else None

    fig_w = size[0] / dpi
    fig_h = size[1] / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor(ocean_color)
    ax.set_facecolor(ocean_color)

    # Draw all countries (white)
    world.plot(ax=ax, color=other_color, edgecolor=border_color, linewidth=0.5)

    # Highlight
    if highlight_row is not None:
        gpd.GeoDataFrame([highlight_row], crs=world.crs).plot(
            ax=ax, color=fill_color, edgecolor="#333333", linewidth=0.8
        )

    # Extent
    if extent:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
    else:
        ax.set_xlim(-170, 180)
        ax.set_ylim(-60, 85)

    ax.set_axis_off()
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    cache.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(cache, dpi=dpi, facecolor=ocean_color, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return cache


def render_asia_map(highlight: str | None = None, **kwargs) -> Path:
    """アジア + 西洋の一部を含む範囲で地図。"""
    return render_world_map(
        highlight=highlight,
        extent=(40, 155, -10, 70),  # アジア〜中東
        **kwargs,
    )


def render_europe_map(highlight: str | None = None, **kwargs) -> Path:
    """欧州 + 西アジアの範囲。"""
    return render_world_map(
        highlight=highlight,
        extent=(-15, 60, 30, 72),
        **kwargs,
    )


def render_mongol_empire_map() -> Path:
    """モンゴル帝国最盛期 (13 世紀)。複数国を茶色で。"""
    # TODO: 歴史地図は別途ハンドメイドデータが必要。今はプレースホルダ。
    return render_asia_map(highlight="Mongolia", fill_color="#8b6f47")


if __name__ == "__main__":
    p = render_world_map(highlight="ハンガリー", out_path=Path("/tmp/test_map_hungary.png"))
    print(p)
    p = render_asia_map(highlight="モンゴル", out_path=Path("/tmp/test_map_mongolia.png"))
    print(p)
