# ADR-0003: Evidence Store / Trace Storeのローカル構成

- status: accepted
- date: 2026-07-03

## Context

Phase 0 WS-B(`evidence-trace-store`)の着手前に、OQ-3(Evidence Storeの具体構成: metadata DB / object storage)と、North Star §15.1のTrace Store / Evidence Store分離をどう実装するかを決める必要がある。

North Star §22の推奨は、Artifact DB = PostgreSQL、Object Store = S3 / GCS / Azure Blob、Trace = OpenTelemetry互換 + 独自redactionである。一方、Phase 0は個人開発のローカル環境であり、T-013(Evidence Store最小版)とT-014(Trace Store最小版)のDoDを満たすことが目的である。判断軸は次の通り:

- セットアップ最短: `uv sync --group dev` 後、追加サービスなしで統合テストを実行できる
- オフライン動作: PostgreSQL / MinIO / cloud credential / Docker daemonに依存しない
- テスト容易性: pytestの一時ディレクトリでstore全体を作成・破棄できる
- 将来移行性: Phase 1以降に§22推奨(PostgreSQL + S3系 + OpenTelemetry互換)へ寄せられる境界を残す
- §15.4の保存禁止対象(raw secret/token、不要なPII、raw production data、private chain-of-thought等)をPhase 0でも混入させない

この決定に直接依存する後続タスク:

- T-013: ExecutionEvidence(test実行結果 + state diff)を保存し、artifact_id / trace_idで読み出す
- T-014: tool call / error のtrace recordをrun_id / trace_id付きで保存し、時系列照会する
- T-020: sandbox runnerがExecutionEvidenceをEvidence Storeへ保存し、同一test 2回実行の決定性を検証する

## Options

| 候補 | 内容 | 長所 | 短所 |
|---|---|---|---|
| A. PostgreSQL + MinIO(S3互換) | §22に近いローカルサービス構成 | Phase 1以降の本命に近い。SQL / object storeの運用差分が小さい | Docker / daemon / port / credential / SDKが必要。Phase 0の個人開発・CIで重い。T-013/T-014の最小DoDに対して過剰 |
| B. SQLite + local filesystem blob store | metadataはSQLite、payload/blobはローカルディレクトリ。logical URIを保存し、絶対pathは保存しない | Python標準ライブラリだけで実装でき、オフライン・一時ディレクトリテストが容易。SQL境界とobject store境界を残せる | PostgreSQL / S3固有の権限・retention・暗号化・並行性は検証できない。Phase 1以降にadapter差し替えが必要 |
| C. JSONL + local filesのみ | metadataもJSONL、payloadもファイル | 最も単純で依存なし | artifact_id / trace_id / run_id検索、時系列照会、将来PostgreSQL移行の境界が弱い。T-014の照会要件が実装都合に寄りすぎる |

## Decision

Phase 0では **SQLite + local filesystem blob store** を採用する。ADR承認後のT-013/T-014実装は、追加依存なし(Python標準ライブラリの `sqlite3` / `pathlib` / `hashlib` / `json` 等)で進める。

オーナー承認時の条件として、T-013 / T-014の実装はPhase 1以降のPostgreSQL + S3互換storageへの移行コストを最小化するため、次の制約を守る。

- **metadata DBのSQLはPostgreSQL互換の範囲に限定する。** SQLiteをPhase 0の実体として使うが、SQLite固有機能・SQLite方言には依存しない。DDL / DMLは標準SQLまたはPostgreSQL互換の構文に寄せ、`AUTOINCREMENT`、SQLite固有のtype affinity、SQLite固有関数、SQLite固有のconflict構文などに実装を結合しない。
- **blobのlogical refはS3風URIとして扱う。** `object-storage://<store>/<run_id>/<object_name>` 形式を維持し、`<store>` をbucket相当、`<run_id>/<object_name>` をkey相当として1:1で写像できる構造にする。保存metadataにはlocal absolute pathを持たせない。
- **blob store adapterのinterfaceはS3セマンティクスで定義する。** Phase 0のlocal filesystem adapterも `put` / `get` / `list` を基本操作とし、Phase 1でS3 / MinIO adapterへ差し替えるときに利用側interfaceを変えない。
- **移行時の差し替え対象をadapterに局所化する。** PostgreSQL / S3互換storageへ移る際、T-013 / T-014の利用側API・logical ref・保存対象の振り分けは維持し、差し替える主対象はmetadata repository adapterとblob store adapterのみとする。

### 1. Evidence Storeのローカル構成

- metadata DB: SQLite file
  - default path: `.veridia/store/evidence/evidence.sqlite3`
  - pytestでは一時ディレクトリ配下に作成する
- object storage: local filesystem blob store
  - default root: `.veridia/store/evidence/objects/`
  - DBには絶対pathではなく、`object-storage://evidence/<run_id>/<object_name>` 形式のlogical refを保存する
  - local adapterがlogical refをfilesystem pathへ解決する
- Evidence metadataは、少なくとも `artifact_id` / `trace_id` / `run_id` / `test_asset_id` / `verdict` / `created_at` / `schema_version` / `payload_ref` / `state_diff_ref` / `log_refs` を検索・読み出し可能にする
- 保存前にT-008 validatorでExecutionEvidenceのJSON Schema検証を実行する

この構成でT-013のDoDは実装可能である。test実行結果とstate diffはblob storeへ保存し、ExecutionEvidence metadataとlogical refsをSQLiteへ保存する。読み出しAPIはartifact_id / trace_idからmetadataを引き、必要なblobをlogical ref経由で読む。

### 2. Trace Storeのローカル構成

- metadata DB: SQLite file
  - default path: `.veridia/store/trace/trace.sqlite3`
  - Evidence Storeとは別DB fileにする
