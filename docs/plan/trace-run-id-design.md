# trace_id / run_id ID設計(T-012)

対応タスク: [T-012](../tasks/phase-0/T-012-trace-run-id-design.md)

## 1. 目的と前提

Phase 0のEvidence Store / Trace Store / Tool Gateway audit logで共通して使うID体系を定義する。対象IDは `run_id`、`trace_id`、`span_id`、`parent_span_id`。

この文書はADR-0003の具体化であり、新規ADRは起票しない。ADR-0003はtrace recordが `run_id` / `trace_id` / `span_id` / `parent_span_id` を持ち、OpenTelemetryに寄せた命名とspan親子関係を採用すると決めている。T-012ではOpenTelemetry SDKやcollectorは導入しない。

ArtifactBaseの `trace_id` は `schemas/artifact-base.schema.json` で `type: string`、`minLength: 1`、descriptionは「生成runのtrace識別子(§15。ID体系の設計はT-012)」。patternは未定義。既存exampleは `trace-20260702-0001` であり、T-012の生成値は同じ `trace-<UTC日付>-<suffix>` prefix構造を維持する。

## 2. ID形式

| ID | 形式 | 例 | 用途 |
|---|---|---|---|
| `run_id` | `run-YYYYMMDDTHHMMSSffffffZ-<12 lowercase hex>` | `run-20260703T123456789012Z-000000000001` | 1回のagent / runner実行単位。Trace Storeのrun集約、Evidence Storeのobject key prefix |
| `trace_id` | `trace-YYYYMMDD-<16 lowercase hex>` | `trace-20260703-00000000000000a2` | 1つのtrace単位。ArtifactBaseに保存し、Evidence Store / Trace Storeを相互参照する |
| `span_id` | `<16 lowercase hex>` | `00000000000000a3` | Trace Store recordのspan識別子。OpenTelemetryのspan ID長(8 bytes hex)に合わせる |
| `parent_span_id` | `null` または `<16 lowercase hex>` | `00000000000000a3` | root spanでは `null`。child spanでは親recordの `span_id` |

実装上の正規表現は `trace_ids` packageの `RUN_ID_RE` / `TRACE_ID_RE` / `SPAN_ID_RE` を正とする。

## 3. 採番

- 生成時刻はUTCに正規化する。clockがtimezone-aware datetimeを返さない場合は `ValueError` とする。
- `run_id` はmicrosecondまで含むUTC timestampをprefixに持つため、文字列ソートでおおむね作成時刻順に並ぶ。
- `trace_id` はArtifactBase exampleとの整合を優先して日付prefixに留め、suffixに64-bit相当のrandom hexを持たせる。
- `span_id` はOpenTelemetryのspan IDと同じ16 hex文字にする。
- 中央採番DBやstore書き込み前の予約はしない。衝突耐性は標準ライブラリ `secrets.token_hex` のentropyに委ねる。
- テストではclockとtoken generatorを注入し、形式・一意性・伝播規則を決定的に検証する。

この設計は、Phase 0で追加依存なしに生成でき、将来OpenTelemetry exporterを導入する場合もTrace Store recordの `span_id` / `parent_span_id` 親子関係を維持できる。一方、`trace_id` はArtifactBaseとの後方互換を優先したrepo内IDであり、OTelの32 hex trace IDそのものではない。将来OTel exporterが必要になった場合は、export adapterでOTel trace IDを別途生成またはmappingする。

## 4. 伝播規則

1. 実行開始時にroot `TraceContext` を作る。
   - `run_id`: 新規生成
   - `trace_id`: 新規生成
   - `span_id`: root spanとして新規生成
   - `parent_span_id`: `null`
2. artifact生成時はArtifactBaseへ `trace_id` だけを付与する。ArtifactBaseは `run_id` / `span_id` を持たないため、artifact本体へ追加しない。
3. Evidence Store(T-013)のmetadataには `artifact_id` / `trace_id` / `run_id` を保存する。artifact本体の `trace_id` とmetadataの `trace_id` は同じ値にする。
4. tool call / error / run metricsをTrace Store(T-014)へ保存するときは、`TraceContext.trace_record_fields()` 由来の `run_id` / `trace_id` / `span_id` / `parent_span_id` を保存する。
5. Tool Gateway audit log(T-016)は、gateway呼び出しごとに現在のspanを親にしたchild contextを作り、tool call recordへchild `span_id` と親 `parent_span_id` を保存する。複数tool callは同一 `run_id` / `trace_id` を共有し、spanで親子関係を表す。

## 5. ArtifactBase schemaとの整合

T-012ではschema変更をしない。ArtifactBaseの `trace_id` はpattern未定義のstringであり、生成する `trace-YYYYMMDD-<16 lowercase hex>` は `minLength: 1` を満たす。既存example `trace-20260702-0001` と同じ `trace-<UTC日付>-<suffix>` 形を維持するが、suffixは衝突耐性のため16 hex文字へ拡張する。

この整合は `tests/test_trace_ids.py::test_generated_trace_id_passes_artifact_base_schema_validation` で検証する。
