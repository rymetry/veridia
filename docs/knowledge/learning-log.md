# Learning Log

記法は [`README.md`](README.md) 参照。新しいエントリを上に追加する。

---

## 2026-08-02 [process-learning] 契約が既に強制している条件をgateにすると、そのgateは一生発火しない(T-057)

- 事実(何を観測したか): §17.1のsource grounding gateを最初のgateに選んだ理由は「現状の材料で唯一評価できるから」だった。実装直前に気づいたのは、判定材料である `RunRecord.source_refs` に **schema側が既に `minItems: 1` を課している**ことである。さらに `SkillRunner.run()` も空の `source_refs` を入口で拒否する。つまり正常経路を通ったrecordに対しては、このgateは定義上100%passする。テストは全部緑になり、カバレッジも100%になり、gateは何も守っていない。
- 学び(なぜ・何を変えるべきか): **gateの実装は「何を判定するか」ではなく「どの経路で来たpayloadを判定するか」で意味が決まる。** contract検証を通った後のpayloadだけを見るgateは、contractの再実行にすぎない。gateが価値を持つのは、contractが通していない経路 — 手書きのrecord、将来の別producer、直接編集されたfile、versionの違う過去record — から来たpayloadに対してである。したがってgate ruleは入力を検証済みobjectとして扱わず、生のMappingとして受け取り、型・存在・空判定を自分で行う。「防御コードは正常系テストでは一生発火しない」(2026-07-03)の変種だが、こちらは**テストの書き方ではなく実装の置き場所の問題**であり、テストを足しても直らない。
- アクション(変更したもの・リンク): `gate_evaluator/rules.py` のruleは `Mapping[str, Any]` を受け取り、key欠落・非list・空白のみのstringをすべてfailにする。regression guard: `tests/test_gate_evaluator.py::TestSourceGroundingGate`(4種のungrounded payloadでblockすることを実証)。加えて実装へ意図的に6件の欠陥を入れて全件がテストで検出されることを確認した(mutation check)。記録: [T-057](../tasks/phase-1/T-057-gate-decision-source-grounding.md)。

## 2026-08-02 [process-learning] 未実装gateを「安全側」でblockにすると、初日に全runが止まってgateが形骸化する(T-057)

- 事実(何を観測したか): 17 gate中16に評価器が無い状態でgate評価器を作った。未評価gateの扱いとして最初に検討したのは「block stageのgateが判定できないならblockする」だった。これはfail-safeに見えるが、実際には`oracle` / `evidence` / `security` の3つがblock stageで未実装であるため、**すべてのrunが無条件でblockされる**。§17.0が「false blockは1回で10回分の信頼を毀損する」「override常態化でgateは形骸化する」と書いている状態そのものである。
- 学び(なぜ・何を変えるべきか): 「判定できない」に対する安全な既定値は文脈で反転する。**runtimeの権限判定では deny が安全側だが、開発プロセスのgateでは block は安全側ではない** — 止まったチームはgateを迂回する手段を制度化し、gateは以後どの違反も止められなくなる。3値(`pass` / `fail` / `inconclusive`)を用意し、inconclusiveは「passにはしないがblockもしない = warnへ落として可視化する」に割り当てるのが、精度が立証されるまでの正しい既定値である。ただしこれは「黙ってpassにする」と紙一重なので、(a) 全gateの判定をrecordへ列挙する、(b) 理由を必須にする、(c) 現在のpolicyではpassが出得ないことをテストで固定する、の3点で可視性を担保する。
- アクション(変更したもの・リンク): `gate_evaluator/results.py::aggregate` がstage別に集約し、block stageのinconclusiveはwarnへ落とす。`schemas/gate-decision.schema.json` の `gateResult.reason` は全outcomeで必須。regression guard: `tests/test_gate_evaluator.py::TestStageDrivesTheDecision::test_todays_real_policy_cannot_yield_pass`(gate実装が進むとこのテストが落ちて状況の変化を知らせる)。記録: [T-057](../tasks/phase-1/T-057-gate-decision-source-grounding.md)。
## 2026-08-02 [process-learning] 上流へのフィードバックループが1周した — pinテストは「削除条件を書いておくと自分で落ちて知らせる」

