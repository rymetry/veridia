# ADR-0002: 実装言語・schema lib・schema正本方針

- status: accepted
- date: 2026-07-02

## Context

Phase 0(`docs/plan/phase-0-foundation.md`)のWS-A(`artifact-schema`)着手にあたり、OQ-1(実装言語・スタック、`docs/plan/00-overview.md`)を確定する必要がある。計画§6により、これがPhase 0の最初のタスク(T-001)であり、未決のままWS-Aを始めると後続タスク群が手戻りする。

このADRで確定するのは次の3点:

1. **実装言語**(計画§5の候補: Python / TypeScript)
2. **schema lib**(North Star §22の候補: Pydantic / Zod)
3. **`schemas/` のJSON Schemaファイルとコード内schema定義の併用方針** — どちらを正本とし、生成方向をどうするか、乖離をどう防ぐか

この決定に直接依存する後続タスク: T-002(dev scaffolding)、T-003〜T-007(ArtifactBase + 各spec schema)、T-008(validator)、T-009 / T-010(TestAssetIndex / ChangeImpact generator)。schema定義・validator・generator群がこの上に積まれるため、切替コストは高い(supersede可能だが安価ではない)。

前提となる制約:

- North Star §6.1: 共通contractを `ArtifactBase` として JSON Schema / Pydantic / Zod 等で定義し、各artifact schemaは `allOf` やcompositionで継承する。将来全27 artifactがschema化される(Phase 0では8個)。
- リポジトリ構成マップ・`schemas/README.md` は既に `schemas/artifact-base.schema.json` を「共通契約を定義し各schemaが `allOf` で継承するファイル」と規定済み。すなわち **`schemas/` のJSON Schemaファイルを成果物とすること自体は既定路線**であり、本ADRの争点は「JSON Schemaに加えてコード内schema libを何にするか / どちらを正本とするか」に絞られる。
- 個人開発(1人)であり、学習コスト・保守負荷・エコシステムの一体性が判断軸になる。
- Phase 0の実装対象(計画§3): TestAssetIndex generator(対象repoのAST解析)、ChangeImpactSpec generator(git diff解析)、Evidence Store、Tool Gateway、sandbox runner。Phase 1以降でLLM呼び出し・eval harness・Playwright実行が入る。

## Decision

### 1. 実装言語: Python(3.12+)

QAプラットフォームの実装言語をPythonとする。

### 2. schema lib: Pydantic v2

コード内のartifact表現・バリデーションにPydantic v2を採用する。加えて、`schemas/*.schema.json` に対する生JSONの検証には `jsonschema`(Python標準的なJSON Schema validator)を併用する(理由は下記「正本方針」参照)。

### 3. schema正本方針: JSON Schemaファイルを正本、Pydanticはコード側の型付き表現(単方向生成 + CI検証)

- **正本(source of truth)は `schemas/*.schema.json`(JSON Schema, draft 2020-12)。** これはNorth Star §6.1・`schemas/README.md`・リポジトリ構成マップの既定と整合する。artifact契約は言語非依存の資産であり、将来runtimeや言語が変わっても contract が生き残る形にする。
- **生成方向は「JSON Schema → Pydanticモデル(コード生成)」を基本とする。** `datamodel-code-generator`(`--input-file-type jsonschema`)で `schemas/` からPydanticモデルを生成する。手書きのPydanticモデルを正本にしてJSON Schemaをexportする逆方向は取らない(理由: §6.1が全27 artifactの `allOf` 継承を前提としており、契約の一覧性・言語非依存性を保つには宣言的なJSON Schemaを人間可読の正本に据えるのが乖離に強い)。
- **生JSON artifactの検証は `jsonschema` で `schemas/*.schema.json` に対して行う(T-008 validatorの中核)。** Pydanticは「コード内でartifactを型安全に構築・受け渡しする」ための表現であって、release gateの契約判定の正本ではない。§6.1の「`source_refs` が空のartifactはgateに使えない」の実証(T-008 DoD)は、JSON Schemaの `required`(キー存在)+ `minItems: 1`(空配列のreject)+ validatorで担保する(`required` はキーの存在のみを検証し、空配列 `[]` はvalidとして通過するため、`minItems: 1` が必須)。
- **乖離防止(CI):** 次の2点をCIで検証する。(a) 各 `schemas/*.schema.json` がJSON Schema meta-schema(draft 2020-12)に対してvalid(T-003 DoD)。(b) `schemas/` から生成したPydanticモデルがコミット済みの生成物と一致する(生成物をコミットし、CIで再生成→diff無しを確認する。生成をビルド時のみにして生成物を追跡しない方式は、個人開発では追跡する方が差分レビューしやすいため採らない)。生成物には「generated — do not edit by hand」の注記を付す。

