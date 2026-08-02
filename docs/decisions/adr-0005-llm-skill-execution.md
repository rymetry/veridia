# ADR-0005: LLM skill実行方式

- status: accepted
- date: 2026-08-02

## Context

Phase 1(`docs/plan/phase-1-crud-mvp.md`)で初めてLLM駆動のskillを実装する。Phase 0は決定的実装のみでLLM統合が存在しないため、呼び出し方式が未決のままではskill実行基盤([T-027](../tasks/phase-1/T-027-skill-runner-minimal.md))へ進めない。計画§7のOQ-5がこの未決事項である。

ここで言うskillは `qa-skills/` 配下のskill package(§7.1)である。開発エージェント自身の拡張である `.claude/skills/` とは別物(AGENTS.md「注意(名前空間)」/ ADR-0001)。

この決定に直接依存するタスク:

- T-027: skill実行基盤最小版。LLM呼び出し境界・リトライ方針・trace記録内容が本ADRに従う
- T-027を `blocked_by` に持つLLM skill 11本: T-029 / T-030 / T-031 / T-035 / T-036 / T-038 / T-039 / T-041 / T-042 / T-043 / T-050
- T-052: QualityAnalyticsSnapshot生成。LLMコスト記録の保存先を本ADRから引く

### オーナー確認の結果(2026-08-02)

タスク備考の指示に従い、provider契約・課金についてオーナーの確認を取った。

- 利用可能な契約は **Claude と Codex のサブスクリプションの範囲**。従量課金APIの契約は持たない
- **API keyは未設定**
- 既定modelはClaude Opus 5でよいが、**Codex(GPT-5.6 Sol)でも利用できるようにする**。位置づけは「選択可能なbackend」
- run単位のコスト上限は設けない
- prompt記録は「**指示部は全文・データ部は参照**」の形で§15.4と整合させる(Decision 7)
- Codexの分離保証がClaudeより弱い件は、**制限を明記したうえで制約なしに使う**(Decision 5.3 / 5.4、Consequences)

この回答は、タスクDoDが暗黙に前提していた「API直結 + API key + 従量課金」を否定する。DoDの「API key管理(環境変数名。ハードコード禁止、起動時検証)」はサブスクリプション経由では文字どおり成立しないため、**「認証情報の扱い」** として読み替えて満たす(Decision 4)。読み替えは要件を緩めない。runnerが秘密情報に一切触れなくなるため、趣旨としてはむしろ強い。

### 実行環境の実測(2026-08-02)

方式を机上で決めないため、両CLIの非対話実行をリポジトリ外の空ディレクトリをcwdにして実行し検証した。

| 確認項目 | `claude -p`(Claude Code 2.1.207) | `codex exec`(codex-cli 0.145.0) |
|---|---|---|
| API key未設定での実行 | 成功(サブスクリプション認証) | 成功(`--ignore-user-config` でも認証は保持) |
| JSON Schema制約出力 | `--json-schema` → envelopeの `structured_output` | `--output-schema <file>` → 最終メッセージがJSON |
| 消費量の自己申告 | `usage` / `modelUsage` / **`total_cost_usd`** | tokens合計(機械可読にするには `--json`) |
| 実行metadata | `session_id` / `num_turns` / `stop_reason` / `duration_ms` | header に model / provider / approval / sandbox / reasoning effort / session id |
| 終了状態(実測値) | `num_turns: 3` / `stop_reason: "tool_use"` / cache_creation **35,447 tokens** / `total_cost_usd: 0.3736` | tokens used **17,067** |

この実測から、方式決定に効く事実が4つ出た。

1. **CLIはUSD建てコストを自己申告する。** サブスクリプション利用でも `total_cost_usd` が返る。これは実請求額ではなく従量課金換算の参考値だが、コスト記録のために独自の単価表を持つ必要がないことを意味する。CodexはUSDを返さないため、記録側は「取得できない場合がある」前提で設計する。
2. **CLIの既定実行は単発推論ではない。** 「OKと返せ」だけの試行で17K〜35K tokensが積まれた。CLI既定のsystem prompt・tool定義・環境情報・プロジェクト文脈が全て乗るためである。hermetic化は「望ましい」ではなく**必須**である。
3. **toolの完全無効化はできない。** claude側の `stop_reason` が `tool_use` であることが示すとおり、構造化出力自体がtool機構で配送される。制約は「toolを持たせない」ではなく **「外界へ到達するtoolを持たせない」** と定義する必要がある。
4. **CLIは既定でセッションをローカルへ永続化する。** 上記プローブのprompt本文が `~/.claude/projects/<...>/<session-id>.jsonl` と `~/.codex/sessions/<date>/rollout-<...>.jsonl` に平文で残っていることを確認した。**veridiaのstoreに保存しなくても、CLIがpromptを保存する。** 対策として `claude --no-session-persistence` と `codex exec --ephemeral` が存在することも確認した(Decision 5.5)。

### Codexレビューの結果(2026-08-02)

オーナーの指示により、本ADRのdraftを `codex exec`(gpt-5.6-sol)で批判的レビューにかけた。判定は `request-changes`、blocker 4件・major 7件・minor 3件。指摘された事実主張はすべてCLIの実挙動で裏付けを取り、本文へ反映した。主な修正:

- CLI側のセッション永続化を見落としていた(上記4)→ Decision 5.5を新設
- 「cwdを空ディレクトリにすれば指示ファイル経路は閉じる」は不十分。`CLAUDE.md` / `AGENTS.md` は**祖先ディレクトリへ遡って**探索され、`~/.codex/AGENTS.md` も実在する → Decision 5.1を厳格化
- 「promptを保存しなくても完全再構成できる」という論証は成立しない → Decision 7で保証範囲を限定
- ArtifactBase必須の `confidence` が生成経路から欠落していた → Decision 6で責務を確定
- CLIバージョンの「pin」と「下限許可」が自己矛盾 → Decision 1でexact allowlistに変更
- リトライの実呼び出し回数の見積りが誤り(最大2ではなく最大6)→ Decision 8で logical call と attempt を分離

### 判断軸

ADR-0003 / ADR-0004と揃えたうえで、LLM特有の軸を加える。

- **セットアップ最短**: 追加契約・追加課金なしで、既存のサブスクリプションだけでskillを実行できる
- **テスト容易性**: 実LLMなしで `uv run pytest` がgreenになる(T-027 DoD)
- **将来移行性**: provider追加・API直結への切替をadapter追加に局所化する
- **§15.4の遵守**: private chain-of-thought・raw secret・raw production dataを保存しない。**保存先はveridiaのstoreに限らない**
- **§16.4の前提**: LLMへの入力(対象プロダクトのPR diff・コード・チケット・仕様書)は**信頼できない入力**である
- **§17.0 / 計画§7の方針**: Phase 1のLLM出力は「候補生成 + 人間レビュー必須」から始める

### 現行の実装境界

| モジュール | 本ADRへの含意 |
|---|---|
| `tool_gateway/` | allowlist + input/output schema検証付きの**tool実行**境界。`redaction.py` の `SECRET_KEY_PARTS` はkey名に `session` を含む値をsecret扱いする |
| `trace_store/` | 許可event typeは `tool_call` / `error` / `run_metrics` の3種のみ。`TraceRecord` で構造化payloadを置けるのは `redacted_args`(Mapping)だけで、`result_summary` / `error_summary` は文字列 |
| `trace_ids/` | `IdFactory.new_trace_context()` とchild context生成。`TraceContext.artifact_fields()` がartifactへ `trace_id` を伝播する |
| `evidence_store/` | **ExecutionEvidence専用**であり、任意の入力artifactをimmutable保存する契約ではない |
| `artifact_validator/` | `schemas/*.schema.json`(正本)による検証。`ArtifactValidationError` が `field_path` / `schema_path` / `validator` をmachine-readableに返す |
| `schemas/artifact-base.schema.json` | `confidence` / `source_refs` を含む10 fieldが必須。`minLength` / `minItems` / `pattern` / `minimum`・`maximum` / `format` を使い、`additionalProperties` は意図的に開いている |

## Options

### A. 実行経路

