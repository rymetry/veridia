---
task_id: T-047
epic: execution-evidence
plan_ref: phase-1-crud-mvp.md#5-epic分解
status: not_started
owner:
blocked_by: [T-024]
---

# T-047: 対象サービスsandbox統合(起動・fixture seed・reset)

## 目的

対象サービスをPhase 0のsandbox基盤(sandbox_env / sandbox_runner)上で起動し、fixture seed・resetができる状態にする(§21 Week 3「fixture設計」+ Week 4「sandbox実行」の環境部分)。W14以降の実行系タスクすべての前提。

## 参照

- 計画: §5(execution-evidence)
- North Star: §5.7(Execution Sandbox)、ADR-0004(sandbox runtime)
- Phase 0: T-018(ephemeral env)、T-019(fixture seed / deterministic clock)、T-020(runner)

## DoD

- [ ] 対象サービス(アプリ+DB等の依存)をsandbox内で起動・破棄できる(コマンドまたはスクリプト1発。ADR-0004の方式で足りない場合は差分をADRに追記してから実装)
- [ ] 対象サービスのfixture(初期データ)をseedでき、同一seedからの再構築で同一初期状態になる(T-019の機構を利用。状態hashまたはdump比較のテストで実証)
- [ ] テスト実行間でresetでき、前の実行の状態が残らない(テストで実証)
- [ ] 対象サービス固有の起動・seed手順が設定/スクリプトとして分離されており、sandbox基盤のcoreに対象固有ロジックが入っていない(計画§1の隔離方針)
- [ ] 手順が対象サービス用README(または `docs/domain/` 配下)に記録されている(redaction適用)

## 検証方法・根拠

<完了時に記入>

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