### 採用しなかった候補と却下理由

| 論点 | 採用 | 却下した代替 | 却下理由 |
|---|---|---|---|
| 言語 | Python | TypeScript | 下記「言語比較」参照。Phase 0の中核(AST解析・coverage・property-based・eval harness)でPythonエコシステムが厚い |
| schema lib | Pydantic v2 | Zod v4 | JSON-Schema-as-source workflowの成熟度・双方向ツールの安定性でPydanticが優位(下記) |
| 正本 | JSON Schemaファイル | コード内schemaを正本にしexport | 契約の言語非依存性・一覧性・runtime変更耐性。§6.1の宣言的 `allOf` 継承と整合 |
| 二重管理 | 単方向生成 + CI diff検証 | JSON Schemaとコードを手書き二重管理 | 二重管理は改訂のたびに乖離する(AGENTS.md変更ルール2の複製回避原則と同じ理由) |

#### 言語比較(Python vs TypeScript)

| 観点 | Python | TypeScript |
|---|---|---|
| §22 API test | pytest(厚い) | Playwright API(可) |
| §22 property-based | Hypothesis(成熟) | fast-check(可) |
| §22 UI test(Phase 1+) | Playwright(python binding) | Playwright(first-class) |
| Test Asset Index: 対象repoのAST解析 | 標準 `ast` + tree-sitter | ts-morph等(TS/JSに限定的) |
| coverage mapper(§22) | coverage.py | Istanbul/nyc |
| eval harness / LLM adapter(Phase 3) | エコシステム厚い | 可 |
| schema双方向ツール | datamodel-code-generator(成熟) | zod fromJSONSchemaは新しめ |

TypeScriptはUI test(Playwright)がfirst-classである点が強みだが、Phase 0の中核はUIではなくschema・AST解析・generatorであり、そこはPythonが優位。UI testはPhase 1以降にsubprocess経由でPlaywright(任意言語)を呼べば足り、プラットフォーム本体の言語をTSにする決め手にはならない。

#### schema lib比較(Pydantic v2 vs Zod v4)

| 観点 | Pydantic v2 | Zod v4 |
|---|---|---|
| JSON Schema出力 | `model_json_schema()`、draft 2020-12準拠 | `z.toJSONSchema()`、既定target draft 2020-12 |
| JSON Schema → コード生成 | `datamodel-code-generator`(独立の成熟CLI、jsonschema入力対応) | `z.fromJSONSchema()`(v4で追加、比較的新しい) |
| `allOf`/継承の表現 | sub-modelは `$defs` + `$ref`、override時に `allOf` | 可(表現差あり) |
| 表現不能型の扱い | 少ない | `z.toJSONSchema(z.bigint())` は既定でthrow等、input/output型(`io`)の曖昧さあり |
| 言語親和性 | 本ADRの言語(Python)にネイティブ | TS前提 |

Pydanticを選ぶ決め手: (1) 本ADRで言語をPythonに決めたため親和性で自明、(2) JSON-Schema-as-source(datamodel-code-generator)の成熟度、(3) draft 2020-12準拠が確認できている。

## Consequences

### トレードオフ

- **UI test(Playwright)はTSがfirst-class。** Phase 1以降でUI testを実装する際、Pythonバインディングまたはsubprocessでの外部プロセス起動になる。これは§22でも「UI test = Playwright」とのみ規定され言語は限定していないため許容範囲。
- **schemaとコードの生成パイプライン(datamodel-code-generator + CI diff検証)の初期セットアップコストがかかる。** T-002(dev scaffolding)でこの生成コマンドとCIチェックを整備する必要がある。手書き二重管理より初期コストは高いが、乖離の静かな事故を構造で防げる。
- **`jsonschema` と Pydantic の二層になる。** 「契約判定はJSON Schema、コード内表現はPydantic」という役割分担を常に意識する必要がある。誤ってPydanticのvalidationをgateの正本にすると、生成漏れ時にJSON Schemaとの乖離を見逃す。T-008のvalidatorは必ず `schemas/*.schema.json` を参照する実装にする。