| 候補 | 内容 | 長所 | 短所 |
|---|---|---|---|
| A1. API直結 | `anthropic` SDKで `/v1/messages` を直接呼ぶ | 単発推論としてクリーン。harness overheadがない。usage/costが正確。CLI側のセッション永続化が無い。環境非依存で再現性が高い | **オーナーがAPI keyを保有せず、サブスクリプション範囲外の従量課金契約が新たに必要になる。** Phase 1の前提を満たさない |
| A2. サブスクリプションCLIのheadless実行 | `claude -p` / `codex exec` を非対話で呼ぶ | 追加契約・追加課金なし。Claude / Codex両方を同じ形で扱える。両CLIともJSON Schema制約出力を持つ。`.claude/commands/run-task-codex.md` にheadless codex運用の実績がある | CLIはtoolを持つagentであり無害化が要る。開発者マシンの設定・プロジェクト文脈・指示ファイルが流入しうる。**CLIがpromptをローカル永続化する。** harness overheadが大きい。CLIのフラグ・出力形式はAPIほど安定した契約ではない。従量課金の代わりにレート制限が効く |
| A3. Bedrock / Vertex経由 | cloud provider経由で呼ぶ | クラウド課金へ寄せられる | cloud credential管理面が増える。platformごとの機能差がある。サブスクリプション範囲外 |

**A2を採用する。** A1の利点は実在するため排除せず、interfaceに実装の口を残す。ただし移行はADR-0005のamendまたはsupersedeを必須とする(Consequences)。

### B. 呼び出し境界

| 候補 | 内容 | 長所 | 短所 |
|---|---|---|---|
| B1. 各skillからCLIを直接呼ぶ | skillごとにsubprocessを起動する | 実装が最短 | 可用性検証・hermetic化・trace記録・消費量集計・リトライを11 skillで重複実装する。T-027 DoDの「差し替え可能な境界」を満たせない |
| B2. Tool Gateway経由 | `ToolGateway.execute("llm.complete", payload)` として通す | audit logを `AuditedToolGateway` から流用できる | §5.6のTool Gatewayは**agentが外界へ働きかけるtool呼び出し**の境界である。LLMはagentの推論エンジンであってagentが選択するtoolではなく、同一allowlist・同一guardrailに載せると権限境界の意味が崩れる。実務上も、(a) `tool_call` として記録するとevent種別を誤分類する(§15.2は `model config` / `run metrics` を別行に持つ)、(b) `redact_tool_args()` はkey名ベースでprompt本文には効かない、(c) `result_summary` は文字列でありtoken usage / costを構造化保存できない |
| B3. 専用の `LLMClient` interface | Tool Gatewayと**並列の**境界を1つ立て、skill runner(T-027)が所有する | 責務が明確。fake実装で決定的テストができる。複数backendを同一interfaceで扱える。hermetic化・trace・消費量・リトライを1箇所に集約できる | 境界が2本になる。両者の規約(trace context伝播・保存前redaction・fail fast)を揃える運用が要る |

**B3を採用する。**

### C. LLM消費量 / コストの記録先

| 候補 | 内容 | 長所 | 短所 |
|---|---|---|---|
| C1. Trace Storeの `run_metrics` record | §15.2の「run metrics: latency、token、cost」行に対応させる | North Starの割当と一致する。既存の `find_by_run_id` でrun単位に集約でき、T-052の要求をそのまま満たす。新規storeが不要 | Phase 0で保存実績のないevent typeであり、payloadのfield契約を本ADRで定める必要がある |
| C2. Evidence Store | ExecutionEvidence相当として保存する | 既存の保存APIが使える | §15.3の保存対象にコストは無い。Evidence Storeは品質判定の証拠であり、実行プロセスのメタデータを混ぜると§15.1の分離が濁る |
| C3. 専用のcost store | 3つ目のstoreを作る | 集計に最適化できる | 数値数種類のためにstoreを増やす正当化がない。ADR-0003の分離方針にも反する |

**C1を採用する。**

## Decision

Phase 1のLLM skillは、**オーナーのサブスクリプション契約下にあるCLI(`claude` / `codex`)を、skill runnerが所有する `LLMClient` 境界経由で、隔離済み・schema制約付きの単発呼び出しとして実行する**。本ADRは決定の記録であり、実装はT-027のスコープである(本ADRの採択で `skill_runner/` を作らない。依存追加も行わない)。

**隔離の強度はbackendで異なる。これを決定の一部として明示する。**

| backend | 隔離の位置づけ | 根拠 |
|---|---|---|
| `claude_cli` | **hermetic**(要件を機械的に満たせる) | `--tools ""` で全builtin toolを無効化でき、`--system-prompt` で指示部をroleごと置換でき、`--no-session-persistence` で痕跡を残さない |
| `codex_cli` | **best-effort isolation**(既知の残存リスクを受容する) | builtin toolをゼロにできず、`-s read-only` はhost読み取りを禁じない。system prompt置換フラグが無く、指示/データ分離は区切り依存。グローバル指示ファイルの除外も未確定 |

`codex_cli` を「hermetic」とは呼ばない。オーナーは制限を明記したうえで制約なしに使う判断をした(2026-08-02)ため実装するが、**要件を満たしているという記述にはしない**。残存リスクはConsequencesに列挙する。

### 1. 実行経路とバージョン固定

- **headless CLI実行**を採る。API直結はPhase 1では実装しない
- backendは2つ: `claude -p`(Claude Code CLI)と `codex exec`(Codex CLI)
- promptはシェル引数に埋めず**stdin経由で渡す**(引数長・クォート・変数展開の事故を防ぐ。`.claude/commands/run-task-codex.md` の既存運用と同じ)
- **CLIバージョンはexact allowlistで固定する。** `>=` による下限許可はしない。CLIはAPIのようなバージョン契約を持たず、フラグ・出力envelope・既定system promptが更新で変わりうるため、「検証していないバージョンは通さない」を既定にする
  - Phase 1の検証済みバージョン: `claude` **2.1.207** / `codex-cli` **0.145.0**
  - allowlistはpolicy側のversioned configとして持ち、追加は実測検証とセットで行う
- **起動時にcapability probeを行う。** バージョン文字列の一致だけでは不十分であり、次を実行前に検証する。検証結果はtraceへ記録する
  1. 必須フラグが受理されること
  2. schema制約出力が期待どおり得られること(Decision 6のportable profileで)
  3. usage / 実行model / 終了状態が機械可読に取得できること
  4. セッション永続化の抑止が効いていること(Decision 5.5)

### 2. provider / model

- 既定backend: **`claude_cli`**、既定model **`claude-opus-5`**、effort **`high`**
- 併用backend: **`codex_cli`**、model **`gpt-5.6-sol`**、effort **`high`**
- model IDはaliasではなく完全名で指定する(`opus` のようなaliasは指す先が時期で変わるため使わない)
- effort・sandbox・その他パラメータは**毎回明示指定する**。CLIやユーザ設定の既定値に依存しない

**model選択はPhase 1では単純な既定 + 明示overrideに留める。** skill manifestに `model_tier` のような抽象層を今は導入しない。Phase 1時点で両tierの割当が同一である以上、manifest schema・policy mapping・runner解決処理を先に作るのは、T-027備考の「過剰設計にしない」に反する投機的実装である。

- 既定は全skillで `claude_cli` / `claude-opus-5`
- skillごとのoverrideは、skill manifestの単一fieldで backend と model を明示指定できる形にする
- tier抽象の導入は、skillごとのprecision実績とコスト差が観測され、**実際に異なる割当が必要になった時点**で行う

**Codexの位置づけ。** `codex_cli` はPhase 1から選択可能なbackendとして実装し、テストで実際に通す。全skillの既定にはしない。同一skillを両backendで実行して出力を比較できる状態が、Phase 3以降でmodel依存性を評価する材料になる。分離保証がclaude backendより弱い点はDecision 5.3 / 5.4に明記する。

**model IDの記録は要求値ではなく実行値を使う。** `created_by.model`(§6.1)にはCLIが報告した実行modelを入れる。要求値と実行値の両方をtraceへ残す。

### 3. 呼び出し境界

`LLMClient` を、Tool Gatewayと並列の実行境界としてskill runner(T-027)側に定義する。**LLM呼び出しはTool Gateway経由にしない。**

