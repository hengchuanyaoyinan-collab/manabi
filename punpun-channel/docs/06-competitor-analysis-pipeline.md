# 🔍 競合分析パイプライン

YouTube → Data API → Claude Code → 自動分析 の仕組み。

## 流れ

```
1. scripts/analyze-competitors.py "ぴよぴーよ速報"
   │
   ├→ YouTube Data API v3 でチャンネル検索
   │   └ チャンネル ID・統計を取得
   │
   ├→ 最新 30 本の動画メタデータを取得
   │   └ タイトル・再生数・タグ・公開日・尺
   │
   ├→ 再生数上位 3 本の字幕 (文字起こし) を取得
   │   └ youtube-transcript-api で自動字幕取得
   │
   ├→ 全部を claude CLI に渡して分析
   │   └ タイトル構文・語彙・人気題材・演出を抽出
   │
   └→ config/insights.json に保存
```

## セットアップ (1 回だけ)

### YOUTUBE_API_KEY の取得

1. https://console.cloud.google.com/ でプロジェクト作成 (既存でも可)
2. 「API とサービス」→「ライブラリ」→ `YouTube Data API v3` を有効化
3. 「認証情報」→「認証情報を作成」→「API キー」
4. 表示された `AIza...` をコピー
5. `punpun-channel/.env` に追加:
   ```
   YOUTUBE_API_KEY=AIza...
   ```

**所要時間: 5 分。無料枠 10,000 quota/日 で十分。**

## 使い方

### 1 チャンネル分析
```bash
python scripts/analyze-competitors.py "ぴよぴーよ速報"
```

### 複数チャンネル一気に
```bash
python scripts/analyze-competitors.py \
    "ぴよぴーよ速報" \
    "大人の学び直しTV" \
    "ホモサピのいい話"
```

### 深掘り (動画 50 本 + 字幕 5 本)
```bash
python scripts/analyze-competitors.py --deep "ぴよぴーよ速報"
```

## 出力例

```
============================================================
▶ 分析: ぴよぴーよ速報
============================================================
📺 分析対象: ぴよぴーよ速報 (UC...)
   登録者: 1,080,000, 動画: 228
   動画取得: 30 本
   字幕取得: 小学生でもわかる古代の原子論
   字幕取得: 歴史的偉人が現代人を論破するアニメ第1〜53弾
   字幕取得: 小学生でもわかるアインシュタインの哲学
🤖 Claude で分析中 (数分かかります)...
✅ 保存: config/insights.json

📊 サマリー: ひよこキャラが学問・偉人を『小学生でもわかる』語り口で...

🏷 タイトルパターン:
  - 「小学生でもわかる〇〇」が定番
  - 数字 (%、年) を入れて具体性を出す
  - 大胆な主張を「」で強調

🎯 新題材チャンス:
  - 小学生でもわかる量子力学
  - 小学生でもわかる西洋哲学
  - 歴史上の皇帝の失敗談
```

## insights.json の構造

```json
{
  "lastUpdated": "2026-04-24T09:00:00",
  "analyses": [
    {
      "channelId": "UC...",
      "channelTitle": "ぴよぴーよ速報",
      "analyzedAt": "2026-04-24T09:00:00",
      "videosCount": 30,
      "insights": {
        "channel_summary": "...",
        "title_patterns": ["..."],
        "vocabulary_trends": ["..."],
        "pacing": "...",
        "high_view_topics": ["..."],
        "low_view_topics": ["..."],
        "opportunity_topics": ["..."],
        "hooks_and_techniques": ["..."],
        "risks": ["..."],
        "actionable_advice": ["..."]
      },
      "top3Videos": [...]
    }
  ]
}
```

## ぷんぷんの台本生成への自動反映 (将来)

今後 `actionable_advice` を定期的に `templates/script-prompt.md` にマージし、
`opportunity_topics` を `config/topic-queue.json` に追加する自動化を予定。

## 定期実行

週 1 回の競合チェックを Windows タスクスケジューラに登録可能:
```powershell
# 毎週月曜 09:00 に競合分析
schtasks /create /tn "PunpunCompetitorAnalysis" /tr "python scripts/analyze-competitors.py ぴよぴーよ速報" /sc weekly /d MON /st 09:00
```

## コスト

- YouTube Data API v3: 無料枠 10,000 ユニット/日
  - 1 チャンネル分析 = ~100 ユニット程度
  - 週 1 分析なら 100 チャンネルまで無料
- Claude Haiku 分析: Max 契約内 (追加料金 0)

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `YOUTUBE_API_KEY が設定されていません` | .env 未設定 | .env に追加 |
| `quotaExceeded` | 1 日 10,000 超 | 翌日に再実行、または API キー追加 |
| 字幕取得失敗 | 動画が字幕無効 | エラー無視、メタデータのみで分析 |
| `claude CLI が見つかりません` | Claude Code 未導入 | Claude Code インストール |
