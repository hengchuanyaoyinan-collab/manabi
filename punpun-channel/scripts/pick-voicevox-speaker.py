"""VOICEVOX 話者選び補助。

起動中の VOICEVOX Engine から全話者リストを取得し、それぞれを
試聴できるサンプル音声 (1 セリフ) を生成する。

使い方:
    1. VOICEVOX を起動 (Windows GUI)
    2. python3 scripts/pick-voicevox-speaker.py
    3. output/voice_samples/ に各話者の WAV が生成される
    4. お気に入りを聞いてその ID を config/voice.json の speaker.id に設定
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


SAMPLE_TEXT = "どうもこんにちは、ぷんぷんの世事見聞録です。今回は織田信長の人生を見ていきます。"


def main() -> int:
    base = "http://localhost:50021"

    try:
        ver = requests.get(f"{base}/version", timeout=2).text
    except Exception:
        print("❌ VOICEVOX Engine に接続できません (http://localhost:50021)")
        print("   VOICEVOX を起動してから再実行してください。")
        return 1
    print(f"✅ VOICEVOX Engine v{ver}")

    speakers = requests.get(f"{base}/speakers", timeout=10).json()
    out_dir = Path(__file__).resolve().parent.parent / "output" / "voice_samples"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{len(speakers)} 名の話者が見つかりました。サンプルを生成します...\n")

    index_lines = ["# VOICEVOX 話者サンプル一覧", "", "| 話者名 | スタイル | ID | ファイル |", "|---|---|---|---|"]

    total_samples = 0
    for sp in speakers:
        name = sp["name"]
        for style in sp.get("styles", []):
            sid = style["id"]
            style_name = style["name"]
            wav_path = out_dir / f"{name}_{style_name}_{sid}.wav".replace("/", "_")
            try:
                q = requests.post(
                    f"{base}/audio_query",
                    params={"text": SAMPLE_TEXT, "speaker": sid},
                    timeout=20,
                ).json()
                wav = requests.post(
                    f"{base}/synthesis",
                    params={"speaker": sid},
                    json=q,
                    headers={"Content-Type": "application/json"},
                    timeout=60,
                ).content
                wav_path.write_bytes(wav)
                index_lines.append(f"| {name} | {style_name} | {sid} | `{wav_path.name}` |")
                total_samples += 1
                print(f"  ✅ {name} / {style_name} (id={sid})")
            except Exception as e:
                print(f"  ❌ {name} / {style_name}: {e}")

    index_md = out_dir / "INDEX.md"
    index_md.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    print(f"\n✅ {total_samples} 個のサンプルを生成しました")
    print(f"   保存先: {out_dir}")
    print(f"   一覧: {index_md}")
    print()
    print("おすすめ候補 (ぷんぷんの高音キャラ路線):")
    print("  - 春日部つむぎ ノーマル (8): 高めで親しみやすい")
    print("  - 四国めたん ノーマル (2): 高めで元気")
    print("  - 剣崎雌雄 ノーマル (42): 中性的で個性が立つ")
    print("  - 雨晴はう ノーマル (10): 元気で明るい")
    print()
    print("お気に入りの ID を選んだら config/voice.json の speaker.id に設定してください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
