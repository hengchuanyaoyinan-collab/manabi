"""環境チェックスクリプト。

ユーザーの PC で必要なツール・設定が整っているか診断する。
パイプライン実行前にこれを走らせると安心。

使い方:
    python3 scripts/check-env.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def check(label: str, ok: bool, detail: str = "", warning: bool = False) -> bool:
    if ok:
        mark = "✅"
    elif warning:
        mark = "⚠️ "
    else:
        mark = "❌"
    print(f"  {mark} {label}{(' ' + detail) if detail else ''}")
    return ok


def cmd_version(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        return (out.stdout or out.stderr).split("\n")[0].strip()
    except Exception:
        return None


def main() -> int:
    print("\n=== ぷんぷんチャンネル 環境診断 ===\n")
    all_ok = True

    print("[1] 必須ツール")
    py = sys.version.split()[0]
    all_ok &= check(f"Python {py}", sys.version_info >= (3, 10), "(>=3.10 推奨)")

    node = cmd_version(["node", "--version"])
    all_ok &= check(f"Node.js {node or '未インストール'}", node is not None, "(Remotion 用、現状 Phase 2)")

    ffmpeg = cmd_version(["ffmpeg", "-version"])
    all_ok &= check(f"FFmpeg", ffmpeg is not None, ffmpeg or "")

    git = cmd_version(["git", "--version"])
    all_ok &= check(f"Git", git is not None, git or "")

    print("\n[2] Python パッケージ")
    for pkg, mod in [
        ("requests", "requests"),
        ("pydantic", "pydantic"),
        ("Pillow", "PIL"),
        ("beautifulsoup4", "bs4"),
        ("pyyaml", "yaml"),
        ("python-dotenv", "dotenv"),
    ]:
        try:
            __import__(mod)
            check(pkg, True)
        except ImportError:
            check(pkg, False, "→ pip install -r requirements.txt")
            all_ok = False

    print("\n[3] VOICEVOX (本番音声合成)")
    try:
        import requests
        r = requests.get("http://localhost:50021/version", timeout=2)
        if r.ok:
            check(f"VOICEVOX Engine 起動中 (v{r.text})", True)
        else:
            check("VOICEVOX Engine 応答なし", False, warning=True)
    except Exception:
        check(
            "VOICEVOX Engine 未起動",
            False,
            "→ VOICEVOX を起動してください (任意: 起動してなければ open-jtalk が使われる)",
            warning=True,
        )

    print("\n[4] 設定ファイル")
    project = Path(__file__).resolve().parent.parent
    for p in ["config/channel.json", "config/voice.json", "config/style.json", "config/topic-queue.json"]:
        check(p, (project / p).exists())

    print("\n[5] YouTube 認証 (本番投稿)")
    yt_token = project / "config/youtube-token.json"
    yt_oauth = project / "config/oauth-client.json"
    if yt_token.exists():
        check("youtube-token.json (認証済み)", True)
    elif yt_oauth.exists():
        check("oauth-client.json はあるが未認証", True, "→ python3 src/upload/youtube_oauth.py")
    else:
        check(
            "YouTube 認証 未設定",
            False,
            "→ 投稿しないなら不要。本番運用時に docs/01-setup.md 参照",
            warning=True,
        )

    print("\n[6] アセット (任意)")
    char = project / "assets/characters/punpun.png"
    if char.exists():
        check(f"ぷんぷんキャラ画像", True)
    else:
        check(f"ぷんぷんキャラ画像 未配置", True, "(代替キャラが使われます)")

    fonts = list((project / "assets/fonts").glob("*.ttf")) + list((project / "assets/fonts").glob("*.otf"))
    if fonts:
        check(f"フォント ({len(fonts)} 個)", True, ", ".join(f.name for f in fonts[:3]))
    else:
        check("カスタム日本語フォント 未配置", True, "(システムフォントが使われます)")

    print("\n" + "=" * 30)
    if all_ok:
        print("\n✅ 必須項目はすべて OK。パイプラインを実行できます。\n")
        print("次のステップ:")
        print("  python3 src/orchestrator.py --script test_data/elizabeth_bathory_short.json --test\n")
        return 0
    print("\n⚠️  いくつか未設定です。上の指示に従ってセットアップしてください。\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
