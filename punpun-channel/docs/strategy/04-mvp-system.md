# 🚀 MVP 自動投稿システム仕様

**定義**: 人間の手動介入なしで「毎日 19:00 に YouTube に動画が公開される」最小構成。

---

## MVP 達成条件 (Done の定義)

1. ✅ 毎日 19:00 に **新規動画 1 本** が公開される
2. ✅ 人間の作業 = **0 分/日**
3. ✅ 1 週間無停止で回る (7 日連続投稿)
4. ✅ エラー時は Discord 通知が飛ぶ
5. ✅ 動画の品質は現状の v4 以上

## システム構成

```
[cron / Windows Task Scheduler]
        ↓ 毎日 18:30 起動
[src/orchestrator.py]
        ↓
┌─────────────────────────────────────┐
│ 台本 → 音声 → 画像 → 動画 → メタ → 投稿 │
└─────────────────────────────────────┘
        ↓
[YouTube にアップロード、19:00 公開予約]
        ↓
[Discord webhook 通知: "✅ 公開完了"]
        ↓
[翌朝 09:00: 前日動画の成績を取得、insights 更新]
```

## 実装ステータス (2026-04-24 時点)

### ✅ 実装済み
- [x] 題材選定ロジック (`src/generator/topic_selector.py`)
- [x] 台本生成 (`src/generator/script_generator.py`)
- [x] 音声合成 (VOICEVOX + open-jtalk フォールバック)
- [x] 画像取得 (Wikipedia, いらすとや, 地図)
- [x] 動画組立 (アニメーション付き)
- [x] サムネ生成
- [x] オーケストレータ (`src/orchestrator.py`)
- [x] Windows タスクスケジューラ登録 (`scripts/setup-windows-task.ps1`)
- [x] 競合分析 (`scripts/analyze-competitors.py`)

### 🟡 半実装
- [ ] YouTube アップロード (コードは書いた、OAuth 未認証)
- [ ] アナリティクス取得 (記録スキーマあり、fetcher 未作成)

### 🔴 未実装 (MVP に必要)
- [ ] Discord webhook 通知
- [ ] 失敗時自動リトライ
- [ ] 連続成功 7 日間の実証

---

## 未実装の詳細仕様

### 1. Discord webhook 通知

```python
# src/notify/discord.py
import requests, os

def notify(message: str, color: int = 0x2ecc71):
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook:
        return
    requests.post(webhook, json={
        "embeds": [{
            "title": "ブンブンの政治権文録",
            "description": message,
            "color": color,
        }]
    }, timeout=5)
```

`src/orchestrator.py` の最後に:
```python
if report["errors"]:
    notify(f"❌ 失敗: {report['errors'][0]['stage']}", color=0xe74c3c)
else:
    notify(f"✅ 公開: {report['title']}\nhttps://www.youtube.com/watch?v={report['video_id']}")
```

### 2. 失敗時自動リトライ

```python
# src/orchestrator.py 末尾
for attempt in range(3):
    report = run_pipeline(...)
    if not report["errors"]:
        break
    stage = report["errors"][0]["stage"]
    if stage in ("audio", "scenes"):
        # 一時的エラーなら 1 分待ってリトライ
        time.sleep(60)
        continue
    else:
        break  # 永続エラーは諦める
```

### 3. YouTube アナリティクス自動取得

```python
# scripts/fetch-analytics.py (毎朝 09:00)
from googleapiclient.discovery import build
from src.upload.youtube_oauth import get_credentials

youtube = build("youtube", "v3", credentials=get_credentials())
analytics = build("youtubeAnalytics", "v2", credentials=get_credentials())

# 昨日投稿した動画の成績を取得
r = analytics.reports().query(
    ids="channel==MINE",
    startDate=yesterday.isoformat(),
    endDate=today.isoformat(),
    metrics="views,likes,averageViewDuration,averageViewPercentage",
    dimensions="video",
).execute()
```

### 4. 7 日間連続実証

本番稼働前に:
1. test モードで 7 日間連続成功
2. 品質チェック (ランダム 3 本を手動レビュー)
3. 問題なければ本番モード ON

## MVP リリース手順 (順序厳守)

### Day 0: 準備
- [ ] `git pull` で最新コード取得
- [ ] `pip install -r requirements.txt`
- [ ] `winget install Gyan.FFmpeg`
- [ ] VOICEVOX インストール

### Day 1: 認証
- [ ] YouTube Data API キー取得 (`YOUTUBE_API_KEY`)
- [ ] OAuth クライアント作成 (投稿用)
- [ ] `python src/upload/youtube_oauth.py` で認証実行
- [ ] Discord webhook URL 発行 (任意の Discord server で)

### Day 2: テスト
- [ ] `python scripts/check-env.py` で全 ✅ 確認
- [ ] `python src/orchestrator.py --script test_data/chinghis_khan_v4.json --test` で動画生成
- [ ] 生成された MP4 を自分の目で確認

### Day 3〜4: 手動投稿
- [ ] `--test` モードのまま動画 3 本生成
- [ ] 手動で YouTube Studio にアップロード
- [ ] タイトル・サムネ・概要をチェック

### Day 5: 本番テスト投稿
- [ ] `--test` を外して 1 本投稿 (`python src/orchestrator.py`)
- [ ] YouTube に限定公開で上がることを確認
- [ ] 問題なければ公開設定に変更

### Day 6: タスクスケジューラ登録
- [ ] `.\scripts\setup-windows-task.ps1`
- [ ] 翌日 19:00 に自動投稿されることを確認

### Day 7+: 7 日間完走
- [ ] 毎朝 Discord 通知をチェック
- [ ] 週末に全 7 本をレビュー
- [ ] 異常なければ **MVP 完成**

## MVP 完成後の最初の改善

1. **Analytics 自動取得** (翌朝 09:00 に cron)
2. **A/B サムネ** 2 案投稿システム
3. **ElevenLabs 統合** (声質改善)
4. **Shorts 自動生成** (20 秒切り出し投稿)

## MVP の成功指標

- ✅ 1 週間無停止
- ✅ 人間作業 10 分/週 以下
- ✅ 7 本の動画で平均再生数 1,000 超え
- ✅ 最低 1 本が 5,000 再生を超える

達成したら **フェーズ 1 (実験期) に正式突入**。