- 事実(何を観測したか): veridiaの境界検証が検出したsqk-coreの不整合(envelope内包payloadが `schema_ref` に対して未検証)を [Issue #48](https://github.com/rymetry/sqk-core/issues/48) として起票したところ、上流は PR #49 / #50 で解決した。**fixtureの修正だけでなく、提案どおり `scripts/check.py` に envelope 検証(CHECK6)が追加**され、再発が構造的に防がれた。veridia側でSHAを `54e78cc` → `01f104d` へ付け替えたところ、壊れた挙動をpinしていた `test_envelope_payload_gap_in_sqk_core_fixture` が `DID NOT RAISE` で落ちた。skill frontmatterの `version` は16本すべて据え置き、schemaの契約変更も無し(差分はfixtureとREADMEのみ)だったため、取り込みは非破壊だった。
- 学び(なぜ・何を変えるべきか): 上流の未修正事項をpinするテストには、**docstringに削除条件を書いておくと、条件が満たされた瞬間にテスト自身が失敗して知らせてくれる**。「上流が直ったか」を人間が定期的に確認する必要がない。これはTODOコメントとの決定的な違いで、TODOは腐るがpinテストは腐ると落ちる。あわせて、分離リポジトリ構成の価値がここで実証された — 修正が上流の検証ハーネスに入ったため、veridia以外の3プラットフォーム(claude-code / gpts / codex)にも同じ防御が届いた。veridia側で直していたら1リポジトリ分の修正で終わっていた。
- アクション(変更したもの・リンク): submodule SHAを `01f104d788d2423a85e514483edbf2983dc7b553` へ更新([統合方針 §4](../plan/sqk-core-integration.md) の手順1〜4を実行。上流 `scripts/check.py` はCHECK1〜6すべてissues=0)。pinテストを削除し、合成で迂回していたhappy pathを上流のvalid fixture原本を使う形へ戻した(`test_upstream_valid_envelope_fixture_passes`)。

## 2026-08-02 [process-learning] CLIが拘束できない制約はpromptで伝えないと、呼び出しコストだけ払って破棄される(T-027実LLM実測)

- 事実(何を観測したか): T-027でsqk-core skillを実LLM(`claude -p`)で初めて実行した。ADR-0005 Decision 6.1に従いCLIへ渡す出力schemaはportable profile(`type`/`properties`/`required`/`enum`/`items`/`additionalProperties`)に限り、`pattern` は `artifact_validator` 側で強制する設計にしていた。結果、`test-architecture-design` はcold start時にDTCをグループ分けした `DTC-A01` / `DTC-B02` 形式のIDを合成し、sqk-coreの `^DTC-[0-9]+$` に18件弾かれてrecordは保存されなかった。**契約検証は正しく働いたが、モデルは自分が何で検証されるかを知らないまま出力していた。** 制約をschemaから導出してprompt指示部へ載せる `contract_note` を追加したところ、次の実行はTAE 8件を正しい形式で生成し検証を通過した。
- 学び(なぜ・何を変えるべきか): 「CLI側で拘束できない制約はvalidator側で強制する」は正しいが、それだけでは**検証は通るが実行が通らない**。強制する場所と、モデルに伝える場所は別に必要である。かつ伝える内容はschemaから導出する — 手書きでpromptに書くと、schemaが変わったときに黙って乖離する(North Star変更ルール2の複製回避と同じ理由)。portable profileを採る設計では、profile外の制約すべてについて「validatorで強制する」と「promptで伝える」の両方を配線する。
- アクション(変更したもの・リンク): `skill_runner/contract_note.py` を追加し、宣言された出力schemaから `pattern` を走査して指示部へ載せる。regression guard: `tests/test_skill_runner.py::TestContractNote`(schemaからの導出・制約が無い場合は空・指示部にのみ載りデータ部には混ざらない)。記録: [T-027](../tasks/phase-1/T-027-skill-runner-minimal.md)。

## 2026-08-02 [process-learning] CLIの隔離フラグはトークン消費を1/15にする(ADR-0005 Decision 5の効果実測)

- 事実(何を観測したか): ADR-0005起票時の実測では、`claude -p` に「OKと返せ」だけを渡してもcache_creation 35,447 tokensが積まれていた(CLI既定のsystem prompt・tool定義・環境情報・プロジェクト文脈が乗るため)。T-027でDecision 5の隔離フラグ(`--safe-mode` / `--setting-sources ""` / `--disable-slash-commands` / `--strict-mcp-config` / `--tools ""` / `--no-session-persistence`)を全て明示し、cwdをリポジトリ外の一時ディレクトリにした状態で同等の試行を行ったところ **2,361 tokens** になった。約1/15。
- 学び(なぜ・何を変えるべきか): 隔離要件は再現性・§15.4・§16.4のために課したものだが、**コスト面でも支配的な効果を持つ**。「hermetic化は望ましいではなく必須」というADR-0005の結論は、安全性だけでなく経済性からも裏付けられた。一方でこれは、隔離フラグが1つでも外れると静かにコストと汚染が戻ることも意味する。フラグの存在をargvレベルのテストで固定する価値がある(防御コードは正常系テストでは発火しない — 2026-07-03のエントリ)。
- アクション(変更したもの・リンク): `tests/test_skill_runner.py::TestIsolationArgv` で6フラグと `--bare` 不使用・model明示をargv単位で固定した。実測値は [skill_runner/README.md](../../skill_runner/README.md) に記載。

## 2026-08-02 [northstar-proposal] ArtifactBaseの `confidence` 必須は最初の非artifact producerで破綻した(RunRecordは継承を見送り)

- 事実(何を観測したか): ADR-0007の監査ラッパー `RunRecord` を定義する際、`artifact-base.schema.json` を `allOf` で継承すると必須10fieldがすべて掛かる。うち `confidence`(number / 0.0〜1.0 / required)はskill実行1回の記録に対応する値を持たない。埋めるとすれば 1.0 等の任意の定数になり、これは値の捏造にあたる。`created_by.skill` も sqk-core envelope の `source_skill` と二重管理になる。残る8fieldは意味を持った(`source_refs` は「何に対して実行したか」、`status` は人間レビューの到達点として実用的)。
- 学び(なぜ・何を変えるべきか): これは 2026-07-02のエントリ「出力契約schemaの必須度は最初のproducerのPhase能力と突き合わせて決める」(T-006でPhase 0 generatorにrefの捏造を迫る契約になった件)と同じ罠が、base schema 側で再発したものである。§6.1 の共通契約は「agent/skillの成果物(artifact)」を想定して設計されており、**artifactを運ぶ入れ物(run / envelope / decision record)には合わない**。ArtifactBaseの必須10を減らす判断材料が1件出たが、既存9 schemaへの波及があるため本エントリでは変更しない。**producer証拠が2件目まで出た段階で §6.1 の必須fieldの見直しを起票する**(特に `confidence` は schema 自身が「較正されていない、gate入力にするな」と注記しており、必須である根拠が弱い)。
- アクション(変更したもの・リンク): `RunRecord` はArtifactBaseを継承せず、`artifact_type` のconstのみ持つ設計とした(artifact_validatorのルーティングは `artifact_type` だけで成立するため検証経路は1本のまま)。例外の条件と理由を [schemas/README.md](../../schemas/README.md) のルールへ明記。非継承であること自体を `tests/test_run_record_schema.py::TestSchemaItself::test_does_not_inherit_artifact_base` / `test_does_not_require_confidence` で固定した。North Star §6.1 の改訂は未実施(変更ルール1)。

## 2026-08-02 [northstar-proposal] North Star §6 は「veridiaが定義する契約の一覧」ではなく「必要な契約の一覧」に改める必要がある

- 事実(何を観測したか): §6 の27契約(§6.2〜6.27)に**テスト設計系の成果物が1つも含まれていない**ことを確認した。§4.3 は W9 → `TestArchitectureSpec`、W12 → `TestDesignSpec` / `TestAsset` を出力すると定め、§7.3 のskill表も同じ出力を宣言しているのに、§6 に契約定義が無い。結果として [phase-1計画 §4](../plan/phase-1-crud-mvp.md) は W9 を「独立ステップとしては実装しない」と省略していた。一方 sqk-core は同じ工程を ISO/IEC/IEEE 29119-2 / JSTQB v4.0 接地の11工程モデルとして正典化しており、該当契約(`test-architecture-element` / `condition-assignment-matrix` / `test-case` / `coverage-item` 等)をschema + fixture付きで保有していた。さらに sqk-core 側の文書は「TAD を入れないと、agent が分析結果から突然テストケースを生成する動きになりやすい」とアンチパターンとして明示しており、phase-1計画のW9省略はこれに該当していた。
- 学び(なぜ・何を変えるべきか): §6 が「veridiaが全契約を定義する」前提で書かれているため、外部正典が既に持っている契約まで自前定義の対象に見え、未定義18件が停滞の要因になっていた。契約は「必要かどうか」と「誰が正本を持つか」を分けて扱うべきで、正本がsqk-coreにあるものはveridiaで再定義しない。ただし**変更ルール1に従い、North Star本文は本エントリでは改訂しない**。Phase 1 の実運用(工程4→5→6を実際に通すこと)を経てから改訂を判断する。
- アクション(変更したもの・リンク): [ADR-0007](../decisions/adr-0007-sqk-core-contract-consumption.md) を採択し、テストプロセス成果物の契約は sqk-core を正本として直接消費すると決定(veridiaが定義する契約は27→4)。実装は [artifact_validator/sqk_schema_store.py](../../artifact_validator/sqk_schema_store.py) / [sqk_validator.py](../../artifact_validator/sqk_validator.py)。regression guard: `tests/test_sqk_schema_validation.py`(sqk-coreの全18契約×valid/invalid fixture 36件)。North Star改訂は未承認のため未実施。

## 2026-08-02 [process-learning] スキルにTADを実施させると、直後に書いた自分のコードのテスト空白が出る(全緑・カバレッジ97%を通り抜けていた2件)

- 事実(何を観測したか): sqk-core の `test-architecture-design` スキルを、その1時間前に自分で実装した機能(sqk-core契約の境界検証)に対して実行した。出力は4つのTAE(schema解決の防御 / envelope・payload二層検証 / 契約網羅回帰 / エラー位置精度)と10件のDTC割当で、`gate_status: passed-with-risks`。リスク→厚みの変換根拠(§4.2のリスクレベル別ポリシー)が各TAEの `rationale` に付いていた。この出力が指摘した未検証項目2件は実在した — (1) 複数 artifact × 複数 item での エラーJSONPath の精度(既存テストは `artifacts[0].items[0]` のみ)、(2) envelope構造が壊れている場合にpayload検証をスキップする挙動(実装済み・テスト無し)。いずれも 82テスト全緑・カバレッジ97% を通り抜けていた。テストを追加したところ**2件とも即passした**(バグではなく検証欠落)。
- 学び(なぜ・何を変えるべきか): 2026-07-03のエントリ「全緑テスト+80%超カバレッジでも実行時異常系・セキュリティ境界のテスト空白は残る」と同じ構造が、規模の小さい新規実装(214行)でも再現した。カバレッジは「その行を通ったか」しか見ないため、**分岐の組合せ(artifact index × item index)と早期returnの副作用(検証しないこと)は測れない**。TADを工程として挟むと、テストを「書いた順」ではなく「構造の切り口」から数え直すことになり、この種の空白が可視化される。テスト生成の前にTADを置く理由は網羅率ではなく、この数え直しにある。
- アクション(変更したもの・リンク): 指摘2件に対応するテストを追加(`test_paths_stay_precise_across_multiple_artifacts_and_items` / `test_broken_envelope_skips_payload_validation`)。TAD出力そのものは [artifact_validator の validate_handoff_envelope](../../artifact_validator/sqk_validator.py) で検証してVALIDを確認済み(知識→分析→契約準拠成果物→検証のループが初めて一周した)。

## 2026-08-02 [process-learning] sqk-core の検証ハーネスは envelope 内包payloadを schema_ref に対して検証していない(上流起票案件)

- 事実(何を観測したか): veridia側で `handoff-envelope` の内包artifactを `artifacts[].schema_ref` に対して検証する実装を入れた直後、sqk-core の**valid fixture** `schemas/tests/fixtures/handoff-envelope/valid/risk-analysis-handoff.json` が落ちた。内包する RiskItem が `{id, statement}` の2fieldしか持たず、`risk-item.schema.json` が要求する `category` / `likelihood` / `impact` / `treatment` を欠いていた。原因を追うと、sqk-core の `scripts/validate-schemas.sh` は各fixtureを**自分のschemaに対してのみ**検証しており、`handoff-envelope.artifacts[].items` が制約なしのarrayであるため、内包payloadは宣言した `schema_ref` に対して一度も検証されない構造だった。
- 学び(なぜ・何を変えるべきか): envelope方式は「transport構造」と「payload契約」の2層になるが、片方だけを検証するハーネスでは層の継ぎ目が無検査になる。これはveridia固有の問題ではなく、envelopeを受け取る全consumer(claude-code / gpts / codex / veridia)が同じ穴を踏む。したがって**修正はveridia側ではなくsqk-coreの検証ハーネスに入れるべき**で、veridia側の境界検証は二重防御として残す。分離リポジトリ構成の価値はここに出る(マージしていればveridia1件の修正で終わり、他3プラットフォームには届かない)。
- アクション(変更したもの・リンク): 事実を `tests/test_sqk_schema_validation.py::TestHandoffEnvelope::test_envelope_payload_gap_in_sqk_core_fixture` に固定(docstringにSHA更新後の削除条件を明記)。sqk-coreへ [Issue #48](https://github.com/rymetry/sqk-core/issues/48) を起票([統合方針 §5](../plan/sqk-core-integration.md) の経路。フィードバックループの初回稼働)。
## 2026-08-02 [process-learning] サブスクCLIを推論backendにすると、CLI自身がpromptを平文永続化する(§15.4はveridiaのstoreに閉じた制約ではない)

- 事実(何を観測したか): [ADR-0005](../decisions/adr-0005-llm-skill-execution.md) の検討で、`claude -p` / `codex exec` をLLM skillの実行経路として実測した際、プローブで送ったprompt本文が `~/.claude/projects/<...>/<session-id>.jsonl` と `~/.codex/sessions/<date>/rollout-<...>.jsonl` に**平文で残っている**ことをgrepで確認した。ADRのdraftは「veridiaのTrace Storeにprompt本文を保存しない」ことで§15.4を満たすと書いていたが、保存しているのはCLI側であり、この設計では対象プロダクトのPR diff・コードがveridiaの管理外のディスクに残る。対策として `claude --no-session-persistence` / `codex exec --ephemeral` が存在する。
- 学び(なぜ・何を変えるべきか): §15.4「保存しないもの」は**保存先を問わない制約**であり、自プロダクトのstoreの保存方針だけでは満たせない。外部プロセス(CLI・SDK・proxy)を実行経路に挟む場合は、そのプロセスが何を永続化するかを**実際にディスクを見て確認する**。ドキュメントやフラグ一覧を読むだけでは、既定で有効な永続化を見落とす。加えて、provider側のretentionは制御外であり、これは緩和ではなく残存リスクとして記録するしかない。
- アクション(変更したもの・リンク): ADR-0005 Decision 5.5でセッション永続化の抑止を必須要件化し、抑止が効いていることをcapability probeで検証する契約にした。provider側retentionはConsequencesの残存リスクとして明記。

## 2026-08-02 [process-learning] CLIはcwdの祖先方向へ指示ファイルを探索する — 「空ディレクトリ」は隔離条件ではない

- 事実(何を観測したか): ADR-0005 draftは「LLM実行用のcwdを専用の空ディレクトリに固定すれば、対象プロダクトの `AGENTS.md` が指示として流入する経路を構造的に閉じられる」とし、あわせて「[ADR-0004](../decisions/adr-0004-sandbox-runtime.md) のsandbox一時ディレクトリと同じ扱いでよい」と書いていた。しかしCLIの `CLAUDE.md` / `AGENTS.md` 探索は**cwdから祖先方向へ遡る**ため、空であることと指示ファイルを持つ祖先の外にあることは別条件である。ADR-0004の通常rootは `.veridia/sandbox/runs/`(veridia repo内)であり、そこをcwdにすると親のveridia `AGENTS.md` が探索対象になる。さらに `~/.codex/AGENTS.md` が実在し(検証時点で0バイト)、`--ignore-user-config` が除外すると明記しているのは `config.toml` だけだった。
- 学び(なぜ・何を変えるべきか): エージェントCLIを実行経路に使う場合、隔離条件は「cwdが空であること」ではなく「**指示ファイルを持つ祖先の外にあること**」である。対象プロダクトのrepoをcwdにすると、そのrepoの `AGENTS.md` は「信頼できないソースが書いた指示」そのものになり、§16.4のprompt injection経路として直接効く。API直結には存在しないCLI固有の経路であり、実行経路を変えたら防御面も洗い直す必要がある。既存ADRの成果物(sandbox root等)を「同じ扱いでよい」と流用する際は、その前提が新しい文脈でも成立するか確認する。
- アクション(変更したもの・リンク): ADR-0005 Decision 5.1で、cwdをveridia・対象repo・ユーザ設定ディレクトリの外に置くこと、祖先に指示ファイルとVCS rootが無いことを起動前に検証すること、**ADR-0004の既定rootを流用しないこと**を明記。グローバル指示ファイルの扱いはT-027の実測要件とした。

## 2026-08-02 [process-learning] 信頼ラベルをLLMに生成させるとtrust gateが自己申告で迂回できる(ラベルのauthorityはingestion層に置く)

- 事実(何を観測したか): ADR-0005 draftは、artifactのdomain固有fieldを一律「LLMが生成」とし、§16.4のtrust規則(untrusted / externalをリスク引き下げの根拠にしない)は「`source_refs` を解決してSourceMapの `trust_level` を照合する」ことで担保するとしていた。しかしSourceMap自体をLLM skillが生成する設計では、**入力汚染を受けたモデルが `trust_level: trusted` と出力するだけで照合を通過できる**。「決定的コードによる照合」に見えて、照合対象がモデルの自己申告だった。North Star §5.2はtrust label付与をingestion層の責務としている。
- 学び(なぜ・何を変えるべきか): セキュリティ判定に使うラベルは、**判定される側が生成してはならない**。LLM出力に対するgateを設計するとき、gateの入力がLLM出力の一部になっていないかを必ず確認する。ラベルのauthorityがどの層にあるかはNorth Star側で既に定義されていることが多く、実装側で暗黙に移してしまうと防御が形骸化する。同種の観点として、`status` / `requires_human_review` をrunnerが決定的に組み立てる設計は正しかったが、trust属性は見落としていた — 「モデルに触らせないfield」の列挙は、artifact共通契約だけでなくdomain固有fieldにも及ぶ。
- アクション(変更したもの・リンク): ADR-0005 Decision 6.3でsource identity / trust属性(`source_id` / `uri` / `source_version` / `trust_level`)をconnector決定的付与としてLLM生成対象から除外。Decision 10.5で照合に使う `trust_level` はconnector由来の値に限ると明記。Source Connector(T-026)への依存としてP-3に記録した。

## 2026-08-02 [process-learning] ADRのレビューは反復すると前回の修正が新たな矛盾を生む — 実測1件からの一般化にも注意する

- 事実(何を観測したか): ADR-0005をCodex(gpt-5.6-sol)で5回レビューした(判定は `request-changes` ×4 → `approve`、指摘は延べ blocker 6 / major 16 / minor 5)。2回目の指摘「失敗attemptのtraceが記録されず消費量を過少集計する」に対し、trace保存をCLI呼び出し直後へ移す修正を入れたところ、3回目に「`outcome`(success / retryable_error / terminal_error)は検証後にしか確定せず、Trace Storeはinsert-onlyなので後から更新できない」という**修正が作り込んだ新しい矛盾**を指摘された。別件では、`{answer: string}` という最小schema 1件の実測から「provider側はminLength / patternを非対応」と一般化しており、これも誤りとして指摘された。
- 学び(なぜ・何を変えるべきか): (1) 指摘対応は差分だけを見ず、**修正箇所の前後の整合を再確認する**。特に順序・状態遷移・不変条件に触る修正は、局所的には正しくても全体の契約を壊しやすい。(2) 実測は強い根拠だが、**測った範囲を超えて一般化しない**。1ケースの成功は他ケースの互換性を証明しない。断定する代わりに、検証範囲を明示して未検証部分はcapability probe等で実装時に確定する設計にする。(3) 外部レビューは「同意させる」のではなく「事実主張を検証させる」形で使うと有効に働いた。指摘のうち事実に関わるものは全てCLIの実挙動・既存コード・North Starで裏を取り、成立しないものは採用しない前提で進めた(今回は全て裏付けが取れた)。
- アクション(変更したもの・リンク): ADR-0005 Decision 7で保存位置を「検証・分類の後、retry判定の前」に修正し、artifact全体検証をattempt loop内へ移動。Decision 6.1でportable schema profileを保守的に定義し、keyword単位の実測拡張をT-027のcapability testに委ねた。

## 2026-08-01 [process-learning] 検証は作業ツリーではなくコミット済み内容に対して行う(git addの部分失敗を握り潰したcommitが検証を素通りした)

- 事実(何を観測したか): sqk-core統合の作業で、`git add <複数パス> 2>/dev/null` の引数に既にrename済みの旧ファイル名が混ざっており、git がpathspecエラーでコマンド全体を中断した。`2>/dev/null` でエラーが見えず、`git status --short` の出力も staged(1列目)と unstaged(2列目)を読み違えたため、気づかないままcommit・pushした。結果、commitにはrename(旧内容のまま)・submodule・symlinkしか入っておらず、文書本文の改訂と関連3ファイルの変更が欠落した。その後の検証(SHA記載の一致確認・リンク切れ確認・pytest)はすべて**作業ツリー**を読んでいたため全green となり、欠落を検出できなかった。PR の diff を見て初めて発覚した。
- 学び(なぜ・何を変えるべきか): (1) git コマンドの stderr を捨てない。特に `git add` は引数の一部が不正だと**何もstageせずに全体が失敗する**。(2) commit 前に `git diff --cached --stat` で意図した変更がstageされていることを確認し、`git diff --stat` が空であることも確認する(未staged残りの検出)。(3) commit後の検証は `git show HEAD:<path>` などコミット済み内容に対して行う。作業ツリーに対する検証は「これからcommitする内容」の確認にはなるが、「commitされた内容」の保証にはならない。(4) `git status --short` の2列(staged / unstaged)を機械的に読む習慣を持つ。
- アクション(変更したもの・リンク): 欠落分を追加commitで補填(履歴は書き換えず)。以降の検証はコミット済み内容と、submodule非取得のfresh cloneでのCI相当実行(ruff / format / pytest / `_index --check` / `gen_models --check`)で行った。PR [#2](https://github.com/rymetry/veridia/pull/2)。

## 2026-08-01 [process-learning] 外部正典をsubmodule+symlinkで取り込む際の運用上の落とし穴4点(sqk-core取り込み)

- 事実(何を観測したか): sqk-coreを `vendor/sqk-core` にsubmoduleとしてSHA固定し、`.claude/skills` からsymlinkで参照する配線([ADR-0006](../decisions/adr-0006-sqk-core-integration-method.md))で次を実測した。(1) **スキル名の衝突**: sqk-coreの `code-review` がClaude Code組み込みの `/code-review` コマンドや他プラグインの同名スキルと重なる。(2) **submodule未取得時**: `.claude/skills` はdangling symlinkになり、エラーを出さずスキルが1つも発見されない(silent failure)。(3) **lint/formatの巻き込み**: `ruff format --check .` が vendor 配下の外部原本を対象にして落ちる。`extend-exclude` への追加が必要。(4) **CIへの影響**: `actions/checkout` は既定でsubmoduleを取得しないが、vendorをlint対象外にし pytest が `testpaths` で閉じていれば、dangling symlinkがあってもCI全ステップはgreenのままだった(fresh cloneで実測)。
- 学び(なぜ・何を変えるべきか): 外部リポジトリをsymlinkで開発エージェントの発見パスに差し込む配線は、リポジトリの静的検査(lint/format)と名前空間の両方に副作用を持つ。取り込み時には「lint/format対象からの除外」「名前衝突の確認」「未取得時の挙動(失敗するのか黙るのか)」「CIが取得しない前提で成立するか」の4点を実測してから配線を確定する。特にdangling symlinkが無言で0件になる挙動は、セットアップ漏れが検知されないまま進む危険がある。
- アクション(変更したもの・リンク): 4点すべてを [統合方針 §3.1・§4](../plan/sqk-core-integration.md) に明記。`pyproject.toml` の ruff `extend-exclude` に `vendor` を追加。clone直後の `git submodule update --init --recursive` を [AGENTS.md](../../AGENTS.md) のコマンド表へ追加。

## 2026-08-01 [process-learning] ADR番号は未着手タスクが予約している場合がある(採番前にgrepする)

- 事実(何を観測したか): sqk-core連携方式のADRを `adr-0005-…` として作成したが、既存のADRファイルは0001〜0004しか無い一方、**未着手タスク T-025 が `adr-0005-llm-skill-execution.md` を予約**しており、T-025本文・T-027(3箇所)・T-052・`_index.md` から `ADR-0005` として参照されていた。`docs/decisions/` のファイル一覧だけを見て次番号を決めたため衝突した。
- 学び(なぜ・何を変えるべきか): このリポジトリはタスク分解の時点でADR番号を予約する運用になっている。ADR採番前に `docs/decisions/` のファイル名だけでなく、`grep -rn "ADR-00NN" docs/` でタスク・計画からの予約参照を確認する。既存の予約が先にある場合は、参照数の少ない側(=新規に書く自分のADR)を改番するほうが波及が小さい。
- アクション(変更したもの・リンク): 自分のADRを [ADR-0006](../decisions/adr-0006-sqk-core-integration-method.md) へ改番し、参照3箇所(統合方針・00-overview・AGENTS.md)を更新。T-025の予約は無変更。

## 2026-07-03 [process-learning] 全緑テスト+80%超カバレッジでも実行時異常系・セキュリティ境界のテスト空白は残る(Phase 0徹底レビュー)

- 事実(何を観測したか): Phase 0完了判定(545 passed、カバレッジ実測88%)の直後に行った6観点の徹底レビューで、実行再現可能なバグ4件(ExecutionEvidence `reproduction_bundle` の虚偽blob参照、diff parserのhunk境界誤認・quoted path未対応、generator CLI 2本のexcept順序による到達不能exit分岐、Tool Gateway redactionのkey名不足)を検出した。加えて、実装は正しいのにテストが一度も発火していないセキュリティ境界が3箇所(runner allowlist / repo tool path traversal / seed manifest `..` 拒否)あった。schema契約の負例テストは厚い一方、実行時コンポーネントの異常系が系統的に薄かった。
- 学び(なぜ・何を変えるべきか): 「テストが全緑・カバレッジ80%超」はDoDの必要条件であって十分条件ではない。特に(1)防御コード(allowlist・traversal拒否・redaction)は正常系テストだけでは一生発火しない、(2)出力に埋まる参照(blob ref等)は読み出しまで往復しないと捏造に気づけない、(3)パーサは代表的fixture以外の実在形(quoted path・rename/delete)で黙って誤る。Phase完了後にPoC再現つきの実行検証型レビューを一巡させる価値がある。
- アクション(変更したもの・リンク): 指摘全件を修正し回帰テスト+112本を追加(657 passed、CI coverage gate 80%を配線、検収レビュー合格)。修正内容は本コミットdiffを参照。あわせて `status: done` なのにDoDチェックボックス未記帳のタスクが17/23件あった点を記帳で解消 — タスク完了処理にチェックボックス記帳を含めること。

## 2026-07-03 [northstar-proposal] QualityAnalyticsSnapshotのevidence bucket必須化はPhase 0のEvidence Store集約都合として扱う

- 事実(何を観測したか): `quality-analytics-snapshot.schema.json` はNorth Star §6.17の例示に無い `evidence` bucketをdomain必須にしている。Phase 0ではReleaseReadinessReportやgate理由がEvidence Store / run参照を複数扱うため、QualityAnalyticsSnapshot側にもsource_refsとは別の集計bucketが必要になった。
- 学び(なぜ・何を変えるべきか): これは§6.17の文面からの構造逸脱なので、North Star本文へ即時複製せず、実運用でsnapshot producerがこのshapeを必要とするかを確認してから改訂判断する。Phase 0ではschema `$comment` / descriptionに逸脱理由を残し、後続producer実装時に再評価する。
- アクション(変更したもの・リンク): `schemas/quality-analytics-snapshot.schema.json` に逸脱理由と本entry参照を追記。North Star改訂は未承認のため未実施。

## 2026-07-03 [process-learning] モジュールREADMEのNorth Star項目名列挙は要約であり契約複製ではないと扱う

- 事実(何を観測したか): Phase 0 reviewで、モジュールREADMEにNorth Star由来の項目名を列挙する作業がタスクDoDの「明記」要求を満たす一方、AGENTS.md変更ルール2「North Starの内容を計画・タスクへ複製しない」と緊張することを確認した。
- 学び(なぜ・何を変えるべきか): READMEでは§番号と実装境界を示し、North Star本文の詳細な要件文は複製しない。項目名列挙は利用者がmodule boundaryを理解するための要約に留め、仕様の正本性はschema / policy / North Star §参照へ戻す。
- アクション(変更したもの・リンク): 今後のREADME修正では、North Star項目の全文複製ではなく、§番号・Phase 0スコープ・実装しないものを簡潔に書く。

## 2026-07-03 [process-learning] Phase完了判定は「テストID+再実行可能コマンド」に落ちた完了条件なら機械的に済む(Phase 0 review)

- 事実(何を観測したか): /phase-reviewでPhase 0完了条件7項目を再検証した。5項目はpytestのテストID単位で、2項目(TestAssetIndex / ChangeImpactSpec生成)はCLI実実行+validator検証で、全項目をその場で再実行して確認できた(全体 `uv run pytest` 545 passed。個別根拠は [phase-0-foundation.md §2](../plan/phase-0-foundation.md) の検証記録)。generatorのtimestamp既定が決定的sentinelだったこと(T-009 / T-010)も再実行検証を安定させた。判定側の追加作業はゼロで、「充足の解釈」を要する項目が無かった。
- 学び(なぜ・何を変えるべきか): phase-0計画§2の方針「完了条件は検証方法まで具体化する」は機能した。以降のPhase計画でも、完了条件1項目ごとに再実行可能なコマンドまたはテストIDへ落とす形を維持する。曖昧な条件(例:「〜が使える」)は判定時に解釈コストと恣意性を生む。§29 DoD追跡表の更新では、Phase 0成果はすべて「基盤のみ」であり完成形項目の達成ではないと保守的に記録した(agent実行・実運用が乗って初めて達成になる)。
- アクション(変更したもの・リンク): [phase-0-foundation.md §2](../plan/phase-0-foundation.md) へ根拠リンク記入、[00-overview.md](../plan/00-overview.md) のPhase 0 statusをdone化、§29追跡表を項目1 / 5 / 6 / 14 / 15 / 20 / 25で分割し根拠リンク付きで更新。northstar-proposalに値する乖離は無し。

## 2026-07-03 [process-learning] Evidence Store境界のredaction検出はPhase 0では呼び出し側責務として明記する(T-013)

- 事実(何を観測したか): T-013のEvidence Store最小版は、ExecutionEvidenceをschema検証してmetadata DB + blob storeへ保存する境界を実装する。一方、North Star §15.4のraw secret / PII / raw production data / private chain-of-thoughtの機械的検出は、ADR-0003でもPhase 0最小として利用側redaction前提に留めている。
- 学び(なぜ・何を変えるべきか): Phase 0ではstore APIがredaction済みpayloadだけを受け付ける運用契約をREADMEに明記し、機械的検出はTool Gateway redactionや将来のstore policy taskへ送る。Evidence Store自体が未実装の検出をしたように見せない。
- アクション(変更したもの・リンク): `evidence_store/README.md` に保存禁止対象とPhase 0スコープ外を明記。regression guard: `tests/test_evidence_store.py` はsynthetic fixtureのみを保存する。

---

## 2026-07-03 [process-learning] runtime validatorはschema正本を直接読み、date-timeは生JSON境界でtimezone必須にする(T-008)

- 事実(何を観測したか): T-008でartifact validatorをlib + CLIとして実装する際、T-003からの申し送りどおり、生成Pydanticモデル `models/` は `[tool.uv] package = false` 構成の通常スクリプト実行ではimport前提にしにくいことを再確認した。また `jsonschema` の通常設定では `format: date-time` がrelease gate用の強制境界にならないため、timezone無し `created_at` を生JSON validatorが通す余地があった。
- 学び(なぜ・何を変えるべきか): gateの入力になるartifact contract検証は、生成モデルではなくADR-0002の正本である `schemas/*.schema.json` を直接読むruntime validatorに寄せる。`created_at` のtimezone必須意図は生JSON境界でも強制し、生成モデルとの非対称を残さない。future generator / Evidence Storeは `from artifact_validator import validate_artifact` または `python -m artifact_validator` を使い、T-008時点ではpackage設定の見直しや新規ADRに広げない。
- アクション(変更したもの・リンク): `artifact_validator/` にschema registry + `FormatChecker` 付きvalidator + CLIを追加。`tests/test_artifact_validator.py` で7 artifact種のpass、`source_refs` 空/欠落、未知/欠落 `artifact_type`、timezone無し `created_at`、machine-readable errorを検証。記録: [T-008](../tasks/phase-0/T-008-artifact-validator.md)。

---

## 2026-07-02 [process-learning] 出力契約schemaの必須度は最初のproducerのPhase能力と突き合わせて決める

- 事実(何を観測したか): T-006でTestAssetIndex / ChangeImpactSpec schemaをNorth Star §6.13 / §6.9のサンプルinstanceに寄せて定義したところ、最初のproducerであるT-009 / T-010のPhase 0 DoDと矛盾した。T-009はcovered requirement / flake rate等を未収集として扱う前提で、T-010はrequirement / riskへの意味的マッピングをPhase 1以降に送る前提だったため、required + `minItems: 1` や非null必須numberはPhase 0 generatorにrefの捏造を迫る契約になった。
- 学び(なぜ・何を変えるべきか): 出力契約schemaの必須度(required / minItems / nullable)は、その契約の最初のproducerタスクのDoD・Phase能力と突き合わせて決める。North Starのサンプルinstanceが全fieldを埋めていても、それだけでは必須化の根拠にならない。
- アクション(変更したもの・リンク): T-006一次検収対応で、Phase 0 producerが未収集にできるmapping配列はrequiredのまま空配列を許し、未収集のflake_rateはnullを許す契約へ修正。regression guard: `tests/test_test_asset_impact_schemas.py` のPhase 0 generator/candidate sample。

## 2026-07-02 [process-learning] allOf外部$ref(modular reference)はdcgのファイル単位生成と両立しない — ディレクトリ一括生成へ移行(T-004)

- 事実(何を観測したか): T-004でspec schemaが `allOf: [{"$ref": "artifact-base.schema.json"}]` を持った時点で、datamodel-code-generator(0.66.3)のファイル単位 `--output <file>.py` が「Modular references require an output directory」で失敗。ディレクトリ入力+ディレクトリ出力の一括生成に切り替えると成功し、`class RequirementSpec(ArtifactBase)` というクラス継承+モジュール間importが生成される。付随の実測: (1) モジュール名はdcg規則で `<type>_schema.py` になる(旧 `<type>.py` から改名)。(2) `__init__.py` も生成物になる(models/ は名前空間パッケージから通常パッケージへ)。(3) dcg既定ヘッダは入力ディレクトリ名(=一時dir名)を `__init__.py` に埋めて決定性を壊すため `--custom-file-header` で置換が必要。(4) 一括実行はschema parse失敗時のエラーにファイル名を含めないため、事前に個別JSON parseで文脈を付与する必要がある。(5) 入力ディレクトリに非schemaファイル(README等)があるとYAMLとしてparseして失敗するため、一時ディレクトリへ `*.schema.json` のみコピーして渡す。
- 学び(なぜ・何を変えるべきか): 生成器の制約がモジュール命名などリポジトリ規約側に波及する。schema間参照(継承)を導入する時は、生成側の挙動(命名・決定性・エラー文脈)を先に実測してから規約を確定する。
- アクション(変更したもの・リンク): `scripts/gen_models.py` をディレクトリ一括生成へ書き換え([T-004](../tasks/phase-0/T-004-core-spec-schemas.md))。生成物は `models/artifact_base_schema.py` 等へ改名(T-003記録に追記済み)。regression guard: `tests/test_gen_models.py`(継承の生成・`__init__.py` ヘッダ・決定性・orphan掃除)。

## 2026-07-02 [process-learning] uniqueItems等、dcgがPydantic制約へ変換しないJSON Schema制約がある(生JSONのみ強制の非対称)

- 事実(何を観測したか): `oracle_type` の `uniqueItems: true` は生JSON検証では重複をrejectするが、dcg(0.66.3)生成モデルは `list` のまま重複を通す(T-004の2次レビューで検出、実測再現済み)。`format: date-time`(T-003)とは逆向きの非対称(あちらは生JSONが緩く生成モデルが厳しい)。
- 学び(なぜ・何を変えるべきか): JSON Schema制約と生成モデルの強制範囲は一致しない前提で扱う。非対称を見つけたら「schema description/$commentへの明記+挙動を固定するregression test」をセットで置く(Signal extra / naive datetimeと同じ扱い)。gateの入力になる契約検証は生JSON側(T-008 validator)を正とする。
- アクション(変更したもの・リンク): `schemas/oracle-spec.schema.json` のdescriptionへ明記。`tests/test_core_spec_schemas.py::test_generated_model_does_not_enforce_unique_oracle_type` で挙動を固定。

## 2026-07-02 [process-learning] 開いたobjectは additionalProperties: true を明示しないと生成モデルが追加fieldを黙って捨てる(T-005〜T-007への注意)

- 事実(何を観測したか): OracleSpec.signals のitem(type毎に異なるfieldを持つ開いたobject)で `additionalProperties` を省略(=JSON Schema既定のtrue)したところ、dcg生成の `Signal` モデルはPydantic既定の `extra=ignore` になり、`model_dump()` のround-tripで `query_ref` / `endpoint` 等の中身が黙って消えた(silent data loss)。schema側に `"additionalProperties": true` を明示すると `extra='allow'` が生成され保持される。
- 学び(なぜ・何を変えるべきか): JSON Schemaの既定値と生成コードの既定値は一致しない。「開いておく」意図は省略ではなく明示で表現する。開いたobjectには生成モデルのround-trip保持テストを置く。
- アクション(変更したもの・リンク): `schemas/oracle-spec.schema.json` のsignals itemに `additionalProperties: true` を明示($commentに理由)。regression guard: `tests/test_core_spec_schemas.py::test_generated_signal_model_preserves_extra_fields`。

## 2026-07-02 [process-learning] 子schemaでconst再宣言したfieldは子のrequiredにも再列挙しないと生成モデルがOptional化する(T-005〜T-007への注意)

- 事実(何を観測したか): `artifact_type` をbase側required+子側 `const` 再宣言のみとした場合、dcg生成の子クラスは `artifact_type: Literal['requirement_spec'] | None = None` になり、base側の必須が子のfield再定義で上書きされて緩む(生JSON検証はallOf合成で必須のまま=生成モデルとの非対称)。子の `required` に `artifact_type` を再列挙すると必須の `Literal[...]` になる。
- 学び(なぜ・何を変えるべきか): Pydanticの継承はfield再定義が完全上書きのため、「子schemaで再宣言したfieldは子のrequiredにも再列挙する」を規約にする。T-005〜T-007のspec schema定義でも同じ確認を行うこと。
- アクション(変更したもの・リンク): コアspec 3 schemaの `required` へ `artifact_type` を追加。`tests/test_core_spec_schemas.py::test_required_matches_domain_required` が「domain必須 ∪ {artifact_type}」との完全一致を検証する。理由はschema descriptionにも記載。

## 2026-07-02 [process-learning] package=false構成では生成モデル(models/)のimportがpytest経由でしか解決されない(T-008への申し送り)

- 事実(何を観測したか): T-003の徹底レビューで、`uv run python scripts/<script>.py` のような通常のスクリプト実行では `models/` がimportできないことを実測確認(`sys.path[0]` はスクリプト自身のディレクトリでありcwdではない)。pytest下ではpyproject.tomlの `pythonpath = ["scripts", "."]` で解決される。`[tool.uv] package = false` のためプロジェクト自体はinstallされない。
- 学び(なぜ・何を変えるべきか): 生成モデルをテスト以外のランタイムコード(validator lib/CLI等)から使う段になったら、import解決方式(srcレイアウト化+`package = false` 見直し / パッケージ化 / sys.path運用)を決める必要がある。scaffolding時点の `package = false` は「コードがscripts/しか無い」前提の判断で、コードベースが育つと見直し対象になる。
- アクション(変更したもの・リンク): pytest側は `pythonpath` に `"."` を明示して`__init__.py`・import-mode非依存にした(T-003)。ランタイム側の方式決定は[T-008](../tasks/phase-0/T-008-artifact-validator.md)へ申し送り(タスク参照節に追記済み。ADR-0002委任範囲を超える場合はADRを起票する)。

## 2026-07-02 [process-learning] JSON Schemaのarray itemに制約を付けると生成Pydanticモデルが名前付きRootModelに具象化される(T-004〜T-007への注意)

- 事実(何を観測したか): T-003で `source_refs` のitemsに `minLength: 1` を付けたところ、datamodel-code-generator(0.66.3)が `list[str]` ではなく `SourceRef(RootModel[str])` のlistを生成した。要素の等価比較・`in`判定・`startswith` 等が静かに壊れる(code reviewでHIGH指摘)。`--collapse-root-models` / `--use-annotated` でも解消しない。
- 学び(なぜ・何を変えるべきか): 「schema→コード単方向生成」方式では、schema上の表現の選び方が生成コードのAPI品質を左右する。array itemへのスカラー制約は具象化トリガーになるため、契約上必須でない限り避ける。North Star/ADRが要求しない自前の追加ハードニングは、生成物への影響を確認してから入れる。生成モデルには値セマンティクスのregressionテスト(例: 要素が素のstrであること)を置く。
- アクション(変更したもの・リンク): `schemas/artifact-base.schema.json` のitem側minLengthを除去(`minItems: 1` は維持=ADR-0002の要求)。`tests/test_gen_models.py::test_source_refs_items_are_plain_strings` をregression guardとして追加。schema内 `$comment`/descriptionに理由を記載。T-004〜T-007のschema定義でも同じ確認を行うこと。

## 2026-07-02 [process-learning] 決定的diff検証には出力に埋まる「生成時刻」類を入力で固定できる設計が要る(CI初配線の学び)

- 事実(何を観測したか): T-003でCI(GitHub Actions)を初配線した際、`regen_task_index --check` は `--generated-on` の既定が実行日のため、内容が最新でもコミット済み `_index.md` と日付だけで不一致(exit 1)になることを確認した。datamodel-code-generatorも既定ではtimestampをheaderに埋め、formatterの既定も将来変わる予告(FutureWarning)があり、いずれも「再生成→diff無し」検証を壊す要因になる。
- 学び(なぜ・何を変えるべきか): 「生成物をコミットしCIで再生成→diff無しを検証する」方式(ADR-0002)は、生成が決定的であることが前提。実行時刻・ツール既定値など入力以外に依存する要素は、生成コマンド側で固定(disable / 明示指定)するか、コミット済みの値を入力として渡す。
- アクション(変更したもの・リンク): `scripts/gen_models.py` は `--disable-timestamp` とformatter明示(black / isort)で最初から決定化。`.github/workflows/ci.yml` の_index検証はコミット済み `_index.md` から生成日を抽出して `--generated-on` へ渡す方式にした。

## 2026-07-02 [process-learning] PhaseレベルstatusのUpdate手順が作業フローに無く、T-001完了時に更新漏れ

- 事実(何を観測したか): T-001がdoneになった時点でPhase 0は着手済みだったが、`docs/plan/00-overview.md` のPhaseレベルstatusは `not_started` のまま残っていた(T-002の監督レビューで検出)。AGENTS.md作業フロー(タスク実行時)には `_index.md` の再生成(手順5)はあるが、「Phaseの最初のタスクがdoneになったら00-overviewのPhaseレベルstatusを更新する」手順が明記されていない。
- 学び(なぜ・何を変えるべきか): statusの持ち場が2層ある(タスクレベル=各タスクfrontmatter、Phaseレベル=00-overview。変更ルール3)のに、作業フローがタスクレベルの更新しか規定していないため、Phaseレベルの更新はトリガーを失い漏れる。Phase statusが変わる契機(最初のタスクdone、Phase完了判定)を作業フローに組み込むかは将来判断(フロー改訂はこのエントリのスコープ外)。
- アクション(変更したもの・リンク): `docs/plan/00-overview.md` のPhase 0 statusを `in_progress` へ修正(2026-07-02、オーナー承認済み)。AGENTS.md作業フロー本体は未改訂(改訂は将来判断)。(2026-07-02追記: `phase-0-foundation.md` 冒頭に残っていたstatus複製行(`not_started` のまま)をT-004徹底レビューで検出し、status値を複製しない参照のみの行へ修正して二重管理を解消。)

## 2026-07-02 [process-learning] datamodel-code-generator生成コマンド+CI diff検証をT-003へ申し送り

- 事実(何を観測したか): ADR-0002 Consequences「後続タスクへの影響」でT-002に「datamodel-code-generatorの生成コマンドとCI diff検証を整備する」と書かれているが、T-002時点では `schemas/*.schema.json`(生成の入力=正本)がまだ1つも存在しない(実体はT-003以降で作られる)。入力の無い生成コマンドを配線しても検証できず、意味のあるCI diffチェックにならない。
- 学び(なぜ・何を変えるべきか): 生成コマンド+CI diff検証は「schema実体があること」に依存するため、T-002(scaffolding)ではなくschema定義タスク側で整備するのが正しい依存順序。T-002ではdatamodel-code-generatorをdev依存として用意するに留め、生成の配線はT-003に持たせる。
- アクション(変更したもの・リンク): datamodel-code-generatorを `pyproject.toml` の dev グループに追加(ツールは先行して利用可能)。生成コマンド(`datamodel-code-generator --input-file-type jsonschema` 相当)とCI再生成→diff無し検証の配線はT-003([T-003](../tasks/phase-0/T-003-artifact-base-schema.md))のDoDで実施する申し送りとする。これはADR-0002が具体化をT-002へ委任した範囲内の判断であり新規ADRは不要。

<!-- テンプレート
## YYYY-MM-DD [型] タイトル

- 事実(何を観測したか):
- 学び(なぜ・何を変えるべきか):
- アクション(変更したもの・リンク):
-->
