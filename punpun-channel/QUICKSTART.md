# 🚀 クイックスタート (起きた時の最初の 30 分)

このプロジェクトを Windows PC で動かすための最短手順。

## 0. ブランチを取得

PowerShell を開いて:
```powershell
cd $env:USERPROFILE
git clone https://github.com/hengchuanyaoyinan-collab/manabi.git
cd manabi
git checkout claude/add-video-creation-gZ3Et
cd punpun-channel
```

## 1. Python セットアップ (5 分)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. FFmpeg インストール (5 分)

```powershell
winget install Gyan.FFmpeg
```
インストール後、PowerShell を**再起動**して以下で確認:
```powershell
ffmpeg -version
```

## 3. 環境診断 (1 分)

```powershell
python scripts\check-env.py
```
赤 ❌ が出たらメッセージに従う。⚠️ は今は無視 OK。

## 4. テスト動画生成 (5 分)

VOICEVOX 無しでもまず 1 本作れる:
```powershell
python src\orchestrator.py --script test_data\elizabeth_bathory_full.json --test --no-voicevox
```

完了後 `output\test\YYYY-MM-DD_HHMMSS\video.mp4` をダブルクリックして再生。

> 🎉 これで **9 分 55 秒のエリザベート・バートリ動画**が完成しているはずです。
> 声は素朴 (open-jtalk) ですが、構造 (吹き出し+キャラ+章立て) は本番品質。

## 5. VOICEVOX をインストール (10 分)

声を本物にするため:

1. https://voicevox.hiroshiba.jp/ から Windows 版ダウンロード
2. インストーラ実行
3. 起動 → 話者選択 → 動作確認

## 6. VOICEVOX 話者選び (5 分)

VOICEVOX を起動した状態で:
```powershell
python scripts\pick-voicevox-speaker.py
```
`output\voice_samples\` に各話者のサンプル WAV が生成される。
お気に入りを選んで、ID をメモ。

`config\voice.json` を開いて `speaker.id` に書き込み:
```json
{
  "speaker": {
    "id": 8,           // ← ここに ID
    "name": "春日部つむぎ"
  }
}
```

## 7. VOICEVOX で再生成 (5 分)

```powershell
python src\orchestrator.py --script test_data\elizabeth_bathory_full.json --test
```
`--no-voicevox` を外すだけ。声が本物になる。

---

## ここまで完了したら:
- ✅ 動画パイプラインが完全動作
- ✅ ぷんぷんの声が本物 (高音キャラ)
- ✅ 1 本動画を再生可能

## 残りのセットアップ (本番投稿に必要)

別途 30 分:
1. **YouTube API OAuth 設定**: `docs/01-setup.md` の Step 5
2. **過去動画からキャラ画像抽出** (任意): `python scripts\extract-character-from-video.py 過去動画.mp4`
3. **Windows タスクスケジューラ登録** (毎日自動投稿): `scripts\setup-windows-task.ps1` を管理者で実行

---

## ドキュメント全体マップ

| 場所 | 内容 |
|---|---|
| `README.md` | プロジェクト概要 |
| `QUICKSTART.md` | ← 今いるところ |
| `docs/REPORT.md` | 留守番作業の詳細レポート (必読) |
| `docs/SHOWCASE.md` | 実生成動画のスペック |
| `docs/00-vision.md` | ビジョン・収益化戦略 |
| `docs/01-setup.md` | 環境構築の詳細 |
| `docs/02-architecture.md` | システム設計図 |
| `docs/03-workflow.md` | 運用コマンド集 |
| `docs/04-competitor-analysis.md` | ぴよぴーよ等の分析 |
| `docs/05-learnings.md` | 過去動画の学び |

---

## 困った時

- 環境系: `python scripts\check-env.py`
- VOICEVOX: 起動してれば自動で使う、無ければ open-jtalk 代替
- YouTube 投稿: OAuth が要、まずは `--test` で動画生成のみ
- それ以外: `docs/REPORT.md` のトラブルシューティング参照
