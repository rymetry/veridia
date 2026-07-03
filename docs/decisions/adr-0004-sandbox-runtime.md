# ADR-0004: Sandbox runtimeのPhase 0実現方式

- status: accepted
- date: 2026-07-03

## Context

Phase 0 WS-D(`sandbox`)の着手前に、North Star §5.7(Execution Sandbox)と§22(`Sandbox = container / ephemeral env`)を、T-018〜T-020で実装可能な方式へ具体化する必要がある。

Phase 0で満たすべき直接の完了条件は、計画§2の「sandboxで同じtestを2回実行し、同一結果になる」である。T-018〜T-020では、sandbox環境の作成・破棄・reset、fixture seed、deterministic clock、test runner実行、ExecutionEvidence保存を最小実装する。

判断軸はADR-0003と同じく、次の通りとする:

- セットアップ最短: `uv sync --group dev` 後、追加サービスやdaemonなしで統合テストを実行できる
- オフライン動作: network access、cloud credential、Docker daemonに依存しない
- テスト容易性: pytestの一時ディレクトリでsandbox全体を作成・破棄・resetできる
- 将来移行性: Phase 1以降にcontainer runtime / stronger isolationへ寄せられる境界を残す
- Phase 0最小性: 計画§6に従い、§5.7の全要件ではなく完了条件を満たす範囲に留める

重要な制約として、Phase 0の実装担当環境(Codex CLI)ではネットワークが遮断され、Docker daemonへのアクセスも保証されない。CIはGitHub Actionsであり、T-018〜T-020の検証は `uv run pytest` 単体でオフライン実行できる方式が望ましい。

この決定に直接依存する後続タスク:

- T-018: sandbox environmentの新規作成・破棄・reset、2回連続作成/resetの初期状態hash一致
- T-019: fixture seed、reset後の再seed同一性、sandbox内の固定時刻
- T-020: sandbox内test実行、ExecutionEvidence保存、同一test 2回実行の結果一致

## Options

| 候補 | 内容 | 長所 | 短所 |
|---|---|---|---|
| A. Docker等のcontainer runtime | Docker / container imageをsandbox単位で起動し、filesystem・process・networkをcontainer境界で分離する | §22の「container」に最も近い。network egress control、resource limit、secret mount制御、tenant isolationへ拡張しやすい | Docker daemon、image build/pull、port/network設定が必要。Codex CLI環境とCIで利用可能性が安定しない。Phase 0のDoDに対してセットアップが重い |
| B. OS process + temporary directory based ephemeral env | Python標準ライブラリで一時ディレクトリを作成し、subprocessの `cwd` と環境変数をsandbox用に固定する。resetは削除後の再作成で実現する | 追加依存なし。オフラインで `uv run pytest` 単体検証できる。pytest `tmp_path` で作成・破棄・hash比較しやすい | kernel/containerレベルの隔離ではない。network egress control、resource limit、tenant isolation、任意プロセスの時刻偽装は担保しない |
| C. 段階導入(process + temp dirを抽象境界にし、Phase 1以降でcontainer adapter追加) | Phase 0はBで実装し、sandbox lifecycle / runner / clock / seedのinterfaceをcontainer移行可能に保つ | Phase 0の検証容易性と将来container移行性を両立できる。Dockerが使える環境でも、まずDoDをローカルで安定検証できる | Phase 0時点ではAの安全性は得られない。interface境界を過剰設計しない注意が必要 |

## Decision

Phase 0では **C. 段階導入** を採用する。実体としては **OS process + temporary directory based ephemeral env** を実装し、container runtimeは導入しない。ADR承認後のT-018〜T-020実装は、追加依存なし(Python標準ライブラリの `tempfile` / `pathlib` / `shutil` / `subprocess` / `hashlib` / `json` / `datetime` 等)で進める。

Dockerがローカルで利用可能な場合でも、Phase 0ではDockerを本線にしない。理由は、T-018〜T-020のDoDが「同一初期状態・seed同一性・時刻固定・runner結果の決定性」の検証であり、container daemonを必要としないうえ、Codex CLIやCIでdaemon可用性に依存するとPhase 0の検証経路が不安定になるためである。Docker / container runtimeは、下記の移行条件を満たした時点で新ADRまたは本ADRのsupersedeにより採用する。

