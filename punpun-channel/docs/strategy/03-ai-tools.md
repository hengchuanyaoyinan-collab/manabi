# 🤖 推奨 AI ツール一覧 (2026 年 4 月時点)

AI による完全自動 YouTube 運営に使う / 検討中のツールカタログ。

**判断軸**: 価格 / 品質 / 自動化容易性 / ロックイン

---

## 🟢 現状採用中

| 用途 | ツール | コスト | 理由 |
|---|---|---|---|
| 台本生成 | Claude Max (CLI) | Max 契約内 | API キー不要、対話的 |
| 音声合成 | VOICEVOX | 無料 | 商用可・日本語特化・ローカル |
| 字幕同期 | Whisper (ローカル) | 無料 | 高精度、オフライン |
| 画像取得 | Wikipedia Commons + いらすとや | 無料 | ライセンス明確 |
| 地図 | Cartopy + Natural Earth | 無料 | 世界中の地図 |
| 動画エンコード | FFmpeg | 無料 | 業界標準 |
| 投稿 | YouTube Data API v3 | 無料 (quota) | 公式 |
| 競合分析 | youtube-transcript-api | 無料 | 字幕取得 |

## 🟡 導入推奨 (ROI 高)

### 1. ElevenLabs (声クローン) ⭐⭐⭐⭐⭐
- **用途**: 声のクオリティアップ、「ブンブン」声を AI 再現
- **価格**: Starter $5/月、Creator $11/月、Pro $22/月
- **判断**: **登録者 5,000 超えたら即導入**。視聴維持率に直結
- **統合**: API がシンプル、src/voice/ に `elevenlabs_client.py` 追加で完結
- **備考**: 10 秒の声サンプルで学習可能

### 2. OpenAI gpt-image-1 / DALL-E ⭐⭐⭐⭐
- **用途**: シーン固有のイラスト生成 (いらすとや依存脱却)
- **価格**: $0.04〜0.08/枚 (1 動画 100 枚で $4〜8)
- **判断**: フェーズ 2 (収益化後) から本採用
- **統合**: OpenAI API
- **備考**: 1 枚 5〜10 秒で生成、バッチ可

### 3. Stable Diffusion (ローカル or Replicate) ⭐⭐⭐⭐
- **用途**: OpenAI の代替、日本画風・手描き風で尖らせる
- **価格**:
  - ローカル: 初期 GPU 必要 (RTX 4090 で $2000)
  - Replicate: $0.005〜0.02/枚
- **判断**: 予算次第、ROI は OpenAI より若干不確実
- **統合**: Replicate API

### 4. Playwright MCP (ブラウザ操作) ⭐⭐⭐⭐⭐
- **用途**: Claude が YouTube を直接見て競合分析
- **価格**: 無料 (OSS)
- **判断**: **すぐ導入**。分析の精度が跳ね上がる
- **統合**: Claude Code MCP 設定

### 5. Whisper API (OpenAI) ⭐⭐⭐
- **用途**: ローカル Whisper の代替 (速度が速い)
- **価格**: $0.006/分
- **判断**: ローカルで回るなら不要。CPU 弱いなら検討

## 🔴 導入検討中 (将来)

### 6. Veo 3 (Google) / Runway Gen-3 / Pika Labs
- **用途**: 動画クリップを AI 生成 (オープニング、キメシーン用)
- **価格**: $0.25〜0.75/秒
- **判断**: 1 動画 10 秒使うだけでも $7.5、月 300 秒で $225。コスト高
- **用途限定**: 特定シーンだけ (例: 5 分版 vs 20 分版のオープニング 5 秒)
- **統合**: Google AI Studio、Runway API

### 7. Suno / Udio (音楽生成)
- **用途**: オリジナル BGM 生成
- **価格**: $10〜24/月
- **判断**: フリー BGM で十分なのでスキップ。独自ブランディング時のみ

### 8. D-ID / HeyGen (AI アバター動画)
- **用途**: 顔出し型に転向する場合
- **価格**: $29〜300/月
- **判断**: ブンブン路線 (顔出しなし) なら**不要**

### 9. TTS (Minimax Speech / Cartesia)
- **用途**: ElevenLabs 代替、感情表現の質
- **価格**: $10〜30/月
- **判断**: ElevenLabs で足りないときに検討

### 10. AssemblyAI / Deepgram
- **用途**: 高精度字幕・話者分離
- **価格**: $0.37/時間
- **判断**: 競合分析で高精度必要なら導入

## 🛠 運営補助ツール

### 11. TubeBuddy / vidIQ
- **用途**: YouTube SEO・タグ最適化
- **価格**: Free / $7.5〜120/月
- **判断**: ブラウザ拡張として便利、無料プランで十分

### 12. Social Blade
- **用途**: 競合チャンネルの成長速度確認
- **価格**: 無料
- **判断**: **即採用**

### 13. Notion AI
- **用途**: 企画メモ管理
- **価格**: $8〜15/月
- **判断**: 個人運営なら別途不要、GitHub で管理

### 14. Discord / Slack (通知)
- **用途**: 動画生成完了・エラー通知
- **価格**: 無料
- **判断**: **即採用**。webhook で 10 行実装

## 📊 月コスト設計

### シナリオ A: 最小運用 (立上げ〜フェーズ 1)
- Claude Max: 既加入
- VOICEVOX: 無料
- YouTube API: 無料
- **合計: 0 円**

### シナリオ B: 標準運用 (フェーズ 2〜)
- + ElevenLabs Starter $5
- + OpenAI (画像) $10〜20
- **合計: $15〜25/月 (2,000〜3,500 円)**

### シナリオ C: フル装備 (フェーズ 3〜)
- + ElevenLabs Creator $11
- + OpenAI (画像+Whisper) $30
- + Replicate (SD 代替) $10
- + Playwright MCP 無料
- **合計: $51/月 (約 7,500 円)**

### シナリオ D: 実験 (一部 AI 動画)
- シナリオ C + Veo 3 (月 60 秒) $45
- **合計: $96/月 (約 14,000 円)**

## 採用判断ルール

### すぐ導入 (Week 1)
- [ ] Playwright MCP (無料、効果絶大)
- [ ] Social Blade (無料)
- [ ] Discord webhook 通知 (無料)

### 登録者 1 千〜収益化前 (Month 1〜3)
- [ ] ElevenLabs Starter ($5)

### 収益化後 (Month 3+)
- [ ] OpenAI API for images ($20)
- [ ] ElevenLabs Creator ($11)

### 登録者 5 万超え (Month 6+)
- [ ] Veo 3 部分採用
- [ ] Stable Diffusion ローカル (GPU 投資)

## 見直しサイクル

本リストは **月 1 回見直す**。新ツールの動向を monitor:
- https://theresanaiforthat.com (新 AI ツール一覧)
- https://aigptfree.com (AI ニュース)
- X (Twitter) の #AI タグ

月次レビューで ROI 低いツールは即解約。