```text
skill runner
  ├── LLMClient        ← モデル推論の境界(本ADR)
  │     ├── ClaudeCliLLMClient   (claude -p)
  │     ├── CodexCliLLMClient    (codex exec)
  │     ├── FakeLLMClient        (テスト用。DIでのみ注入する)
  │     └── (将来) AnthropicApiLLMClient   ← 実装しない。口だけ残す
  └── ToolGateway      ← 外界へのtool実行の境界(T-015/T-016、§5.6)
```

`LLMClient` はProtocol(構造的型)として定義する。責務は次に限定する。

1. backendの可用性検証とcapability probe(Decision 1・4)
2. 隔離済みの単発呼び出しの実行(Decision 5)とschema制約出力の取得(Decision 6)
3. リトライ判定(Decision 8)
4. `model_call` / `run_metrics` trace recordの保存(Decision 7・9)

`LLMClient` はartifactの意味を知らない。prompt組み立て・schema選択・artifact組み立ては呼び出し側(skill runner)の責務とする。

**Protocolはbackend固有事情を漏らさない。** 引数はprompt(指示部 / データ部を分けた構造体)、出力schema、backend選択、および呼び出し予算に限る。CLIのフラグ、`--json-schema` と `--output-schema` の差、envelope形式の差はすべて実装側に閉じる。この境界が守られていれば、API直結実装の追加はコード上は局所で済む(ただし移行にはADRのamendを要する。Consequences)。

**backend選択はfail closedにする。** `VERIDIA_LLM_PROVIDER` に**既定値を持たせない**。未設定での実行は文脈付き例外で失敗させる。`fake` を既定にすると、設定漏れのまま本番runが走って**偽のartifactが `status: draft` で保存される**。これは検出が難しく害が大きい。`FakeLLMClient` は環境変数からは選択できないようにし、テストからのDI(コンストラクタ注入)でのみ使う。これによりT-027 DoDの「実LLMなしで `uv run pytest` がpassする」はDI経路で満たす。

### 4. 認証情報の扱い

タスクDoDの「API key管理」を、サブスクリプション実行に合わせて次のとおり読み替えて満たす。

- **runnerは資格情報に一切触れない。** API key・token・OAuth credentialをveridiaのコード、設定、環境変数、trace、evidence、ログ、例外メッセージのいずれにも載せない。認証はCLI自身の資格情報ストア(`claude` のOAuth / keychain、`codex` の `CODEX_HOME`)に完全に委ねる
- **veridiaはAPI keyを要求しない。** `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` を読まない、設定を促さない、未設定を異常として扱わない
- **起動時検証は「keyの存在確認」ではなく「backendの可用性確認」に置き換える。** `LLMClient` の構築時に次を検証し、満たさなければ文脈付き例外でfail fastする
  1. CLI実行ファイルが存在し起動できる
  2. バージョンがallowlistに含まれる(Decision 1)
  3. **認証済みである。** `claude auth` / `codex login` の状態確認サブコマンドで判定する。最初の呼び出しの失敗まで判定を遅らせない
  4. capability probeが通る(Decision 1)
- **`claude --bare` を使わない。** `--bare` はAnthropic認証を「`ANTHROPIC_API_KEY` または `apiKeyHelper` のみ。OAuthとkeychainは読まない」に切り替えるため、サブスクリプション認証と両立しない。hermetic化の目的で `--bare` に手を伸ばさないことを明示的な制約として記録する(Decision 5は別の手段で達成する)

Phase 1で使う環境変数は次に限定する。いずれも秘密情報を含まない。

| 環境変数 | 用途 | 既定 |
|---|---|---|
| `VERIDIA_LLM_PROVIDER` | `claude_cli` / `codex_cli` | **なし(未設定はエラー)** |
| `VERIDIA_LLM_MODEL_DEFAULT` | 既定modelの上書き | policy側の値 |

`ANTHROPIC_API_KEY` はAPI直結実装を追加した場合にのみ使う**予約名**として記録するに留める。Phase 1では参照しない。

### 5. 実行の隔離(CLI固有の必須要件)

本節の要件を全て満たせるのは `claude_cli` のみである(Decision冒頭の表)。`codex_cli` は5.3 / 5.4を機械的には満たせず、best-effort isolationに留まる。要件は両backend共通で示し、達成できない箇所を明示する。

CLIは既定で、開発者マシンとカレントディレクトリの文脈を推論入力に取り込み、実行内容をローカルへ永続化する。実測で「OKと返せ」だけの試行に17K〜35K tokensが積まれ、prompt本文がディスクへ書かれたのはこのためである。skill実行の入力と痕跡が制御下になければ、再現性も§15.4も§16.4も成立しない。したがって次を**必須要件**とする。

**5.1 cwdはveridia・対象repo・ユーザ設定ディレクトリの「外」に作る。**

`CLAUDE.md` / `AGENTS.md` はcwdから**祖先ディレクトリへ遡って**探索される。「空ディレクトリであること」と「指示ファイルを持つ祖先の外にあること」は別の条件であり、後者が要件である。

- veridiaリポジトリの内側にcwdを置かない。**ADR-0004のsandbox既定root(`.veridia/sandbox/runs/`)を流用しない** — これはveridia repo内であり、親の `AGENTS.md` が探索対象になる
- **対象プロダクトのリポジトリの内側に置かない。** これは再現性ではなくセキュリティの要件である(Decision 10.2)
- 起動前に、cwdの祖先に指示ファイル(`CLAUDE.md` / `AGENTS.md`)とVCS rootが存在しないことを検証する。検証に失敗したら実行しない

**5.2 開発者マシンの設定・グローバル指示ファイルを継承しない。**

- codex: `--ignore-user-config` を付ける(認証は `CODEX_HOME` から解決され続けることを実測で確認済み)。ただし**このフラグが除外すると明記しているのは `config.toml` だけである。** `~/.codex/AGENTS.md` は実在し(検証時点で0バイト)、除外対象に含まれる保証がない。T-027でmodel-visible promptを実測し、除外できない場合の扱いを決める
- claude: `--safe-mode` および設定ソース・plugin・skill・MCPの読み込み抑止(`--setting-sources` / `--disable-slash-commands` / `--strict-mcp-config` 等)を用いる。`--bare` は使わない(Decision 4)
- 両backendとも、model・effort・sandbox・toolを毎回明示指定する

**5.3 指示部の配置。backend間で保証の強さが異なることを明記する。**

- **claude backend**: `--system-prompt`(既定systemの**置換**)でskillの指示を配置する。`--append-system-prompt`(追記)はCLI既定promptが残るため使わない。指示とデータがroleで分離される
- **codex backend**: `codex exec` に**system prompt置換に相当するフラグは存在しない**。skillの指示はinitial instructionsの先頭に置き、データ部を明示的な区切りで囲む。**分離はroleではなく区切りに依存する**
- したがって **codex backendのinstruction/data分離はclaude backendより弱い。** オーナーはこの制限を明記したうえで制約なしに使う判断をした(2026-08-02)。この差はConsequencesのトレードオフとして記録する

**5.4 外界へ到達するtoolを無効化する。到達可能性はbackendで異なる。**

要件は **「ファイルシステム・ネットワーク・シェルへ到達するtoolを持たせない」** である。実測のとおり `stop_reason: "tool_use"` となる場合があり構造化出力自体がtool機構で配送されるため、「tool数がゼロ」ではなく「外界到達がゼロ」で判定する。

- **claude**: **`--tools ""` を必須とする。** CLI helpは `""` を「disable all tools」と定義しており、builtin toolを機械的に全無効化できる。「絞る」ではなく「全無効化」を既定にする。`--allow-dangerously-skip-permissions` / `--dangerously-skip-permissions` は**使わない**
- **codex**: `-s read-only` と `--ignore-rules` を付ける。ただし **`-s read-only` はmodelが生成したシェルコマンドのsandbox policyであって読み取りtoolの無効化ではなく、host filesystemの読み取りを禁じない。** builtin toolをゼロにする手段は現行CLIに無い

**T-027の測定要件と合否基準。** 「T-027で実測する」だけでは合否が定まらないため、基準と不合格時の扱いをここで固定する。

