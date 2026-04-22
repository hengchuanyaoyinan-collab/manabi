# 動画制作ワークフロー

## 1 本作るのに必要なもの

- 題材 (人物名 or テーマ): 例 「エリザベート・バートリ」
- 認証済みの YouTube アカウント (ぷんぷんチャンネル)
- VOICEVOX が起動済み (Windows GUI)
- インターネット接続 (Wikipedia, いらすとや 等)

## ハッピーパス (毎日 19:00 自動実行)

Windows タスクスケジューラから `python src/orchestrator.py` が自動起動。

```
1. config/topic-queue.json から次の題材を pop
2. claude CLI で台本生成 (5〜10 分)
3. VOICEVOX で音声合成 (3〜5 分)
4. Wikipedia/いらすとや から画像取得 (1〜2 分)
5. 各シーンを Pillow で合成 (1 分)
6. ffmpeg で MP4 化 (3〜5 分)
7. サムネ生成 (10 秒)
8. YouTube API でアップロード (3〜5 分)
9. report.json を出力
```

合計 15〜30 分 / 1 本。

## 手動実行コマンド集

### a. テスト動画 (アップロードしない)

```bash
# 自動で次の題材
python3 src/orchestrator.py --test

# 題材を指定
python3 src/orchestrator.py --topic "ナポレオン" --test

# 既存台本から動画だけ
python3 src/orchestrator.py --script output/test/.../script.json --test

# VOICEVOX 起動してない時 (open-jtalk フォールバック)
python3 src/orchestrator.py --topic "カリグラ帝" --test --no-voicevox
```

### b. 本番投稿

```bash
# 即時公開
python3 src/orchestrator.py --topic "則天武后"

# 公開時刻指定 (ISO8601)
python3 src/orchestrator.py --topic "西太后" --publish-at 2026-04-23T19:00:00+09:00
```

### c. 個別ステップ

```bash
# 台本だけ生成
python3 src/generator/script_generator.py "エカチェリーナ2世" --out output/script.json

# VOICEVOX 接続テスト
python3 src/voice/voicevox_client.py --test

# サムネだけ
python3 src/video/thumbnail_generator.py --text "血の伯爵 / 600人惨殺"

# YouTube OAuth (初回のみ)
python3 src/upload/youtube_oauth.py
```

## 失敗時のリトライ

`output/test/{date}/report.json` で各ステージの状態を確認。

| ステージ | 失敗時の対処 |
|---|---|
| script | claude CLI のレート制限の可能性。少し待って再実行 |
| audio | VOICEVOX が起動してない -> 起動してから再実行 / `--no-voicevox` |
| scenes | Wikipedia/いらすとや への接続失敗。リトライ |
| video | ffmpeg のエラー。`output/.../video.mp4` のログ確認 |
| upload | YouTube API クォータ。OAuth 再認証 |

途中失敗時は、生成済みのファイルを使って `--script` で再開可能。

## クオリティチェックリスト (毎日確認)

- [ ] 動画の長さが 18〜22 分の範囲か
- [ ] 音声が途切れてないか
- [ ] テキストが画面外に出てないか
- [ ] サムネが視認しやすいか
- [ ] タイトルが 100 字以内・煽り過ぎてないか
- [ ] 概要欄に章タイムスタンプが入っているか

## 改善サイクル (週次)

```bash
# 直近 1 週間のレポート集計 (TODO: scripts/weekly-report.py)
python3 scripts/weekly-report.py

# どの題材が伸びたか確認
# config/topic-queue.json の `posted` を見る
```

伸びた動画の傾向 (題材カテゴリ、サムネ文言、タイトル形式) を観察し、
template/script-prompt.md や config/topic-queue.json を更新する。