### 1. Sandbox runtime構成

Phase 0のsandboxは、次の境界を持つ軽量runtimeとする:

- sandbox root: runごとの一時ディレクトリ
  - 通常実行のdefault rootは `.veridia/sandbox/runs/` 配下に作成してよい
  - pytestでは `tmp_path` 配下に作成し、テスト終了時に破棄する
- execution boundary: OS subprocess
  - runnerはsandbox rootを `cwd` にして、allowlistされたコマンドだけを実行する
  - shell展開に依存しない引数配列実行を基本にする
  - child processにはsandbox用に構築した環境変数のみを渡す
- state boundary: sandbox root配下のファイルツリー
  - state hashは、相対path、file type、file contentを正規化して計算する
  - absolute path、mtime、inode、permissionのような環境差・実行差が出やすい値はPhase 0のhash対象に含めない

このruntimeは安全境界ではなく、決定性検証のための実行境界である。任意コードを敵対的に隔離する目的には使わない。

### 2. 環境reset方式

Phase 0のresetは **削除後の再作成(recreate from deterministic manifest)** とする。overlay filesystemやsnapshot機能は使わない。

T-018で実装する最小操作:

- `create`: sandbox rootを新規作成し、固定の初期ディレクトリ構造とmanifestを配置する
- `destroy`: sandbox rootを再帰削除する
- `reset`: 既存sandbox rootを削除し、同じ定義から再作成する
- `state_hash`: sandbox root配下を相対path順に走査し、正規化した状態hashを返す

初期状態の定義はコード上の固定値または小さなmanifest fileに留める。T-019のfixture seedはreset後に再投入できる別層として扱い、T-018の初期状態hashとT-019のseed後状態hashを分けて検証する。

この方式でT-018のDoDは実装可能である。2回連続で `create -> state_hash -> destroy`、または `reset -> state_hash -> reset -> state_hash` を実行し、同じ初期状態hashになることをpytestで確認できる。

### 3. Deterministic clockの実現手段

Phase 0では **環境変数 + clock抽象の注入** を採用する。`libfaketime` やOS-level time namespaceは導入しない。

最小仕様:

- 固定時刻はISO 8601 UTC文字列として `VERIDIA_FIXED_NOW` に設定する
- sandbox runnerはchild processへ `VERIDIA_FIXED_NOW` を渡す
- veridia側の実装とPhase 0のsample testは、直接 `datetime.now()` を呼ばず、clock helper / clock abstraction経由で現在時刻を取得する
- clock helperは `VERIDIA_FIXED_NOW` がある場合はその値を返し、ない場合だけ実時刻を返す
- ExecutionEvidenceやstate hashで時刻が必要な場合も、同じclock helperを使う

この方式でT-019のDoDは実装可能である。sandbox内で同じsample commandまたはsample testを2回実行し、どちらも `VERIDIA_FIXED_NOW` に由来する同一時刻を返すことをpytestで確認する。

`libfaketime` は、既存テストや対象プロダクトが直接OS clock / language runtime clockを読む場合に有効だが、Phase 0では追加依存・動的ライブラリ注入・OS差分の負担がDoDに対して重い。Phase 0の対象はveridia自身のsample runnerであり、clock abstractionを守る方が小さい。

### 4. Phase 0で実装する§5.7範囲

| §5.7要件 | Phase 0扱い | 実現方法 / 理由 |
|---|---|---|
| Ephemeral env | 実装する | trialごとのsandbox root作成、destroy、reset |
| Deterministic clock | 実装する | `VERIDIA_FIXED_NOW` + clock abstraction |
| Seeded fixtures | 実装する | T-019でseed定義をsandbox rootへ投入し、reset後の同一性をhash比較 |
| Snapshot / rollback | 最小実装する | 汎用snapshotではなく、reset(recreate)とstate hashで代替 |
| No production write | 最小担保する | Phase 0はsynthetic fixture + tmpdirのみを対象にし、production credentialや本番pathを渡さない |
| Mock external services | スコープ外 | Phase 0のsample runnerは外部serviceを使わない。Phase 1以降のpilot integrationで再検討 |
| Network egress control | スコープ外 | process + tmpdirでは強制できない。container / firewall / proxy導入時に扱う |
| Secrets isolation | 最小担保のみ | child processへ渡すenvを明示構築し、secretを渡さない。強制隔離はPhase 1以降 |
| Tenant isolation | スコープ外 | Phase 0は単一開発環境・synthetic fixtureのみ |
| Resource limit | スコープ外 | timeout程度はrunnerで扱ってよいが、CPU/memory hard limitはcontainer等へ移行後 |
| Performance sandbox | スコープ外 | Phase 4以降 |

