# テスト台本集

このフォルダには手動で書いた短いテスト台本が入っている。
本番用 (20 分) は claude CLI が自動生成するが、パイプライン検証用に短めのものを置いている。

## ファイル

| ファイル | 題材 | 用途 |
|---|---|---|
| `elizabeth_bathory_short.json` | エリザベート・バートリ | E2E 動作確認 (1 分強) |
| `caligula_short.json` | カリグラ帝 | サムネ・タイトル変化テスト |
| `wu_zetian_short.json` | 則天武后 | 中国史テスト |

## 使い方

```bash
python3 src/orchestrator.py --script test_data/elizabeth_bathory_short.json --test --no-voicevox
```

## 本番台本生成

```bash
# 1 本だけ生成
python3 src/generator/script_generator.py "ナポレオン" --out output/script.json

# パイプライン全体
python3 src/orchestrator.py --topic "ナポレオン" --test
```
