---
task_id: T-015
epic: tool-gateway
plan_ref: phase-0-foundation.md#3-ワークストリーム分割
status: not_started
owner:
blocked_by: [T-002]
---

# T-015: Tool Gateway最小版(allowlist + schema validation)

## 目的

tool呼び出しをGateway経由に強制する最小実装。§5.6の全機能表ではなく、allowlistとschema validationのみに留める(計画§6のスコープクリープ注意)。

## 参照

- 計画: §3 WS-C、§6(最小実装に留める)
- North Star: §5.6(Tool allowlist / Schema validation)

## DoD

- [ ] tool呼び出しがGateway経由で実行でき、allowlist外のtool呼び出しはrejectされる(テストで実証)
- [ ] tool input / outputがschema検証され、violation時はエラーになる(テストで実証)
- [ ] 最小のtool 1〜2種(例: repo読み取り、test実行)が登録され、正常系が動作する
- [ ] §5.6のうちPhase 0で実装しない機能(AuthN/AuthZ / guardrail / dry-run / approval / rate limit等)がREADMEにスコープ外として明記されている

## 検証方法・根拠

(完了時に記入。想定: テスト実行結果)

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見: <リンク or 「なし」>
