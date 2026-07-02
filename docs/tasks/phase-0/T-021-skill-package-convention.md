---
task_id: T-021
epic: skill-registry-gatepolicy
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-002]
---

# T-021: skill package規約とtemplate skeleton

## 目的

Phase 1でskill群を実装するための規約を確定する。§7.1のpackage構造に従うtemplateを `qa-skills/` に置き、manifest必須項目(§7.2)を機械検証可能にする。

## 参照

- 計画: §3 WS-E
- North Star: §7.1(Skillの構造)、§7.2(manifest例)
- `qa-skills/README.md`(ADR-0001の名前空間注意を含む)

## DoD

- [ ] `qa-skills/_template/` に§7.1のpackage構造に対応するskeletonが存在する(構成要素の網羅は§7.1のディレクトリ図との突き合わせで確認。各ファイルは構造を示すstubで可)
- [ ] manifestの必須項目セットを§7.2の例から定義してschema化し(§7.2は例示のため、どのkeyを必須とするかはschema側で確定させる)、templateのmanifestがvalidationをpassする(テストで実証)
- [ ] `qa-skills/README.md` にtemplateの使い方(新規skill作成手順)が追記されている

## 検証方法・根拠

(完了時に記入。想定: manifest validationのテスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
