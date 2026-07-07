---
task_id: T-045
epic: modeling-generation
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-032, T-035, T-038, T-042]
---

# T-045: APIテスト生成(W12: 不足分のみ・1機能で実行可能)

## 目的

CoverageGapで不足と判定された範囲**のみ**を対象に、review済みOracleSpec・StateModelからAPIテストを生成する(W12)。reuse判断(T-035)でreuse / extendとされた範囲は生成しない。Phase 1完了条件「不足分だけAPIまたはPlaywrightテストを生成できる」の前半をカバーする。

## 参照

- 計画: §5(modeling-generation)、§4(W12は不足分のみ)
- North Star: §7.3(test-design / test-implementation)、§4.3([E] Generation)、§13(生成前に既存資産を確認する思想)

## DoD

- [ ] テスト生成の入力がCoverageGap・TestReuseCandidate・OracleSpec・StateModelであり、gapのない要求に対してテストを生成しないことがテストで実証されている
- [ ] 対象サービスの1機能について、生成されたAPIテストがsandbox(T-047)または対象環境でそのまま実行可能な形式で出力される(§21 Week 3のDoD「1機能で実行可能」)
- [ ] 生成テストがOracleSpecの判定方式を実装しており、期待値がsourceのある根拠に紐づく(assertion根拠のtrace: どの要求・oracleから来たか)
- [ ] 生成テストのmetadata(covered requirement / oracle参照)がTestAssetIndexへ反映される
- [ ] 生成テストはhuman review(T-031のフロー)を通過してから実行対象になる(承認前の生成物を実行系へ流さないことをテストで実証)
- [ ] fake LLMでの構造検証・生成抑制ロジックのpytestがpassする

## 検証方法・根拠

<完了時に記入>

## 備考

生成方式(テンプレート+LLM、全LLM等)は実装時に判断してよいが、生成物の実行可能性検証(構文チェック・dry run)を生成パイプラインに含めること。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