1. 両backendについて、model-visible promptとtool inventory、network到達性を実測し記録する
2. **claude backendの合格条件**: `--tools ""` 下でfilesystem / network / shellへ到達するtoolが存在しないこと。不合格ならclaude backendを使わない
3. **codex backendの扱い**: 到達可能な範囲を**測定して記録する**ことを完了条件とする。到達がゼロでないこと自体は不合格としない(オーナー判断により受容)。ただし測定を省略したまま実装完了としない
4. **グローバル指示ファイル(`~/.codex/AGENTS.md` 等)がmodel-visible promptに含まれるかを実測する。** 含まれ、かつ除外手段が無い場合は、その事実をREADMEとConsequencesに記録し、当該ファイルを空に保つ運用前提を明示する

呼び出し後、CLIが報告するtool使用の痕跡(claude: `permission_denials` / `num_turns`、codex: `--json` のevent)を検証し、想定外のtool実行があれば失敗として扱う。**ただしこれは事後検出であり、読み取りや送信を防止しない。** codex backendにおいてはこれが唯一の観測手段であり、防御ではないことを明記する。

**5.5 CLI側のセッション永続化を抑止する。**

実測により、両CLIが既定でprompt本文をローカルへ平文保存することを確認した(Context参照)。**veridiaのstoreに保存しないことは、prompt本文がディスクに残らないことを意味しない。** §15.4の保存禁止はveridiaのstoreに限った制約ではないため、次を必須とする。

- claude: **`--no-session-persistence`** を付ける
- codex: **`--ephemeral`** を付ける
- codexの `-o`(最終メッセージのファイル出力)は、raw応答をディスクへ書く。使う場合は権限を絞った一時ファイルとし、読み取り後に確実に削除する。可能なら標準出力の機械可読形式(`--json`)から直接取得して `-o` を使わない
- 抑止が効いていることをcapability probeで検証する(Decision 1)
- **provider側のretentionはveridiaの制御外である。** これは緩和できない残存リスクとしてConsequencesに記録する

**5.6 実際に使用したフラグ集合をtraceへ記録する。** hermetic性は運用で崩れる。どの制約付きで実行されたかを事後検証できるようにする。フラグ集合の確定はT-027の実装事項とし、本ADRは要件のみを課す。

### 6. Schema制約出力とartifact組み立ての責務分担

両backendとも最終応答をJSON Schemaで拘束できる(claude: `--json-schema`、codex: `--output-schema`)。

**6.1 portable schema profileを定義する。**

実測で確認したのは `{answer: string}` という最小schemaのみであり、`minLength` / `pattern` / union / nested object / optional field の互換性は**未検証である**。したがって「これらは非対応」と断定しない。代わりに次を行う。

- Phase 1で使用可能なJSON Schemaキーワードの**portable profile**をkeyword単位で定義し、`qa-skills/` の規約として文書化する
- profileの各keywordについて、両CLIで実際に拘束が効くかをT-027の**capability testで検証する**(Decision 1のprobeに含める)
- skillの `output.schema.json` はこのprofileの範囲に収める。profile外のkeywordはvalidator側(`artifact_validator`)でのみ強制する
- profileの初期案は保守的に置く(`type` / `properties` / `required` / `enum` / `items` / `additionalProperties: false`)。拡張は検証とセットで行う

**6.2 artifact schemaを直接渡さない。**

`schemas/artifact-base.schema.json` は `minLength` / `minItems` / `pattern` / `minimum`・`maximum` を使い `additionalProperties` を意図的に開いており、portable profileと直接互換ではない。

**6.3 field責務の確定。**

| field | 生成主体 | 理由 |
|---|---|---|
| domain固有field(下記の例外を除く) | **LLM** | skillの本体出力 |
| `confidence` | **LLM**(自己申告) | §6.1がArtifactBaseの必須fieldとして定義しており、値の意味上runnerが決定できない |
| `source_refs` | **LLM**(根拠の主張) | 根拠の提示はモデルの出力そのもの。ただしrunner / validatorが解決可能性とtrust levelを検証する(Decision 10.5) |
| **source identity / trust属性**(`source_id` / `uri` / `source_version` / `trust_level` 等) | **connector / ingestion層**(決定的) | 下記のとおり。**domain固有fieldであってもLLMに生成させない** |
| `artifact_id` / `artifact_type` / `version` / `created_by` / `status` / `requires_human_review` / `trace_id` / `created_at` | **runner**(決定的) | 同一性・来歴・ライフサイクル・監査線。モデルに触らせない |

**source identity / trust属性をLLMに生成させない理由。** §5.2はsource trust labelの付与をingestion層の責務としている。これをLLM出力に含めると、§16.4のtrust規則(untrusted / externalをリスク引き下げの根拠にしない)が**自己申告で迂回可能**になる — 入力汚染を受けたモデルが `trust_level: trusted` と出力すれば、Decision 10.5の照合はそのラベルを信じてしまい、「決定的コードによる照合」が成立しない。

したがって:

- source inventory(どのsourceが存在し、そのuri / source_version / trust_levelは何か)は**connector側が決定的に確定する**。skill runnerはそれをprompt組み立て時にデータ部へ与え、出力検証時の照合表として保持する
- LLMが生成してよいのは「どのsourceを根拠として選んだか」という**参照**のみである。参照先の属性は生成させない
- **これはSource Connector(T-026)への依存である。** connectorがtrust_levelを提供しない場合、Decision 10.5のtrust照合は実装できない。この依存は「前提の欠落と申し送り」節に記録する

**source側のversionを `version` という名前にしない。** ArtifactBaseの `version` はartifact自身のsemverであり、source側のversion(commit SHA等)とは別物である。同一JSON keyに両方を持たせられないため、source inventory側は **`source_version`** 等の別名を使う。SourceMap schema上の具体的な表現はT-028のスコープとする。North Starの構造を変える必要が生じた場合はADRを先に起票する(AGENTS.md変更ルール5)。

skillの `output.schema.json` は「domain固有field(source identity / trust属性を除く) + `confidence` + `source_refs`」を出力契約とする。**`confidence` を含めないとArtifactBase必須fieldが埋まらず、最終validatorが必ず失敗する。**

**この分担はセキュリティ上も要である。** `status` / `requires_human_review` / `trace_id` / `artifact_id` / trust属性をLLM出力の一部にしないため、prompt injectionで `status: approved`、`requires_human_review: false`、`trust_level: trusted` を注入することが構造上できない。`source_refs` はモデル生成だが、これは「特権」ではなく「検証対象の主張」である。

**6.4 複数artifactを出すskillの契約。**

1 skillが複数のartifact型を出す場合がある(T-030は1回の実行でRequirementSpec / RiskSpecの候補を生成する)。単一artifact前提では汎用runnerが型を解決できないため、次を契約とする。

- skillの `output.schema.json` は、出力を**名前付きbucketの集合**として表現する
- **bucket名はartifact型名と完全一致させる(identity mapping)。** 現行の `qa-skills/manifest.schema.json` の `outputs` は `required` / `optional` の文字列配列であり写像を表現できない。manifest schemaを変更するより、名前一致を規約にするほうが変更面が小さく、`outputs.required` の宣言がそのままbucketの宣言になる。LLMに `artifact_type` を生成させない点は変わらない(Decision 6.3の分担を崩さない)
- **`outputs.required` の意味を「bucketが存在すること」と定める。** 要素0件を許す。「最低1件のartifactを生成すること」を要求したい場合は、skill側の `output.schema.json` で `minItems` を課す(portable profile外のためvalidator側で強制する)。required = 最低1件、と読まない
- 各bucketは0件以上の要素配列とし、**各要素が `confidence` と `source_refs` を持つ**。artifact単位で§6.1の契約が成立する必要があるため、bucket単位ではなく要素単位で要求する
- **atomicity: 全要素が検証を通った場合のみ保存する。** 1要素でも不適合ならskill実行を失敗させ、部分保存しない。部分保存を許すと、後続のhuman reviewとgateが「欠けている候補があるか」を判別できない
- 修復logical call(Decision 8)の対象は不適合要素を含むbucketに限定してよいが、再生成された出力は全体として再検証する

