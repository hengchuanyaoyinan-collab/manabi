# 🔁 自己改善ループ (Self-Improvement System)

運営 AI が**自分で学び、自分で改善する**仕組み。

---

## ループの核

```
         ┌──→ 1. 投稿 ────┐
         │              ↓
         │        2. 計測 (再生数・維持率)
         │              ↓
         │        3. 分析 (何が良かったか)
         │              ↓
         │        4. 反映 (次の台本・サムネに)
         │              ↓
         └──── 5. 再投稿 ←┘
                 (1 日後)
```

**毎日このループを 1 周させる。**

---

## ループの 5 ステップ詳細

### Step 1: 投稿

既存の `orchestrator.py` で日次実行。

### Step 2: 計測 (翌朝 09:00 cron)

```python
# scripts/daily-analytics.py
# 前日公開した動画の成績を取得
yesterday_videos = analytics.get_videos(since=yesterday)
for v in yesterday_videos:
    record = {
        "videoId": v.id,
        "views_24h": v.viewCount,
        "ctr": v.impressionClickThroughRate,
        "avg_view_duration_sec": v.averageViewDuration,
        "audience_retention_graph": v.retentionGraph,  # 各 10 秒ごとの維持率
    }
    save_to_analytics_json(record)
```

### Step 3: 分析 (週次、毎週日曜 23:00)

```python
# scripts/weekly-review.py
videos = get_last_week_videos()
prompt = f"""
以下は先週投稿した {len(videos)} 本の動画データです。

{json_dump(videos)}

これを分析して、以下を抽出してください:
1. 最も成功した動画 Top 3 の共通点 (タイトル・サムネ・冒頭 30 秒)
2. 最も失敗した動画の共通点
3. 維持率グラフの離脱ポイントのパターン
4. 改善すべき台本プロンプトの具体的変更提案
5. 次週の題材キュー並び替え提案

JSON で出力。
"""
insights = claude_analyze(prompt)
```

### Step 4: 反映 (自動 or 半自動)

#### 自動反映 OK (ヒト承認不要)
- **題材キューの並び替え** (`config/topic-queue.json`)
- **投稿時刻の微調整** (アナリティクスから最適時間抽出)
- **サムネ文言のパターン更新** (勝ちパターンを A/B テスト入れ替え)

#### 要承認 (ヒトに Discord 通知)
- **台本プロンプトの大幅改訂** → Pull Request で提案
- **声キャラの変更** → 比較音源付きで相談
- **新シリーズの立ち上げ** → 題材群を提示

### Step 5: 翌日に反映された新投稿

ループ 1 周完了。

---

## 改善の粒度

### Daily (毎日自動)
- 視聴者層の時間帯変化チェック → 投稿時刻の微調整
- コメント欄の頻出キーワード → 次回の題材ヒント

### Weekly (毎週日曜)
- 全動画の再生数ランキング更新
- 台本パターンの A/B 結果集計
- 題材キューの並び替え (伸びそうな順)
- script-prompt.md の微修正 (新パターン追加)

### Monthly (毎月 1 日)
- 競合チャンネル再分析 (`analyze-competitors.py`)
- ロードマップの進捗レビュー
- AI ツール見直し (新ツール導入・不要ツール解約)
- 月次レポート作成 (Discord 投稿)

### Quarterly (3 ヶ月ごと)
- 大方針レビュー
- シリーズ再編
- 次フェーズへの移行判断

---

## Daily Analytics テーブル (config/analytics.json)

```json
{
  "videos": [
    {
      "videoId": "abc123",
      "topic": "エリザベート・バートリ",
      "publishedAt": "2026-04-30T19:00:00+09:00",
      "metrics": {
        "views": [
          {"at": "2026-05-01T09:00", "value": 1200},
          {"at": "2026-05-02T09:00", "value": 3800},
          {"at": "2026-05-08T09:00", "value": 15000}
        ],
        "retention_graph": [
          {"at_sec": 0, "pct": 100},
          {"at_sec": 30, "pct": 82},
          {"at_sec": 60, "pct": 65},
          {"at_sec": 120, "pct": 52}
        ],
        "ctr_percent": 6.8,
        "avg_view_duration_sec": 340
      }
    }
  ]
}
```

---

## 改善を自動で学習するアルゴリズム

### 「勝ちパターン」の抽出 (毎週)

```python
def extract_win_patterns(videos):
    """過去 100 本から勝ちパターンを抽出"""
    # 再生数上位 20% を取得
    top = sorted(videos, key=lambda v: v["views"])[-20:]
    bottom = sorted(videos, key=lambda v: v["views"])[:20]

    # タイトルの単語頻度差分
    top_words = count_words([v["title"] for v in top])
    bot_words = count_words([v["title"] for v in bottom])
    winning_words = {w: top_words[w] / (bot_words.get(w, 1))
                     for w in top_words if top_words[w] >= 3}

    # サムネの文字色・配置パターン (将来)
    # 冒頭 30 秒の維持率グラフ形状 (将来)

    return winning_words
```

結果を `templates/script-prompt.md` の「勝ちパターン」セクションに自動追記。

### 「離脱パターン」の検出 (毎週)

```python
def find_dropoff_points(videos):
    """維持率グラフから離脱の多いタイミングを検出"""
    avg_retention = average_retention_curve(videos)
    dropoffs = find_sudden_drops(avg_retention, threshold=5.0)
    return dropoffs  # [120s, 180s, 240s, ...]
```

離脱ポイントの内容を調査して、次の台本で避ける。

---

## 人間が介入するべきタイミング

**AI が自律判断できないもの**を Discord で通知:

| ケース | 通知 |
|---|---|
| 連続 7 日 CTR < 2% | 「サムネ戦略レビュー必要」 |
| コメントが荒れた (ネガティブ率 >30%) | 「題材再検討必要」 |
| YouTube ポリシー警告 | 「即対応必要」 |
| 新シリーズ提案 | 「承認依頼」 |
| 月間 KPI 未達 | 「戦略見直し」 |

それ以外は AI が自己判断で継続。

---

## 実装ロードマップ

### Phase A (現行〜Week 2)
- [x] analytics.json スキーマ (済)
- [ ] `scripts/daily-analytics.py` (前日動画の成績取得)
- [ ] `scripts/weekly-review.py` (週次レビュー)

### Phase B (Month 1〜2)
- [ ] Discord webhook 通知
- [ ] Retention graph 自動分析
- [ ] 勝ちパターン抽出・自動反映

### Phase C (Month 3〜)
- [ ] 月次レポート自動生成
- [ ] 新シリーズ提案 AI
- [ ] コメント欄分析 → 次題材ヒント

---

## 本ドキュメントは「システムの魂」

ほかのドキュメントは手順書 / 仕様書だが、**このドキュメントはシステムの行動原則**。

**毎月必ず見直し、改善の仕組みそのものを改善する**。
