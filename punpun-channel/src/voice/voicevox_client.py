"""VOICEVOX Engine HTTP API クライアント。

ユーザーの Windows PC で VOICEVOX を起動しておき、その HTTP API
(http://localhost:50021) を叩いて音声合成する。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import voice_config, env


class VoiceVoxClient:
    """VOICEVOX Engine と HTTP で会話するクライアント。"""

    def __init__(self, base_url: str | None = None):
        cfg = voice_config()
        self.base_url = base_url or env("VOICEVOX_URL", cfg.get("engineUrl", "http://localhost:50021"))
        self.params = cfg.get("params", {})

    # --- low level API -------------------------------------------------

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/version", timeout=3)
            return r.ok
        except Exception:
            return False

    def list_speakers(self) -> list[dict]:
        r = requests.get(f"{self.base_url}/speakers", timeout=5)
        r.raise_for_status()
        return r.json()

    def audio_query(self, text: str, speaker_id: int) -> dict:
        r = requests.post(
            f"{self.base_url}/audio_query",
            params={"text": text, "speaker": speaker_id},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def synthesis(self, query: dict, speaker_id: int) -> bytes:
        r = requests.post(
            f"{self.base_url}/synthesis",
            params={"speaker": speaker_id},
            data=json.dumps(query),
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        r.raise_for_status()
        return r.content

    # --- high level API -----------------------------------------------

    def speak_to_file(
        self,
        text: str,
        out_path: Path,
        speaker_id: int | None = None,
    ) -> Path:
        """1 セリフを WAV にする。"""
        cfg = voice_config()
        sid = speaker_id or cfg.get("speaker", {}).get("id")
        if sid is None:
            raise ValueError("VOICEVOX speaker id is not configured (config/voice.json)")

        query = self.audio_query(text, sid)
        # apply tunable params
        for k, default in (
            ("speedScale", 1.0),
            ("pitchScale", 0.0),
            ("intonationScale", 1.0),
            ("volumeScale", 1.0),
            ("prePhonemeLength", 0.1),
            ("postPhonemeLength", 0.1),
        ):
            if k in self.params:
                query[k] = self.params.get(k, default)

        wav = self.synthesis(query, sid)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(wav)
        return out_path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true", help="Engine 接続を確認")
    p.add_argument("--text", help="この文を喋る")
    p.add_argument("--speaker", type=int, help="speaker id")
    p.add_argument("--out", default="voice_test.wav")
    args = p.parse_args()

    client = VoiceVoxClient()
    if not client.health():
        print(
            "❌ VOICEVOX Engine に接続できませんでした",
            f"  -> {client.base_url}",
            "  Windows で VOICEVOX を起動してから再実行してください。",
            sep="\n",
        )
        return 1
    print(f"✅ VOICEVOX Engine OK ({client.base_url})")

    if args.test and not args.text:
        speakers = client.list_speakers()
        print(f"利用可能スピーカー: {len(speakers)} 名")
        for s in speakers[:5]:
            print(f"  - {s['name']}: styles={[st['id'] for st in s.get('styles', [])][:5]}")
        return 0

    if args.text:
        out = Path(args.out)
        client.speak_to_file(args.text, out, speaker_id=args.speaker)
        print(f"✅ 出力: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