**6.5 schema制約出力を検証の代替にしない。** CLIのschema制約はbest-effortの拘束であり契約の保証ではない。取得したJSONは必ず `output.schema.json` で再検証し、artifact組み立て後に `artifact_validator` で全schema検証する。

`confidence` は§6.1の注意書きどおり較正されていないため、**Phase 1ではgate条件の入力に使わない**。記録のみとする。

### 7. LLM出力の扱い、再現性の範囲、trace記録

1回のskill実行は次の順で進む。

```text
入力artifactをinput.schema.jsonで検証(fail fast)
  ↓
入力サイズ上限の検査(Decision 10.6)
  ↓
prompt組み立て(指示部 = skill所有 / データ部 = 信頼できない入力)
  ↓
┌─ attempt loop(Decision 8) ──────────────────────────────┐
│  隔離済みCLI呼び出し(Decision 5) + schema制約出力(Decision 6)  │
│    ↓                                                     │
│  終了状態とtool使用痕跡の検証(Decision 5.4)               │
│    ↓                                                     │
│  output.schema.json検証                                   │
│    ↓                                                     │
│  ArtifactBase envelopeを組み立て                          │
│    (status: draft / requires_human_review: true)         │
│    ↓                                                     │
│  artifact_validatorでartifact全体を検証し、不適合の原因を   │
│    分類(LLM由来 / runner由来。Decision 8)                │
│    ↓                                                     │
│  ★ outcomeを確定し、成否によらず model_call / run_metrics │
│     を保存(finally相当。retry判定より前) ★               │
│    ↓                                                     │
│  不適合なら修復判定へ戻る                                  │
└──────────────────────────────────────────────────────────┘
  ↓
artifact本体を永続化(全要素が通った場合のみ。Decision 6.4)
```

**trace保存はattemptごとに、成否によらず行う。** 検証成功後にまとめて保存する設計にすると、失敗attemptのtoken・cost・latencyが記録から落ち、T-052が消費量を**過少集計する**。`run_metrics.outcome` が `retryable_error` / `terminal_error` を持つのはこのためであり、失敗attemptを記録しない実装は契約と矛盾する。

**保存位置は「検証・分類の後、retry判定の前」である。** `outcome` はtool使用痕跡・output schema・**artifact全体の検証**の結果が出て初めて確定する。Trace Storeの保存APIはinsert-onlyであり後から更新できない(`trace_store/repository.py`)ため、**保存を分類より先に置いてはならない。**

**artifact全体の検証はattempt loopの内側に置く。** Decision 8はLLM生成fieldに起因するartifact schema不適合を修復対象としているため、artifact検証をloopの外に置くと、`success` として保存済みのattemptの後から修復可能な不適合が判明し、insert-onlyのtraceに誤ったoutcomeが確定保存される。envelope組み立てとartifact検証をloop内で行い、不適合の原因(LLM由来 / runner由来)を分類してからoutcomeを決める。**artifact本体の永続化だけはloopの外**(全attempt完了後)でよい。

実装上は `finally` 相当の位置に保存を置き、例外経路でも必ず1回保存されるようにする。

**`model_call` と `run_metrics` の2 recordはatomicに扱う。** 片方だけが保存された状態は、traceとmetricsの不整合として集約側に現れる。両方の保存が成立しない場合はattemptを `terminal_error` として扱い、fail closedにする(部分的な記録を残したまま成功扱いにしない)。

artifact保存だけを成功時の別段階に置く。

- 生成artifactは **`status: "draft"` かつ `requires_human_review: true`** で保存する。§6.1のenum以外の値を発明しない
- 検証に失敗したartifactは保存しない。部分的な成果物を残さない(Decision 6.4のatomicity)
- **artifactの保存先そのものがPhase 1で未整備である。** 「前提の欠落と申し送り」節を参照

**7.1 promptの記録: 指示部は全文、データ部は参照。**

T-027 DoDの「prompt・model・パラメータを含む。redaction適用して記録」を、次の形で満たす(オーナー承認済み、2026-08-02)。

| prompt構成要素 | 出所 | 記録 |
|---|---|---|
| **指示部**(system prompt / prompt template のrendered結果) | **veridia自身**が書いたもの | **全文を記録する。** 対象プロダクト由来の内容を含まないため§15.4に抵触しない。デバッグ価値が最も高い部分でもある |
| **データ部**(対象プロダクトのdiff・コード・チケット等) | 信頼できない外部 | **本文は記録しない。** 入力artifactへの参照 + content digest のみ |
| rendered prompt全体 | 合成結果 | SHA-256 digest のみ |

これは「redactionを適用したprompt記録」の一形態である。データ部を機械的にマスクするのではなく、**構成要素の出所で分離する**。自由テキストのredactionは検出漏れがそのまま§15.4違反になるため、出所による分離のほうが確実である。

**7.2 再現性の保証範囲。**

**LLM出力は非決定的である。決定性を主張しない。** ADR-0004のsandbox決定性はLLM skillには及ばない。CLI経由ではCLIバージョン・CLI既定promptの変更という非決定要因も加わる。gate判断に対する保証は決定的フロア(§12.5)と人間レビュー(§17.0)が担う。

再現性について保証するのは、**「runnerがrenderしたapplication promptの同一性を検証できる」ことに限る。** 「promptを保存せずとも完全に再構成できる」とは主張しない。理由:

- CLIが注入するsystem prompt・tool定義はveridiaの制御外であり、バイト単位の再構成対象に含められない
- 完全再構成には入力artifactのimmutableな本文が必要になるが、汎用Artifact Storeは現時点で存在しない(`evidence_store/` はExecutionEvidence専用)
- そもそも、再構成に足るだけの入力本文をどこかに保存するなら、「prompt本文を保存しないから§15.4を守れている」という説明は循環する。§15.4の遵守はartifact層が何を保存するかに依存しており、prompt層だけでは完結しない

**7.3 保存するもの / しないもの。**

保存する:

| 項目 | 保存先 |
|---|---|
| backend種別 / **CLIバージョン** / 実行フラグ集合 / capability probe結果 | `model_call` |
| 要求model・effort / 実行model・effort | `model_call` |
| **指示部の全文** と そのdigest | `model_call` |
| **skill package の commit または content digest** / prompt template ID・version / renderer version | `model_call` |
| **output schema の digest** | `model_call` |
| 入力artifactの `artifact_id` / `trace_id` / **content digest** | `model_call` |
| rendered prompt全体のSHA-256 digest | `model_call` |
| 終了状態(`stop_reason` / `num_turns` / tool使用痕跡)/ **logical call ID と attempt番号** / 所要時間 | `model_call` |
| token usage / コスト参考値 | `run_metrics`(Decision 9) |

保存しない:

- **データ部の本文**(対象プロダクトのdiff・コード等)。§15.4のraw production data / 不要なPII / raw secretの混入経路
- **thinking / reasoningの内容**(private chain-of-thought。§15.4で明示的に保存禁止)。claude側はthinking表示を有効化せず、codex側は `reasoning summaries: none` の既定を変えない
- **完了テキストの生データ**。検証を通ったartifactが成果物である
- **CLIのsession idの生値**。既存redaction規約は key名に `session` を含む値をsecret扱いしており(`tool_gateway/redaction.py`)、生値の保存はこれと衝突する。相関が必要な場合は**digestを保存する**

**7.4 Trace Storeへの追加。** 許可event typeに **`model_call` を追加する**。§15.2はTrace Storeの保存対象に `model config` 行を持っており、この追加はNorth Starからの逸脱ではなくPhase 0で先送りしていた範囲の解禁である。実装(`trace_store/records.py` の `ALLOWED_EVENT_TYPES` 追加とREADME更新)はT-027で行う。既存recordのfield構成は変えず、構造化payloadは `redacted_args` に versioned schema で載せる(Decision 9と同じ方式)。

### 8. リトライ方針

T-027 DoDが「schema不適合時のリトライ方針はADR-0005に従う」と記載しているため、ここで確定する。**logical call と attempt を区別する。**

- **logical call**: 1回の意味的なLLM要求。初回と「修復」で最大 **2**
- **attempt**: logical callに対する実際のCLI起動。一時的失敗の再実行を含めて各logical callあたり最大 **3**
- したがって **1 skill実行あたりのLLM要求attemptは最大6回** である

