# ADR-0007: テストプロセス成果物の契約は sqk-core を正本として直接消費する

- status: accepted
- date: 2026-08-02

## Context(何を決める必要があったか)

North Star §6 は27種のartifact契約(§6.2〜6.27)をveridia側で定義する前提で書かれている。一方、実装状況と突き合わせると次の乖離があった。

- §6 の27契約に**テスト設計系の成果物が1つも含まれていない**。§4.3 のworkflowは W9 → `TestArchitectureSpec`、W12 → `TestDesignSpec` / `TestAsset` を出力すると定め、§7.3 のskill表も同じ出力を宣言しているが、§6 に対応する契約定義が存在しない
- そのため [phase-1計画 §4](../plan/phase-1-crud-mvp.md) は W9 を「独立ステップとしては実装しない」とし、`TestArchitectureSpec` / `TestDesignSpec` のschema化をPhase 2以降へ送っていた
- sqk-core は同じ工程を ISO/IEC/IEEE 29119-2 / JSTQB v4.0 に接地した11工程モデルとして正典化済みで、`test-architecture-element` / `condition-assignment-matrix` / `test-case` / `coverage-item` / `detailed-test-condition` / `high-level-test-condition` を含む18のJSON Schemaと、valid/invalid fixture 36件を持っている
- sqk-core の `docs/test-techniques/test-process-research-summary-test-design.md` は「TAD を入れないと、agent が分析結果から突然テストケースを生成する動きになりやすい」と明示している。phase-1計画のW9省略はこのアンチパターンに該当する

すなわち、veridiaが未定義のまま停滞していた契約群を、sqk-coreが標準接地した形で既に保有していた。

## Decision(何を決めたか)

**テストプロセス成果物(sqk-core 11工程モデルの工程0〜8)の契約は sqk-core を正本とし、veridia は複製・再定義せずに直接消費する。**

1. veridia が自前で定義する契約は、sqk-core が扱わない**実行系固有のもの**に限る。具体的には `ExecutionEvidence` / `GateDecision` / `GatePolicy`、および envelope に監査項目を付す薄いラッパー(`RunRecord`、未実装)
2. sqk-core 成果物の受け口は `handoff-envelope`。envelope 構造を検証したうえで、内包する各artifactを `artifacts[].schema_ref` が指す sqk-core schema に対して検証する([artifact_validator/sqk_validator.py](../../artifact_validator/sqk_validator.py))
3. sqk-core schema は `artifact_type` を持たず `additionalProperties: false` であるため、veridia の `ArtifactBase` を継承させることも、後からfieldを追加することもできない。**2つのschema familyを別ルーティングで扱う**(veridia系=`artifact_type`、sqk-core系=`schema_ref`)
4. mapping表・adapter層は作らない。envelope をそのまま保存し、veridia固有の監査項目は**外側に付す**(field mappingではなくwrapping)

これは **North Star §6 からの意図的な逸脱**である。§6 の27契約のうち、テストプロセス成果物に相当するものはveridiaでは定義しない。

### 却下した代替案

| 代替案 | 却下理由 |
|---|---|
| North Star §6 に `TestArchitectureSpec` 等を追加定義する | 標準(29119/JSTQB)接地済みの契約をveridia側で再発明することになる。sqk-core と語彙が二重化し、OQ-KB-5(generic contract と adapter の境界)が恒久的な課題として残る |
| sqk-core schema を veridia の `schemas/` へコピーし `ArtifactBase` を継承させる | ADR-0006 の「正典を複製しない」原則に反する。更新のたびに乖離する |
| sqk-core 側に `artifact_type` と `ArtifactBase` 相当を足してもらう | sqk-core は veridia を含む4プラットフォーム(claude-code / gpts / codex / veridia)に供給する設計であり、1 consumer の runtime 都合を正典の契約へ持ち込むことになる。sqk-core `schemas/README.md` も「veridia 固有の GatePolicy / OracleSpec / Evidence / ExecutionEvidence をこのディレクトリに混ぜない」と定めている |

## Consequences(トレードオフ、影響)

- **利点(契約数)**: veridiaが定義する契約は27 → 4 になる。工程4(TAD)/5(TDD)/6(TI)の契約設計作業そのものが消滅する
- **利点(テストデータ)**: sqk-core の valid/invalid fixture 36件がveridiaの回帰テストとしてそのまま機能する。veridia側でテストデータを作らない
- **利点(規律)**: sqk-core schema は `additionalProperties: false` のため、veridia側で契約を勝手に膨らませられない。§6 が27契約へ膨張したのは veridia 側で自由に定義できたためであり、この制約はその再発を構造的に防ぐ
- **コスト(ビルド時依存)**: veridiaのテストが `vendor/sqk-core` の schema と fixture に依存する。ADR-0006 時点の「veridiaのテスト・CIはsubmoduleに依存しない」という前提は**本ADRで解消される**。CIでsubmoduleのcheckoutが必要になる
- **コスト(SHA更新)**: sqk-core の SHA を進めると検証挙動が変わりうる。[sqk-core-integration.md §4](../plan/sqk-core-integration.md) の手順に、veridiaテスト全体の再実行を含める必要がある
- **コスト(上流修正の往復)**: sqk-core側の不整合を見つけても veridia 内では直せない。Issue/PR を経由し、SHA更新で取り込む(2リポジトリ・2PR)。実際に本ADR採択時点で1件発生している(learning-log 2026-08-02)
- **North Star への影響**: §6 の扱いを「veridiaが定義する契約の一覧」から「必要な契約の一覧(正本は契約ごとに異なる)」へ改める必要がある。ただし**変更ルール1に従い、本ADRでは North Star 本文を改訂しない**。Phase 1 の実運用を経てから改訂を判断する(`northstar-proposal` として learning-log に起票済み)
- **OQ-KB-5 の解決**: 「generic platform contract と profile-specific adapter の境界」は、本ADRにより「契約 vs 契約の扱い」の線として確定する。adapter層は作らない
