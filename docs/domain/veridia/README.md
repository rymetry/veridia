# domain/veridia/ — Phase 1 対象プロダクトのドメイン知識

Phase 1でW1〜W19を通す対象は **veridia自身**([T-024](../../tasks/phase-1/T-024-target-service-decision.md) で決定、2026-08-02。根拠と選定基準の充足は [phase-1計画 §1](../../plan/phase-1-crud-mvp.md#1-目的と対象))。

対象機能は2件に絞る。記録はjust-in-time([domain/README.md](../README.md))— この2機能で触れた範囲のみを書き、veridia全体の棚卸しはしない。

出典はすべてこのリポジトリのコードとschemaであり、本番データ・PII・secretは含まない。

---

## F-1: RunRecordのライフサイクル

sqk-core skillの1回の実行を、後から監査できる形で残す機能。veridiaの他のあらゆる判断(gate判定、release報告)がこの記録を根拠にするため、ここが壊れるとプラットフォーム全体の主張が成立しない。

### 主要な状態

```text
[存在しない]
   │ build_run_record()   ← envelope検証 + RunRecord契約検証を両方通ったものだけが次へ進む
   ▼
[検証済みpayload(メモリ上)]
   │ RunStore.save()      ← 保存時にもう一度契約検証する
   ▼
[status: draft / requires_human_review: true]   ← producerが出せるのはここまで
   │ (人間レビュー。実装は T-031)
   ▼
[status: reviewed] ─→ [status: approved]
```

- `status` は `draft` / `reviewed` / `approved` の3値。ArtifactBaseの4値から `deprecated` を除いた集合(出典: `schemas/run-record.schema.json`)
- **producerは常に `draft` を出す。** `reviewed` / `approved` への遷移は後続の更新であり、Phase 1時点で遷移させるコードは存在しない(T-031が担当)
- `requires_human_review` はPhase 1では常に `true`(計画§7「候補生成+人間レビュー必須」)

### 観測点

| 種別 | 場所 | 何が見えるか |
|---|---|---|
| ファイル | `.veridia/store/runs/<run_id>.json` | 記録の全内容。1 run = 1ファイル。`sort_keys=True` / `indent=2` で決定的に書かれる |
| API | `RunStore.get(run_id)` / `run_ids()` | 取得と一覧。`get` は保存時と違い契約検証を**しない**(読み戻しは生JSONのまま返る) |
| event | Trace Storeの `run_metrics` record | backend / model / token usage / 参考コスト。prompt本文は入らない(§15.2) |
| 契約 | `artifact_validator.validate_artifact` | `artifact_type: run_record` でルーティングされる |

### 既知の設計上の性質(要求・リスク分析の入力)

- `source_refs` は `minItems: 1`。`SkillRunner.run()` も入口で空を拒否する。**契約とruntimeの二重で強制されている**
- `RunRecord` はArtifactBaseを継承しない。`confidence` がrunに対して意味を持たないため([ADR-0007](../../decisions/adr-0007-sqk-core-contract-consumption.md))
- `sqk_core.commit` に、そのenvelopeが準拠する契約のcommit SHAが入る。SHA固定が契約の更新手段なので、これが無いと後から記録を解釈できない
- `RunStore.get()` は契約検証をしない。ファイルを直接編集された場合や、古いschema versionで書かれた記録がそのまま返る経路が存在する

---

## F-2: ExecutionEvidenceの保存と検索

sandbox実行の証跡(テスト結果、state diff、ログ、再現バンドル)をmetadataとblobに分けて保存し、`trace_id` / `run_id` / `test_asset_id` で引けるようにする機能。失敗時のevidenceが無いとevidence gateが判定できない(§17.1)。

### 主要な状態

```text
[evidence未収集]
   │ save_execution_evidence()
   │   1. artifact契約検証
   │   2. blob書き込み(test_result → state_diff → [reproduction_bundle] → logs)
   │   3. refを埋めたpayloadを再検証
   │   4. payload本体をblobへ
   │   5. metadataをSQLiteへ
   ▼
[metadata登録済み + blob保存済み]
```

- **2〜4と5の間に中間状態が実在する。** blobは書けたがmetadata登録前に失敗すると、SQLiteから引けないblobが残る。トランザクション境界がblobとSQLiteをまたがないため(出典: `evidence_store/store.py`)
- 契約検証は**2回**行われる。ref埋め込みの前と後。後段が落ちるとblobだけが残る

### 観測点

| 種別 | 場所 | 何が見えるか |
|---|---|---|
| DB | `.veridia/store/evidence/evidence.sqlite3` テーブル `evidence_metadata` | `artifact_id`(PK)/ `trace_id` / `run_id` / `test_asset_id` / `verdict` / `created_at` / `schema_version` と各ref |
| blob | `.veridia/store/evidence/` 配下の `<run_id>/` | `payload` / `test_result` / `state_diff` / `reproduction_bundle` / 各ログ |
| API | `get_by_artifact_id` / `find_by_trace_id` / `find_by_run_id` / `find_by_test_asset_id` | 4経路の検索 |
| 契約 | `artifact_type: execution_evidence` | `schemas/execution-evidence.schema.json` |

### 既知の設計上の性質(要求・リスク分析の入力)

- **redaction検出はPhase 0では呼び出し側の責務**(learning-log 2026-07-03、T-013)。Evidence Store境界では検査していない。§15.4の「secret / PIIの生値を残さない」はP0要求だが、現状それを強制する仕組みは境界に無い
- `run_id` はblobのパス要素になるため、traversalを拒否する検証がある(`_validate_run_id`)
- 決定性の材料は `sandbox_env` のseed / clock固定で供給される

---

## この2機能を選んだ理由

[phase-1計画 §1](../../plan/phase-1-crud-mvp.md#1-目的と対象) の選定基準4項目への適合を参照。要点は、どちらも**状態と観測点が実在し、破れるとプラットフォームの主張が崩れるP0要求を持つ**こと。

F-2をあえて含めたのは、F-1だけだと「今回のセッションで書いたばかりのコードを自分でテストする」構図に寄りすぎるため。F-2はPhase 0の実装で、かつredactionという未解決のP0要求を抱えている。

## 移行時の注意

Phase 1完了後に外部の実在サービスへ横展開する([計画 §1](../../plan/phase-1-crud-mvp.md#1-目的と対象) の移行条件)。そのとき本ファイルの内容は対象固有知識として**破棄ではなく併存**させる。veridia自身も継続してQA対象であるため。