**この6回は「attempt数の上限」であって、消費量の数値的な上界ではない。** attempt数を固定しても、1 attemptが消費するtoken量に上限がなければ総消費は決まらない。したがって次を併せて要件とする。

- **attemptごとの予算を明示指定する**: 実行時間のtimeout、出力token上限、turn数上限。CLIが該当の制御を持たない場合はその旨を記録し、timeoutを最終防壁とする
- **capability probe(Decision 1)はattempt数に含まれない。** probeが実推論を伴う場合、その消費も `run_metrics` に記録する。probe結果はプロセス単位でcacheし、skill実行のたびに再実行しない
- 数値的な上界が必要になった時点で、attempt予算の実測値から算出する。現時点では算出しない

| 失敗 | 扱い | 上限 |
|---|---|---|
| CLIの一時的失敗(プロセス異常終了、ネットワーク起因) | 同一logical call内で指数backoff再実行 | attempt 3まで |
| **レート制限 / 使用量上限** | 再実行**しない**。runを止めて上限到達として報告する。待機時間が時間枠単位になりうるため自動待機でrunを塞がない | 0 |
| **LLM由来fieldのschema不適合**(`output.schema.json` 不適合、またはLLM生成fieldに起因するartifact schema不適合) | **修復logical callを最大1回**。`ArtifactValidationError` の `field_path` / `schema_path` / `validator` を機械可読な指摘として渡す | logical call 2まで |
| 出力がJSONとして取り出せない | 同上 | logical call 2まで |
| **runner生成envelope由来の不適合** | 修復リトライ**しない**。runnerの欠陥でありLLMに直せない。文脈付きエラーで失敗させる | 0 |
| 想定外のtool実行痕跡 | 再実行**しない**。hermetic化の破れであり設定の欠陥として失敗させる | 0 |
| 認証エラー / CLI不在 / バージョン非allowlist / probe失敗 | 再実行**しない**。可用性エラーとして起動時検証へ差し戻す | 0 |
| 入力artifactのschema不適合・入力サイズ上限超過 | 再実行**しない**。呼び出しの前にfail fastする | 0 |

理由:

- 無制限のリトライは所要時間とレート制限の消費を非決定的に膨らませる。サブスクリプション運用では消費が金額ではなく**時間枠**で効くため、暴走の代償が「請求」ではなく「一定時間なにも実行できない」形で現れる
- schema不適合が繰り返す状態はskillまたはprompt templateの欠陥である。リトライで覆い隠すのではなく失敗として表面化させるべきである(計画§7の「候補生成 + 人間レビュー必須」と整合する)
- 修復logical callの結果もschema不適合なら、`error` trace recordを残してskill実行を失敗させる。artifactは保存しない

**成果物の扱いの用語を統一する。** 「検証を通っていないartifactは保存しない」(本Decision)と「上限到達時に部分的成果を保持する」(Decision 9)は別の対象を指す。前者は**当該skillの未完成出力**、後者は**同一run内で既に検証を通り保存済みの他skillのartifact**である。後者はrunの中断時に破棄しない。

**backend間の自動fallbackを行わない。** `claude_cli` の失敗時に `codex_cli` へ暗黙に切り替えない。gate判断に影響するartifactを生成したmodelは `created_by.model` として監査可能でなければならず、暗黙の切替は監査線を弱める。backend切替は明示的な設定変更として行う。

### 9. 消費量とコストの記録

**記録先: Trace Storeの `run_metrics` record。** §15.2の「run metrics: latency、token、cost」に対応する。T-052はこのrecordを `find_by_run_id` で集約する。

**9.1 保存契約。** 既存 `TraceRecord` で構造化payloadを置けるのは `redacted_args`(Mapping)のみであり、`result_summary` は文字列である。したがって `run_metrics` のpayloadは `redacted_args` に**versioned schemaで載せる**。T-052が決定的に集約できるよう、次を機械可読な契約として定める(schemaの正本化はT-027)。

| field | 型 | nullable | 意味 |
|---|---|---|---|
| `payload_version` | string | no | payload schemaのsemver。破壊的変更時に上げる |
| `call_kind` | string | no | **`skill_attempt` / `capability_probe`**。下記のとおりprobeもLLMを消費するため同一payloadで表す |
| `logical_call_id` | string | probe時のみyes | Decision 8のlogical call識別子 |
| `attempt` | integer | probe時のみyes | 1始まり |
| `outcome` | string | no | `success` / `retryable_error` / `terminal_error` |
| `backend` | string | no | `claude_cli` / `codex_cli` |
| `model` | string | no | **実行値** |
| `input_tokens` / `output_tokens` | integer | **yes** | backendが報告しない場合はnull。0で埋めない |
| `cache_read_input_tokens` / `cache_creation_input_tokens` | integer | **yes** | 同上 |
| `reference_cost_usd` | number | **yes** | 単位はUSD。**取得できない場合はnull**(Codexは報告しない) |
| `latency_ms` | integer | no | |
| `skill_id` / `skill_version` | string | probe時のみyes | probeはskillに紐づかない |

「報告されない」と「0である」を区別する。nullを0で埋めると集計が静かに誤る。

**capability probeの帰属。** probeは実推論を伴う場合があり消費が発生するが、skillにもlogical callにも紐づかない。`call_kind: capability_probe` で区別し、skill関連fieldはnullにする。probeはプロセス単位でcacheされるため、**そのprocessで最初にprobeを必要としたrunの `run_id` に1回だけ帰属させる。** cache再利用時に再計上しない(同じ消費を複数runへ二重計上しない)。集約側は `call_kind` で probe を含める/除くを選べる。

**9.2 独自の単価表を持たない。** `claude -p --output-format json` は `total_cost_usd` と `modelUsage[model].costUSD` を返す。これをそのまま記録する。単価表をveridia側に持つとCLI側の単価改定と二重管理になり、過去の記録が後から書き換わる危険もある。

**9.3 コストは「参考値」であって請求額ではない。** field名を `reference_cost_usd` とし `cost_usd` としない。オーナーの契約はサブスクリプションであり、この値は従量課金換算の参考量である。実請求と一致しない。KPI(§19.2)としてはトレンド把握とskill間の相対比較に使い、会計値として扱わない。**backend横断の比較はUSDではなくtoken数を主軸に行う**(Codexが報告しないため)。ただしtokenの意味もmodel間で厳密には揃わない。

**T-052への集約契約。** `schemas/quality-analytics-snapshot.schema.json` の対応fieldは `cost.llm_cost_usd`(「未収集の場合はnull」)であり、本ADRの `reference_cost_usd` とは名前も含意も異なる。そのまま転記すると「参考値であって請求額ではない」という区別が失われる。したがって集約規則を次のとおり定める。

- **全attemptの `reference_cost_usd` が非nullの場合のみ**、その総和を `llm_cost_usd` に入れる
- **1件でもnullが混じるrunでは `llm_cost_usd` を null にする。** 既知分だけの部分合計を入れない。部分合計は「安く見える」方向にのみ誤り、コスト判断を誤らせる
- 集約対象には**失敗attemptとprobeを含める**。実際に消費された量が集計値であるべきで、成功分だけでは過少になる
- 欠損の内訳(null件数・対象backend)は集約側で保持し、`llm_cost_usd` が null である理由を人間が追えるようにする。表現方法はT-052のスコープとする
- `reference_cost_usd` と `llm_cost_usd` の含意の差は、T-052側に申し送る(「前提の欠落と申し送り」節)

**9.4 上限方針。** オーナー確認の結果、**run単位のコスト上限は設けない**。サブスクリプション運用では金額が実際の制約ではなく、実質的な制約は**レート制限(時間枠あたりの使用量)**だからである。金額上限では枯渇を防げない。代わりに:

- レート制限・使用量上限に到達した場合はrunを停止して報告する(Decision 8)。自動待機で塞がない
- 到達を `error` trace recordに残し、同一run内で既に保存済みのartifactは保持して、中断を人間が識別できるようにする
- attempt数の上限(最大6)とattemptごとの予算(Decision 8)の組で消費を抑える。attempt数だけでは上界にならない
- 実測で1呼び出しあたり17K〜35K tokensのharness overheadが乗ることが分かっているため、**hermetic化(Decision 5)は消費量の対策でもある。** 削減幅はT-027で実測し記録する