- Phase 0で保存するsubsetは、§15.2のうち `tool call` / `error` / `run metrics` に限定する
- trace recordは、少なくとも `run_id` / `trace_id` / `span_id` / `parent_span_id` / `sequence` / `event_type` / `name` / `status` / `started_at` / `ended_at` / `latency_ms` / `redacted_args` / `result_summary` / `error_summary` を持つ
- `trace_id` / `span_id` / `parent_span_id` はOpenTelemetryに寄せた命名と親子関係を採用する。ただしPhase 0ではOpenTelemetry SDKやcollectorは導入しない

この構成でT-014のDoDは実装可能である。run_idまたはtrace_idでrecordを抽出し、`sequence` / `started_at` により時系列照会する。T-016のTool Gateway audit logはこのTrace Storeへtool call recordを追加できる。

### 3. Trace StoreとEvidence Storeの分離方針

Phase 0では **物理分離に近いローカル分離** とする。Evidence StoreとTrace Storeは、同じroot配下に置いてよいが、DB file・blob directory・保存APIを分ける。

```text
.veridia/store/
  evidence/
    evidence.sqlite3
    objects/
  trace/
    trace.sqlite3
```

2つのstoreは `run_id` / `trace_id` で相互参照できるが、Evidence Storeにtrace payload全体を複製しない。Evidence Store側に保存するtool call情報は、ExecutionEvidence schemaの範囲で品質判定に必要なsummaryまたはTrace Storeへのrefに留める。Trace Store側もEvidence blobを保持せず、必要な場合はartifact_idやpayload refへの参照だけを持つ。

保存対象の振り分け:

| Store | Phase 0で保存するもの | Phase 0で保存しないもの |
|---|---|---|
| Evidence Store | ExecutionEvidence、test result、state before/after/diff、test runner log、reproduction bundleのref | agent実行過程の全transcript、raw tool args、private chain-of-thought |
| Trace Store | tool call、error、run metricsのredacted record | test payload/blob、state snapshot/diff、Evidence artifact本体 |

### 4. Redaction / 保存禁止対象の扱い

Phase 0では、§15.4を次の最小ルールで担保する:

- store境界で受け付けるのは、redaction済みpayload、summary、logical refのみとする
- Trace Storeはraw args / raw resultを保存せず、`redacted_args` と `result_summary` / `error_summary` を保存する
- Evidence Storeのblobは、synthetic fixture、test result、state diff、logのredaction済み出力に限定する
- raw secret/token、不要なPII、raw production data、private chain-of-thoughtは保存禁止とし、T-013 / T-014のREADMEに明記する
- Phase 0の機械的redactionは最小限でよい。Tool Gatewayのargs redaction(T-016)が入るまでは、保存API利用側がredaction済みデータだけを渡す前提をREADMEとテストfixtureで明示する

## Consequences

### 良い影響

- Phase 0の個人開発・CIで追加サービスを起動せず、T-013 / T-014 / T-020の統合テストを一時ディレクトリだけで実行できる
- PostgreSQL / S3系へ移行する前提の境界(metadata repository / blob store adapter / logical ref)を残せる
- Trace StoreとEvidence StoreのDB fileを分けるため、§15.1の分離がファイル構造とAPI境界に現れる
- Python標準ライブラリだけで実装できるため、ADR承認直後に依存追加を待たずT-013 / T-014へ進める

### トレードオフ

- SQLiteは単一writer制約があり、複数runnerの高並行書き込みやチーム共有環境の検証には向かない
- filesystem blob storeはS3系のIAM、bucket policy、retention、server-side encryption、lifecycle ruleを検証できない
- OpenTelemetry互換のfield命名とspan親子関係は採用するが、Phase 0ではcollector/exporter連携を検証しない
- redactionはPhase 0最小であり、汎用PII検出や本番データ混入防止はPhase 1以降の課題として残る

### North Star §22との差分

このADRは§22の推奨を否定せず、Phase 0ローカル開発向けに軽量adapterを採用する。

| 領域 | §22推奨 | Phase 0決定 | 差分理由 |
|---|---|---|---|
| Artifact / metadata DB | PostgreSQL | SQLite | 追加サービスなし、オフライン、pytest一時DBで検証しやすい |
| Object Store | S3 / GCS / Azure Blob | local filesystem blob store | credential / network / SDKなしでstate diff等を保存できる |
| Trace | OpenTelemetry互換 + 独自redaction | OpenTelemetryに寄せたID/field + SQLite trace DB + redacted payload | collector導入前にT-014の最小照会要件を満たす |

### Phase 1以降の移行条件

以下のいずれかが成立したら、本ADRをsupersedeしてPostgreSQL + S3互換object storage + OpenTelemetry exporter/collector構成へ寄せる:

- 複数runner / 複数agentが同時にstoreへ書き込む
- CI外部やチーム間でevidenceを共有・長期保持する
- retention、暗号化、access control、監査ログをstore層で強制する必要が出る
- Evidence blobが大きくなり、local filesystem管理では容量・cleanup・参照共有が運用リスクになる
- Traceを外部APM / observability基盤へ送る必要が出る

移行時も、T-013 / T-014の利用側APIは維持し、差し替えるのはmetadata repository adapterとblob store adapterを主対象にする。

採択時に追加したDecision上の制約により、Phase 0実装の時点からPostgreSQL互換SQL、S3風logical URI、S3セマンティクスのblob adapter interfaceを守る。これにより、Phase 1以降の移行はmetadata repository adapterとblob store adapterの差し替えに局所化する。

### 依存パッケージ

Phase 0のT-013 / T-014実装に追加依存は不要。PostgreSQL / S3互換 / OpenTelemetry exporterへ移行するADRを採択する場合のみ、監督者が `uv add` を代行して依存を追加する。