### 後続タスクへの影響

- **T-002(dev scaffolding):** build=Poetry or uv、test=pytest、lint=ruff を想定(具体はT-002で確定)。datamodel-code-generatorの生成コマンドとCI diff検証をここで整備する。AGENTS.md「実装規約」節を埋める。
- **T-003〜T-007(schema定義):** `schemas/*.schema.json` を手書きの正本として定義する(§6.1の宣言的 `allOf` 継承)。Pydanticモデルは生成物。
- **T-008(validator):** `jsonschema` で `schemas/` に対して生JSONを検証する。`source_refs` 空のreject(計画§2完了条件)はJSON Schemaの `required` + `minItems: 1` で担保。
- **T-009 / T-010(generator):** 対象repoのAST解析はPython標準 `ast`(veridia自身がPythonになるため §6のダミー対象とも自然に合致)+ 必要に応じtree-sitter。git diff解析も同エコシステム。

### agent runtime選択肢への影響(ADR-0001追記との関係)

agent runtimeの選定は本ADRのスコープ外(将来別ADR、ADR-0001追記)。言語をPythonにしてもruntime選択肢は不当に狭まらない:

- OpenAI Agents SDK相当 / 自社orchestrator: Python実装が一般的で親和的。
- Claude Agent SDK: Python SDKが提供されており利用可能。
- Codex等を含める場合: skill package正本 `qa-skills/` はSKILL.md規約(言語非依存)であり、`.codex/skills/` へのsymlink方針(ADR-0001追記)は言語選択と独立。

契約(`schemas/*.schema.json`)を言語非依存のJSON Schemaに置いたこと自体が、runtime・言語の将来変更に対する保険になっている。

### North Starからの逸脱

**逸脱なし。** §22は「Schema = JSON Schema / Pydantic / Zod」「言語 = vendor-neutral Python/TypeScript」と複数候補を並記しており、本決定(Python + Pydantic + JSON Schema正本)はいずれも§22の推奨範囲内。§6.1の「JSON Schema / Pydantic / Zod等で `ArtifactBase` を定義し `allOf`/compositionで継承」も充足する。

### 将来の再検討条件(supersede条件)

以下のいずれかが成立した場合、本ADRをsupersedeして再検討する:

- プラットフォーム本体でUI test(Playwright)の比重が大きくなり、TS一本化のメリットがPythonエコシステムのメリットをUI以外でも上回ると判断できる実運用データが出た場合。
- agent runtime選定ADRで、選んだruntimeがTS/JS前提で、Python本体との接続コストが恒常的に問題になった場合。
- datamodel-code-generatorによる `allOf` 継承の生成が §6.1 の要求(全27 artifactの継承)に対して破綻し、手書き二重管理や別方式が避けられなくなった場合(この場合は正本方針=Decision 3のみのsupersedeで足りる可能性がある)。

## 追記(2026-07-02): 承認時に確定した判断根拠

オーナー承認(2026-07-02)の過程で、起案時に不明だった2点が確定した:

- **対象プロダクトの想定スタック**: フロントエンド TS/JS + バックエンド Python/Go。
- **言語習熟度**: オーナーはバックエンドをPython/Goで書く想定であり、Python採用は習熟度面の障害にならない。

§10のQA設計(状態・API中心)により、QA価値は対象のバックエンド層(Python/Go)に集中する。TestAssetIndexのAST解析はPython部分を標準 `ast` でネイティブに解析でき、Go部分はどちらの候補言語でも外部言語となり中立。TSがネイティブ解析できるのはUI層のみで、設計上比重が小さい。以上により本決定(Python + Pydantic)が支持された。上記「将来の再検討条件」(UI test比重のスコープ変更、agent runtime選定等)は引き続き有効。