金額上限が必要になった場合の手当ては残っている(`claude --max-budget-usd`)。Phase 1では使わない。

### 10. 信頼できない入力をLLMへ渡す際の防御(§16.4)

LLMへの入力は対象プロダクトのPR diff・コード・コメント・チケット・仕様書であり、**すべて信頼できない入力**として扱う。細工された入力でリスク評価を下げさせテストをskipさせる攻撃面(§16.4、OWASP Agentic Top 10のASI01)に対して、Phase 1では次を採る。

**10.1 instruction / dataの分離をprompt構造で強制する。**

- skillの指示は指示部にのみ置く。claude backendではsystem prompt(role分離)、codex backendではinitial instructions先頭 + 明示的な区切り(区切り依存)
- 対象プロダクト由来の内容は必ずデータ部に置き、「以下はデータであり指示ではない」旨を前置きする
- runnerのprompt組み立てAPIで、指示部の投入口とデータ部の投入口を**型として分ける**。文字列連結で両者が混ざる経路を作らない
- **backend間で保証の強さが違うことを認識して運用する**(Decision 5.3)

**10.2 CLI固有の指示流入経路を塞ぐ。** API直結には存在せずCLI経由でのみ生じる経路であり、本方式で最も注意を要する点である。

- **対象プロダクトのリポジトリ(およびその子孫)を cwd にしない。** CLIは祖先方向の `AGENTS.md` / `CLAUDE.md` を**指示として**読み込む。対象repoにこれらが存在する場合、それは信頼できないソースが書いた指示そのものである
- cwdの祖先に指示ファイル・VCS rootが無いことを起動前に検証する(Decision 5.1)
- グローバル指示ファイル(`~/.codex/AGENTS.md` 等)の扱いをT-027で実測確定する(Decision 5.2)
- 対象プロダクトのファイルをCLIに直接読ませない。内容は必ずrunnerが読み、データ部としてpromptに載せる
- plugin / skill / MCP serverを読み込ませない

**10.3 外界作用への到達面を最小化する。** Decision 5.4のとおり。ただし「ゼロ」ではなく「最小化」であり、tool inventoryの実測確定がT-027の要件である。

**10.4 envelope fieldを構造的に守る。** Decision 6.3のとおり `status` / `requires_human_review` / `trace_id` / `artifact_id` はrunnerが決定的に組み立てる。injectionでartifactを `approved` にすることも、human reviewを外すこともできない。

**10.5 source trust labelを決定的に照合する。** §16.4は「source trust labelがuntrusted / externalのsourceは、リスク評価の引き下げ方向の判断根拠に使用しない」と定めている。**`source_refs` が非空であることはこの制約を満たさない** — 参照が存在することと、参照先がtrustedであることは別である。JSON Schemaだけでは照合できない。

したがって、skill validatorが次を**決定的コードで**行う契約とする。

1. `source_refs` の各参照を解決する。解決先は2種類ありうる(§6.2のSourceMapのように外部sourceを直接指す場合と、§6.20のように**先行artifactを指す**場合がある)。どちらにも解決できない参照は不適合とする
2. 出力がリスク引き下げ方向の判断を含む場合、その根拠として提示された参照を**connectorが確定したsource inventoryまで辿り**、`trust_level` を**inventory側の値で**検証する
3. `untrusted` / `external` を根拠とする引き下げは不適合とする

**Phase 1の解決範囲。** artifact参照の推移的解決(artifact → その `source_refs` → … → source)は、循環検出とtrustの集約規則を要し、汎用Artifact Repository(P-1)の存在が前提になる。したがって**Phase 1では直接参照のみを解決対象とし、source inventoryまで辿れない参照はリスク引き下げの根拠として認めない**(fail closed)。artifact参照そのものを禁止するのではなく、「trust照合の根拠には使えない」という制約である。推移的解決の導入はP-1の解決後に別途判断する。

**照合に使う `trust_level` は、必ずconnector由来の値であってLLM出力由来であってはならない**(Decision 6.3)。LLMが生成したSourceMapのラベルを信じて照合すると、入力汚染を受けたモデルが `trusted` と出力するだけで規則を迂回でき、決定的照合が成立しない。

判断方向の識別方法は各skillの出力契約に依存するため、具体形は各skillタスクのスコープとする。本ADRは「JSON Schemaによる非空検査では不十分であり、SourceMap解決とtrust_level照合を決定的に行う」ことを要件として課す。

**10.6 入力サイズの上限を設ける。** 巨大なdiffはcontext圧迫と使用量枯渇を同時に引き起こし、レート制限運用では後者が実害になる。入力のbyte数 / 概算token数 / source数に上限を設け、超過時の扱い(reject または truncation とその記録)をskillの入力契約に含める。無言のtruncationはしない。

**10.7 gate判断は決定的フロアと人間レビューを併用する。** §12.5と§17.0のとおり。LLM推論のみを根拠とするskip・引き下げを認めない。Phase 1の全LLM出力は `requires_human_review: true` である。

**10.8 injection caseをskill evalの標準ケースに含める。** §7.1のskill packageは `evals/negative_prompts.csv` を持つ。gate操作を狙う入力汚染(細工されたPR説明文・コメント)に加え、**対象repoの `AGENTS.md` を模した指示注入**をケースに含めることを、各LLM skillタスクの要件とする。ケースの作成は各skillタスクのスコープである。

**Phase 1でやらないこと。** 入力の機械的なinjection検出・分類は行わない。上記は構造による緩和であり検出ではない。検出器の導入はPhase 2以降の課題として残す。

## 前提の欠落と申し送り

本ADRの検討過程(Codexレビューを含む)で、**本ADRのスコープ外にあるが、この決定を実装可能にするために解決が必要な前提**が見つかった。ADRの決定として解決せず、事実として記録する。T-025のスコープは「LLM skill実行方式の決定」であり、下記は他タスクの領域である(AGENTS.md: T-025以外のPhase 1タスクに着手しない)。

| # | 欠落 | 影響 | 解決の所在 |
|---|---|---|---|
| P-1 | **生成artifactの保存先が存在しない。** `evidence_store/` はExecutionEvidence専用、`trace_store/` はtrace専用であり、RequirementSpec / RiskSpec等の汎用artifactをimmutableに保存・読み出しする層がPhase 1のどのタスクにも無い | **T-027のDoD「生成artifactを `status: draft` かつ `requires_human_review: true` として保存し」を満たせない。** 後続のhuman review(T-031)、artifact集約(T-052)、Decision 10.5の推移的trust解決も同じ層を必要とする | **T-027着手前のhard gateとする。** 新しい永続化境界と複数artifactのatomic write(Decision 6.4)を伴うため、T-027の実装詳細ではなく別タスクまたはADRの候補。**オーナー判断事項** |
| P-2 | **T-052の `blocked_by` にT-027が無い**(現状 `[T-048]`)。`run_metrics` のpayload schemaを実装するのはT-027である | T-027完了前にT-052へ着手すると、集約対象の契約が存在しない | T-052の依存関係更新 |
| P-3 | **Source Connector(T-026)がsource inventory(`source_id` / `uri` / `source_version` / `trust_level`)を決定的に提供する必要がある** | 提供されない場合、Decision 10.5のtrust照合が実装できず、§16.4のtrust規則が担保されない | T-026のDoD確認・拡張 |
| P-4 | `reference_cost_usd`(本ADR)と `cost.llm_cost_usd`(QualityAnalyticsSnapshot schema)の**含意の差**。前者は従量課金換算の参考値、後者は名称上コストそのもの | 転記時に「請求額ではない」区別が失われる | T-052での表現方法の決定。集約規則自体はDecision 9.3で確定済み |

P-1は本ADRの採択可否には影響しないが、**T-027の着手前に解決が必要**である。P-2〜P-4は各タスクの着手時に解消できる。

## Consequences

### 良い影響

