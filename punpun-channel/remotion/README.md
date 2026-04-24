# 🎬 Remotion (Phase A: プロトタイプ)

React/TypeScript で動画を作る実験的パイプライン。

## 現状

Phase A プロトタイプ。既存の Pillow パイプラインと**共存**。

### 現在あるもの
- `src/index.ts` — エントリーポイント
- `src/Root.tsx` — コンポジション定義
- `src/PunpunVideo.tsx` — メインコンポジション (Sequence 連結)
- `src/components/Scene.tsx` — 1 シーン
- `src/components/Punpun.tsx` — キャラ (SVG パーツ分割、感情 6 種)
- `src/components/SpeechBubble.tsx` — 吹き出し (手書き風枠)
- `src/components/Background.tsx` — 背景 (章別グラデーション)

### できること
- 既存の `test_data/chinghis_khan_v4.json` をそのまま読み込み
- 各シーンを Remotion Sequence で時系列再生
- spring アニメでポップイン
- キャラ 6 表情 + まばたき + 口パク

### まだできないこと (Phase B)
- 背景画像の表示 (assets/cache の PNG を Remotion に渡す仕組みが必要)
- 音声同期
- BGM ミックス
- ポータブルエクスポート

## 使い方

### Windows で試す

```powershell
cd punpun-channel
npm install
npm run remotion:studio
```

ブラウザが開いて、**対話的に動画プレビュー**できる。
変更すればリアルタイム反映。

### 動画として書き出し

```powershell
npm run remotion:render
```

`out/video.mp4` が出来る。

## Phase B への発展

1. **背景画像の統合**: `assets/cache/*.png` を Remotion の staticFile で読み込み
2. **音声同期**: 各シーンの WAV を `<Audio>` タグで差し込み
3. **BGM**: Remotion の audio mixing で章ごとに BGM 切替
4. **Python からの呼び出し**: `npx remotion render` を subprocess で呼ぶ

## 既存 Pillow パイプラインとの比較

| 項目 | Pillow (現行) | Remotion (Phase A) |
|---|---|---|
| コード量 | 1,500 行 | 300 行 (既にもう少ない) |
| 描画品質 | ピクセル寄り | ベクター (SVG) でスケーラブル |
| アニメ豊かさ | カスタム | spring/interpolate 標準装備 |
| 修正のしやすさ | Python コード | React コンポーネント (ホットリロード) |
| レンダリング速度 | 5〜15 分 | 10〜30 分 (Chrome ヘッドレス) |

## 判断

Phase A で見た目を確認 → 気に入れば Phase B で完全移行。
気に入らなければ Pillow 続行。
