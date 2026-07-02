---
task_id: T-022
epic: skill-registry-gatepolicy
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-021]
---

# T-022: skill registry metadata定義

## 目的

skillの運用metadata(§28.2「残すもの」)を保持するregistry形式を定義する。独立Agent Registryは作らない(§28.2の判断)ため、リポジトリ内のindexファイルとして最小実装する。

## 参照

- 計画: §3 WS-E
- North Star: §28.2「残すもの」(registry metadata項目一覧の正本。ここに複製しない)

## DoD

- [ ] registry index(例: `qa-skills/registry.yaml`)の形式が定義され、§28.2「残すもの」の全項目を保持できる(schemaで検証)
- [ ] template skill(T-021)のentryが登録され、validationをpassする(テストで実証)
- [ ] registry entryとskillディレクトリの整合(存在チェック、version一致)を検証するチェックがある

## 検証方法・根拠

(完了時に記入。想定: registry validationのテスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