- **追加契約・追加課金なしでPhase 1に着手できる。** オーナーの既存サブスクリプションだけでLLM skillが動く
- **runnerが秘密情報を一切扱わない。** API keyの保管・ローテーション・漏えい面がveridia側に存在しない。DoDの「API key管理」を、要件として強い形で満たす
- ClaudeとCodexを同一interfaceで扱えるため、同じskillを2つのmodelで実行して比較できる。model依存性の評価材料がPhase 1時点から取れる
- backend選択をfail closedにしたため、設定漏れのまま偽artifactが保存される事故が起きない
- ArtifactBase envelopeをrunnerが決定的に組み立てるため、`status` / `requires_human_review` がLLM出力面から到達不能になる。§17.0の「候補生成 + 人間レビュー必須」がprompt依存ではなく構造で成立する
- prompt記録を「指示部は全文・データ部は参照」に分けたため、デバッグ価値の高い部分を失わずに§15.4を守れる
- 消費量をTrace Storeの `run_metrics` に寄せ、payloadを versioned schema で定義したため、T-052は決定的に集約できる
- CLI側が報告するコスト参考値をそのまま使うため、単価表の二重管理が発生しない
- Tool GatewayとLLMClientを分けたことで、§5.6のallowlist / guardrailの意味(外界への作用の制御)が保たれる

### トレードオフ

- **CLIはAPIのような安定した契約ではない。** exact allowlistとcapability probeで検知はできるが、CLI更新のたびに検証と追随のコストが発生する。バージョンを上げるまで新機能を使えない硬直も生じる
- **harness overheadが大きい。** 実測で1呼び出しあたり17K〜35K tokens。hermetic化で削減するが、API直結の水準にはならない
- **実質的な制約が金額ではなくレート制限になる。** 枯渇すると一定時間skillが実行できない。T-056のE2E検証で複数skillを連鎖させる際、時間枠を食い潰してrunが止まる可能性がある。金額上限では防げない
- **codex backendはhermeticではない。** `codex exec` にsystem prompt置換フラグが無く指示とデータがroleではなく区切りで分かれる。builtin toolをゼロにする手段が無く、`-s read-only` は生成コマンドのsandboxであってhost filesystemの読み取りを禁じない。グローバル指示ファイル(`~/.codex/AGENTS.md`)の除外可否も未確定である。つまり **host読み取りと指示流入の残存リスクを受容したbest-effort isolation** であり、Decision 5.4の要件を機械的には満たさない。**オーナーはこの制限を認識したうえで、制約を設けずCodexを使う判断をした(2026-08-02)。** claude backendは `--tools ""` により要件を満たせるため、両backendの隔離強度は同等ではない
- **隔離は設定で担保するものであり、破れやすい。** cwd・フラグ・設定ソースのいずれかを取り違えると、開発者マシンの文脈や対象repoの指示が推論入力へ流入する。Decision 5.6の記録とtool使用痕跡の検証は**事後検出であって防御ではない** — 読み取りや送信が起きた後に気づくだけである。実際の防御は `--tools ""`(claude)とcwd配置であり、codex backendでは前者が使えない
- **provider側のretentionはveridiaの制御外である。** ローカルのセッション永続化は抑止できるが、provider側に何がどれだけ残るかは契約とproviderのポリシーに依存する。これは緩和できない残存リスクである
- **toolを完全にゼロにはできない。** 構造化出力自体がtool機構で配送されるため、「外界へ到達しない」という条件付きの無害化に留まる。何が到達可能かはT-027の実測で確定する
- **決定性がない。** 同一入力の再実行が同一artifactを返す保証はない。regression testはfake実装に対してのみ決定的であり、実LLMに対するskill品質はeval(§7.1 `evals/`)で確率的に測るしかない
- **再現の保証は「application promptの同一性検証」に限られる。** 完全なバイト単位の再構成はできない(CLI注入部分がveridiaの制御外、汎用Artifact Storeが未整備)
- **修復logical call 1回の上限は、schema不適合が散発する初期skillでは失敗率として現れる。** 意図した挙動(欠陥を表面化させる)だが、skillの成熟前は運用ノイズになりうる
- **コスト参考値はbackend間で比較できない。** ClaudeはUSDを返しCodexは返さない。横断比較はtoken数で行う必要があり、tokenの意味もmodel間で厳密には揃わない
- **injection防御は構造による緩和であって検出ではない。** 入力汚染そのものは通過する。gate較正の初期段階では人間レビューが最後の防波堤である
- **`model_call` event typeの追加はTrace Storeの契約変更である。** Phase 0のREADMEに書かれた保存対象の記述をT-027で更新する必要がある
- **portable schema profileが未確定である。** 初期案は保守的に置くが、実際に使えるkeywordはT-027のcapability testまで確定しない。skill出力契約の表現力に制約が出る可能性がある

### North Star §22との差分

§22の `LLM provider` 行は `OpenAI / Anthropic / Azure / Gemini / local via adapter` であり、adapter越しの複数provider対応を想定している。本ADRはその想定に沿い、adapter境界(`LLMClient`)を立てたうえで、実体としてサブスクリプション契約下のCLIを選ぶ。

| 領域 | §22推奨 | Phase 1決定 | 差分理由 |
|---|---|---|---|
| LLM provider | OpenAI / Anthropic / Azure / Gemini / local via adapter | Claude Code CLI + Codex CLI(headless)を `LLMClient` 実装として持つ | オーナーの契約がサブスクリプション範囲であり、従量課金APIの契約を持たない。adapter境界は§22の想定どおり維持する |
| Secret管理 | Vault / cloud secret manager | **veridiaは秘密情報を扱わない。** 認証はCLIの資格情報ストアに委ねる | 扱う秘密がないため、secret manager導入の対象そのものが存在しない。API直結へ移行した時点で再検討する |
| Agent runtime | OpenAI Agents SDK相当、または自社orchestrator | agent runtimeを導入しない(1 skill = 1推論)。CLIのagent機能は無害化して使う | T-027備考のとおり過剰設計にしない。workflow orchestrationはT-056で最小限を別途扱う |

### Phase 2以降の移行条件

- **API直結へ移行**: 従量課金APIの契約を取得する、レート制限が恒常的な制約になる、harness overheadが無視できないコストになる、CLIバージョン追随の負担が実装追加の負担を上回る、CLI側のセッション永続化・provider retentionが受容できなくなる。**この移行には本ADRのamendまたはsupersedeを必須とする。** 単なるadapter追加ではなく、契約・認証境界・retention・コスト値の意味・CI利用条件が同時に変わるためである
- **model割当の変更(ADR不要)**: skillごとのprecision実績とコスト差が観測され、実際に異なる割当が必要になった時点で、skill manifestのoverrideまたはpolicy側の既定変更で行う。tier抽象の導入もこの時点で判断する
- **provider追加(新ADR)**: Claude / Codex以外のmodelが必要になる、対象プロダクトの制約でself-hosted modelが要る
- **agentic skillの必要(新ADR)**: 決定的コードでは賄えないtool利用がskillに必要になる。この時点でLLMのtool呼び出しをTool Gateway経由に接続する設計を決める(§5.6のguardrail / approval / rate limitがPhase 1では未実装であることに注意)
- **再現性(新ADR)**: 監査要件でデータ部本文の保存が要求される。§15.4との整合をredaction pipelineと汎用Artifact Storeの設計込みで決める

移行時も、`LLMClient` Protocol、artifact組み立ての責務分担、trace recordのfield契約は維持し、差し替える主対象は `LLMClient` の実装に局所化する。

### 依存パッケージ

**追加依存なし。** CLI呼び出しはPython標準ライブラリ(`subprocess` / `json` / `hashlib` / `pathlib` / `tempfile`)で実装できる。provider SDK、provider抽象layer、prompt template engine、tokenizerのいずれもPhase 1では追加しない。

token数はCLIの出力から取得し、クライアント側で推定しない(`tiktoken` 等はClaude / Codexいずれのtokenizerでもないため使わない)。

**リポジトリ外の前提。** 実行には次が必要である。T-027のREADMEに前提として記載する。

- `claude`(Claude Code CLI)がallowlist記載のバージョンで導入済みで、サブスクリプション認証が済んでいること(検証済み: 2.1.207)
- `codex`(codex-cli)がallowlist記載のバージョンで導入済みで、認証が済んでいること(検証済み: 0.145.0)
- CIでは実LLMを呼ばないため、これらはCIの前提に含めない
