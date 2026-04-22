# 🎬 デモ動画

寝てる間に生成された実物のサンプル。

## ファイル

| ファイル | 内容 |
|---|---|
| `elizabeth_bathory_demo.mp4` | エリザベート・バートリ 9 分 55 秒 (1920x1080) |
| `elizabeth_bathory_thumbnail.png` | 同サムネ (1280x720) |

## 見方

### Windows
```
git pull origin claude/add-video-creation-gZ3Et
cd punpun-channel\demo
start elizabeth_bathory_demo.mp4
```

または、エクスプローラーで `punpun-channel/demo/elizabeth_bathory_demo.mp4` をダブルクリック。

### 注意

- 声は **open-jtalk** (素朴なナレーション)。本番では **VOICEVOX** に置き換わります。
- 背景はサンドボックスから Wikipedia 等にアクセス出来なかったので **単色プレースホルダ** が多め。あなたの Windows PC で再生成すると本物の地図・肖像画が入ります。
- それ以外 (構成、章立て、キャラ位置、吹き出し、サムネ) は本番品質。

## このデモで分かること

✅ パイプライン全体が動いている
✅ 過去動画とほぼ同じ画面構成 (背景 + 吹き出し + ぷんぷん右下)
✅ 9:55 という長尺でも違和感なくシーン切り替わる
✅ サムネがクリックしたくなる作りになっている

## 改善案 (見て気付くポイント)

実際に見た感想を教えてください。次の優先順位を決めます:
- 声が気になるなら → VOICEVOX を最優先
- 背景がつまらないなら → Wikipedia 画像取得を優先 (PC 環境では自動で動く)
- アニメーションが欲しいなら → Remotion 化を Phase 2 で
- ぷんぷんが代替なのが気になるなら → 過去動画から本物のキャラ画像抽出