### 5. T-018〜T-020との整合

- T-018: temporary directory sandboxは、作成・破棄・resetをPython標準ライブラリだけで実装できる。状態hashを相対path + contentで計算すれば、2回連続作成/resetの同一初期状態をオフラインpytestで検証できる。
- T-019: fixture seedをreset後に投入し、seed後のstate hashを比較できる。clockは `VERIDIA_FIXED_NOW` をrunner envに注入し、clock helper経由で2回とも同一時刻を返せる。
- T-020: runnerはsandbox rootを `cwd` にしてsample testを2回実行し、結果とstate diffを比較できる。ExecutionEvidence保存はADR-0003のEvidence Store境界に接続し、run_id / trace_id付きで保存・読み出しできる。

## Consequences

### 良い影響

- Phase 0の個人開発・CIでDocker daemon、network access、追加serviceなしにT-018〜T-020を検証できる
- sandbox全体をpytest一時ディレクトリに閉じ込められるため、作成・破棄・resetのテストが単純になる
- deterministic clockを環境変数と抽象で扱うため、OS差分のある時刻偽装ライブラリを導入せずに決定性を検証できる
- lifecycle / runner / seed / clockの境界を残すことで、Phase 1以降にcontainer adapterへ移行しやすい

### トレードオフ

- Phase 0 runtimeはsecurity sandboxではない。敵対的コード、任意外部通信、resource abuse、tenant越境を防ぐものではない
- 対象コードがclock abstractionを経由せず直接OS時刻を読む場合、Phase 0方式では時刻固定を強制できない
- network egress control、secret isolationの強制、CPU/memory hard limitは後続ADRまで未解決として残る
- container imageのbuild reproducibilityやOS package差分はPhase 0では検証しない

### North Star §22との差分

このADRは§22の「container / ephemeral env」のうち、Phase 0ではephemeral env側を採用する。containerを否定せず、Phase 0の検証容易性を優先して段階導入にする。

| 領域 | §22推奨 | Phase 0決定 | 差分理由 |
|---|---|---|---|
| Sandbox | container / ephemeral env | process + temporary directory based ephemeral env | Docker daemon可用性に依存せず、`uv run pytest` 単体で決定性を検証するため |
| Clock | 明示なし(§5.7でdeterministic clock要求) | `VERIDIA_FIXED_NOW` + clock abstraction | Phase 0のsample runnerには追加依存なしで十分。OS-level clock偽装は後続 |
| Reset | 明示なし(§5.7でephemeral env / snapshot要求) | delete + recreate + state hash | snapshot基盤なしでT-018/T-019のDoDを満たすため |

### Phase 1以降の移行条件

以下のいずれかが成立したら、本ADRをsupersedeしてcontainer runtimeまたはより強いsandbox基盤を採用する:

- 任意の対象repo/testを実行し、敵対的または未知のコードを隔離する必要が出る
- network egress control、secret isolation、tenant isolationを機械的に強制する必要が出る
- CPU/memory/runtimeのhard limitをrunner外で強制する必要が出る
- 対象プロダクトがclock abstractionを守れず、OS-level clock偽装が必要になる
- CI / 開発環境でDocker daemonまたは代替container runtimeの利用が安定し、container imageのbuild/pullもオフラインまたはcache済みで再現できる

移行時も、T-018〜T-020の利用側APIは維持し、差し替える主対象はsandbox lifecycle adapter、runner adapter、clock provider、state snapshot/hash providerに局所化する。

### 依存パッケージ

Phase 0のT-018〜T-020実装に追加依存は不要。`libfaketime`、Docker SDK、container runtime wrapper等は採用しない。Phase 1以降でcontainer runtimeやOS-level clock偽装を採用するADRを起票・承認する場合のみ、監督者が `uv add` 等を代行して依存を追加する。
