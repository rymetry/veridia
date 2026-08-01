# software-quality-knowledge-base 統合方針ドラフト

作成日: 2026-07-07
status: draft

## 1. 目的

本ファイルは、`veridia` と `software-quality-knowledge-base` の統合方針を検討するための叩き台である。

現時点の方針は、`software-quality-knowledge-base` を品質知識の正本とし、`veridia` はそのうち機械可読化・安定化された成果物を読み込んでQA実行・判定・証跡化に使う、という分担にする。

つまり、`veridia` に知識ベース全文を複製するのではなく、次の関係を目指す。

```text
software-quality-knowledge-base
  品質知識・用語・規格・技法・mapping・schema候補の正本
        ↓ versioned export / adapter
veridia
  QAエージェント実行基盤。計画・実行・判定・証跡化で利用する
```

## 2. 現在の入力の扱い

現在作成済みの「ベリサーブ HQW! 記事エッセンス抽出インデックス v3」は、実装仕様ではなく調査要の索引である。

このv3には、オラクル技法、ISO/IEC 25010 taxonomy、概念モデルとschemaの対応、RAG/source grounding評価、SBOM証跡、ドメイン別quality profileなど、`veridia` に役立ちそうな候補が含まれている。

ただし、現時点では以下を前提にする。

- v3は記事由来・Claude版由来の候補を統合した調査索引であり、一次情報確認と正規化が未完了である。
- `veridia` の実装判断に直結させる前に、`software-quality-knowledge-base` 側で知識整理・用語ID・mapping・schema候補を確定する必要がある。
- 詳細な `veridia` 側の実装方針は、追加調査後、かつ `software-quality-knowledge-base` 側の実装が完了してから決める。

## 3. 統合の基本方針

`software-quality-knowledge-base` から `veridia` へ渡すものは、長文の調査メモではなく、安定IDを持つ小さな構造化成果物にする。

候補は次のとおり。

| knowledge-base側の成果物 | veridia側の利用候補 |
|---|---|
| 用語map | artifact / report の表記正規化 |
| ISO/IEC 25010などの品質taxonomy | `GatePolicy` の品質特性・判定軸 |
| テスト技法catalog | `OracleSpec` / `qa-skills` の判定方式 |
| 概念モデルmapping | `StateModel` / `ExecutionEvidence` の構造化 |
| RAG/source grounding評価指針 | source grounding skill / eval harness |
| SBOM・supply chain mapping | `SBOMEvidence` / release gate |
| quality profile template | `quality_profile` によるドメイン別gate |

`veridia` 側では、これらを直接埋め込まず、adapter / loader 経由で読み込む設計を検討する。

## 4. 依存順序

詳細実装は `software-quality-knowledge-base` 側の整備後に行う。

想定順序:

1. `software-quality-knowledge-base` に v3 の正本を置く。
2. v3 をもとに、一次情報確認・用語正規化・mapping候補の精査を行う。
3. `software-quality-knowledge-base` 側で、安定ID・schema・mapping・export形式を決める。
4. `veridia` 側で、どの成果物を読むかをADRまたはPhase計画で決める。
5. 最小のconsumer pathから実装する。
6. `GatePolicy`, `OracleSpec`, `StateModel`, `ExecutionEvidence`, `TraceStore`, `ToolGateway`, `qa-skills`, `quality_profile` へ段階的に接続する。

## 5. 現時点でやらないこと

- v3全文を `veridia` に複製しない。
- v3を根拠に、すぐ `veridia` のruntime挙動を変更しない。
- 記事由来・Claude由来の検証ステータスを、公式確認済みの標準として扱わない。
- 未確定のknowledge-base draftへruntime依存を作らない。
- CRUD/業務アプリ以外の知識をPhase 1の主線へ混ぜ込まない。
- ドメイン固有知識を汎用platform coreへ直書きしない。

## 6. 未決事項

| ID | 未決事項 | 決定タイミング |
|---|---|---|
| OQ-KB-1 | 最初に機械可読化するknowledge-base成果物 | `software-quality-knowledge-base` 側のv3後続調査後 |
| OQ-KB-2 | 連携方式: submodule / package / generated artifact / local file reference | stable export候補が見えた後 |
| OQ-KB-3 | ID・schema変更時の互換性チェック | export形式決定後 |
| OQ-KB-4 | 初回consumer対象の `quality_profile` | Phase 2以降の計画時 |
| OQ-KB-5 | generic platform contract と profile-specific adapter の境界 | 具体タスク化前 |

## 7. 初期提案

当面は、本ファイルを統合方針の叩き台として保持する。

`software-quality-knowledge-base` 側で v3 の後続調査と実装が完了するまでは、`veridia` では具体実装タスクを作らない。

その後、最小の接続として次を検討する。

1. `software-quality-knowledge-base` から品質taxonomy IDを読み込む。
2. `GatePolicy` の品質特性・判定軸へmappingする。
3. テスト技法catalogの1項目を `OracleSpec` に接続する。
4. 生成されるevidenceに、参照したknowledge-baseのversion / commit / artifact IDを保存する。

この順序なら、knowledge-baseの正本性を保ちつつ、`veridia` 側のruntime依存を小さく始められる。
