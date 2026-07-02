# qa-agent-strategy-v3.md 多角的レビュー

- レビュー日: 2026-07-02
- 対象: `docs/qa-agent-strategy-v3.md`(v3 統合版、3390行)
- 目的: 「エージェントと人間の協働によるソフトウェア品質保証」の実現に向けて、プランの現実性・代替案・実運用上の改善点を評価する

---

## 0. 総評

**思想は正しい。しかしこれは「理想形の仕様書」であって、まだ「実行計画」ではない。**

Oracle-first、Source grounding、Evidence-by-default、Reuse-before-generation、Human calibration という中核原則は、テストオラクル問題・metamorphic testing・agent evals の研究/実務知見と整合しており、維持すべき。外部参照もファクトチェックした範囲で正確だった(§7)。不採用判断(自然言語Workflow生成、AgentOps Dashboard の排除)も的確で、「agent管理ではなく品質判断が主語」という軸は一貫している。

一方で、致命的な欠落が3つある。

1. **体制・工数・コストの章が存在しない。** 約30種のartifact、38 skill、12 agent、16 gate、9 dashboard view、40+ KPI を定義しているが、誰が・何人で・どの予算で作るのかが一切書かれていない。4週間MVP Backlogは、内容を積算すると小規模チームで1〜2四半期に相当する(§1.1)。
2. **「人間と協働」が目的なのに、人間側の体験が設計されていない。** ドキュメントの主語はほぼシステムであり、レビュアーの負荷見積り、レビューUI、信頼獲得の段階設計(shadow→warn→block)がない(§1.3)。
3. **コールドスタート問題が扱われていない。** Quality Knowledge Base・TestAssetIndex・CoverageModel は「存在する前提」で下流が設計されているが、初期構築の精度と工数こそが最大の難所(§1.2)。

**結論: アーキテクチャのv3をv4に磨くより先に、「最初の8週間で何を証明するか」を定義した薄い実行計画を別文書として切り出すべき。** 本ドキュメントは North Star(目標アーキテクチャ)として保持し、実行計画とは分離する。

### 指摘事項サマリ

| ID | 重要度 | 指摘 |
|---|---|---|
| C-1 | Critical | 4週間MVPの見積りが非現実的(実態は1〜2四半期規模) |
| C-2 | Critical | コールドスタート問題(KB/TestAssetIndex初期構築、カバレッジ指標の分母問題) |
| C-3 | Critical | 人間協働の設計不足(レビュー負荷未見積り、ラバースタンプ化リスク) |
| C-4 | Critical | QA基盤自体がリリースのSPOF化(可用性SLO・縮退運転・手動フォールバック未定義) |
| H-1 | High | LLM推論の出力をgateに直結する危険(TIA精度、dedupスコア未定義、confidence非校正) |
| H-2 | High | Agent過剰設計 — 大半は「pipeline + LLMステップ」で足り、agent化は探索系のみでよい |
| H-3 | High | Gate 16種の同時導入は信頼を毀損する — 段階的enforcement設計が必要 |
| H-4 | High | Artifact間の鮮度伝播(staleness propagation)が未定義 |
| H-5 | High | Oracle gate 100%要求のデッドロック — 既存機能のgrandfathering方針がない |
| H-6 | High | Sandbox/Testability整備の重さが過小評価されている |
| H-7 | High | QAパイプライン自体への攻撃(gate操作を狙う入力汚染)が脅威モデルにない |
| M-1 | Medium | Build vs Buy の検討が欠落 |
| M-2 | Medium | 人間の修正をskill改善へ還流するactive learningループがない |
| M-3 | Medium | workflow定義が4箇所以上で重複し、順序が微妙に食い違っている |
| M-4 | Medium | KPI 40+は過多。North Star指標とベースライン計測がない |
| M-5 | Medium | 閾値(0.85/0.90、80%等)の根拠と較正手順が未記載 |
| L-1 | Low | ドキュメント内の軽微な矛盾・表記ゆれ |

---

## 1. Critical: 実現可能性のギャップ

### C-1. 4週間MVPは4週間では終わらない

§21のWeek 1だけで、Evidence Store、Trace Store(trace_id/run_id設計込み)、Tool Gateway最小版、8種のartifact schema定義が積まれている。Evidence Store と Tool Gateway はそれぞれ単体で数週間規模のインフラ構築であり、Week 2〜4には agent 3種 + skill 8種 + PR comment UI + sandbox実行 + gate wiring + dashboard最小版が続く。

**なぜ問題か:** 見積りが1桁ずれた計画は、途中で「動くものが何もないまま疲弊する」典型パターンに入る。特に veridia リポジトリは現時点でドキュメントのみの greenfield であり、適用対象のプロダクトすら未選定に見える。

**推奨:**

- 最初の成果物を「**tracer bullet**」に縮める。例: *実在する1リポジトリのPRに対して、change impact要約 + 影響テスト候補 + 不足観点を、source_refs付きでPRコメントする。read-only、gateなし、sandboxなし。* これは既存のCI + LLM API + 数百行のコードで2〜3週間で到達可能で、かつ「LLMによる変更影響分析は現場で使い物になるか」という最大の不確実性を最初に検証できる。
- Phase 0(横断的な基盤整備フェーズ)を廃し、**垂直スライス**で切り直す。基盤(Evidence Store等)は、それを必要とする最初のスライスの中で最小実装する。
- ロードマップ各Phaseに「検証したい仮説」「体制」「概算工数」「中止基準(exit criteria)」を追記する。**やめる条件がない計画は、失敗しても止まらない。**

### C-2. コールドスタート問題 — このプランの隠れた最難関

下流の全機能(TestImpactPlan、CoverageGap、DuplicateTestReport、ReleaseReadinessReport)は、上流の知識基盤の精度に依存する。

- **TestAssetIndex:** 既存テストを requirement / risk / oracle に紐付ける作業は、レガシーなテストスイートではほぼゼロから。LLMで推定可能だが誤りを含み、その誤りは test impact selection や dedup 判断にそのまま伝播する。§21はこれを「Week 1のschema定義タスク」として扱っているが、難所はschemaではなく**マッピング精度**である。
- **カバレッジ指標の分母問題:** `requirement_coverage: 0.92` のような数値(§6.17)は、要求抽出が網羅的である前提で初めて意味を持つ。初期の抽出漏れが多い段階でこの数値をdashboardに出すと、**偽の精度(false precision)**でリリース判断を誤らせる。
- **StateModel / OracleSpec:** 全機能分を前もって作るのは不可能。

**推奨:**

- **Just-in-time modeling** を原則として明文化する: KBはPRが触れた機能から漸進的に構築する。全体マッピングのバッチ構築は行わない。
- TestAssetIndex に **精度検証プロセス**を定義する(サンプル監査: インデックスされた紐付けのN%を人間が検証し、精度がX%未満なら下流gateを無効化)。
- カバレッジ系メトリクスに「分母の信頼度」を併記する仕様にする(例: `requirement_extraction_completeness: estimated/audited`)。信頼度が低い間はスコアではなく件数ベースの表示に留める。

### C-3. 「人間と協働」の人間側が設計されていない

human review はほぼ全gateに登場する(新規OracleSpec、critical RiskSpec、high-risk skip、duplicate override、CoverageGap acceptance、RiskAcceptance、judge sample 10〜20%…§27.2)。しかし:

- **負荷の見積りがない。** 週20 PRの中規模チームで、PRあたり2〜5個のartifactがreview対象になると、週50〜100件のレビューが発生し得る。誰が捌くのか。
- **レビューのUXがない。** レビュアーは何を見るのか — JSON artifactをPRコメントで読むのか。RequirementSpec の妥当性を数分で判断できる表示は何か。この設計がないと、レビューは形骸化する。
- **ラバースタンプ化の検知がない。** 承認率が~100%でレビュー所要時間が数秒なら、そのgateは機能していない(automation complacency)。judge-human agreement は測るのに、**human review の実効性**は測っていない。

**推奨:**

- 人間側のワークフロー章を新設する: ペルソナ別(QAエンジニア/開発者/EM)の1日の体験、レビュー画面の要件、1レビューあたり目標時間。
- KPIに追加: `human_review_load_per_person_week`、`review_median_time`、`approval_rate`(100%近傍が続くgateはアラート)、`human_edit_rate`(AIの出力を人間が修正した割合 — 品質の実測値になる)。
- レビューを**バッチ化・サンプリング化**できる箇所を明示する(全件レビューが必要なのは critical riskのみ、等)。

### C-4. QA基盤がリリースの単一障害点になる

§17.1「ReleaseReadinessReport がない release candidate は pass 不可」等のルールにより、**この基盤が落ちると誰もリリースできなくなる**。基盤自体の可用性SLO、縮退運転モード、監査付き手動オーバーライド手順が未定義。

**推奨:** 「QAプラットフォーム自体の運用」章を追加する — 可用性SLO、degraded mode(基盤停止時は従来のCI green + 手動チェックリスト + 事後記録で代替可、ただしEM承認と監査ログ必須)、基盤障害のインシデント対応。§27.1のblock rulesには必ず「基盤起因の場合の例外パス」を対で定義する。

---

## 2. High: 設計上の改善点

### H-1. LLM推論の出力をgateに直結してはいけない

3箇所で「LLMの確率的出力」が「決定的なblock判断」に接続されている。

1. **Test Impact Analysis:** LLMによる差分→影響推定は不安定。確立されたTIAは coverage map + dependency graph による決定的手法(§22の技術スタックには記載があるが、skill設計上はLLMが主役に読める)。**決定的TIAを土台にし、LLMは requirement/risk への意味的マッピングの補完に限定**すべき。また `skipped_test_escape_rate` を測るだけでなく、**セーフティネットとして nightly は常に全件実行**(skipはPRループのみ)を明記する。
2. **Dedupスコア:** §13.4 は 0.85/0.90 の閾値を定めるが、**類似度関数が未定義**(embedding? AST? カバレッジ重複? oracle重複?)。定義なき閾値は疑似精度。さらにテキスト類似度が高くても境界値が違えば別テストであり、score>=0.90での自動blockは正当なバリアントの生成を妨げ得る。**初期は advisory(warn + extend提案)に留め、false-block率を計測してからblock化**する。
3. **confidence フィールド:** `confidence < 0.75 → human review`(§6.10)は、LLMの自己申告confidenceが較正されている前提だが、一般に較正されていない。**複数trial間の一致率や、retrieval根拠の被覆率など、観測可能なプロキシに置き換える**か、confidenceの較正手順(実績とのcalibration curve)を定義する。

なお dedup の設計思想として、**生成後のコード類似検出(DuplicateTestReport)より、生成前の意図レベル照合(TestReuseCandidate)を主、コード類似検出を保険**と位置付け直すと一貫する。計画段階で「このgapにはextendで対応」と人間が承認してから生成する方が、生成→検出→破棄より安く確実。

### H-2. Agent 12種は過剰設計 — pipeline-first を推奨

§8.1自身が「agentは役職ではなく権限境界」と述べている通り、Source Grounding / QA Analyst / Oracle & Evaluation などの大半は、**入力artifact→出力artifactの変換**であり、自律的なループを必要としない。これらは「workflow engine(Temporal等)上のステップとして実行されるLLM呼び出し + validator」で十分で、その方が再現性・監査性・コストの全てで優る — 本ドキュメント自身の価値観とも一致する。

**agent(自律ループ)が正当化されるのは探索が本質の領域のみ:** exploratory testing、failure triage の根本原因探索、security redteam。それ以外はまず決定的pipelineとして実装し、必要が実証されてからagent化する。§8.2でQuality Intelligenceに対して既に「MVPはskill群、agent化は後」と正しく判断しているので、**同じ判断を全agentに適用**するのが筋。multi-agent handoff(§8.4)はMVPから排除してよい。

### H-3. Gate 16種の同時導入は信頼を破壊する

false block はチームの信頼を非対称に毀損する(1回の誤blockは10回の正しいwarnより記憶される)。§17.1の16 gateを一斉導入すれば、精度が実証される前に「このボットはうるさい」で終わる。

**推奨: gateごとに shadow → warn → block の3段階昇格を制度化する。**

```text
shadow: 判定を記録するだけ。開発者には見えない。precision/recallを計測
warn:   PRコメントに表示。blockしない
block:  マージ/リリースを止める

昇格条件(例): shadow期間4週間以上、precision >= 90%、
              オーナーチームの明示的合意
```

初期にblockまで上げるのは4つで十分: source grounding(P0/P1)、oracle(変更されたP0/P1のみ、H-5参照)、evidence(失敗時)、security。残りはwarn以下から開始。`quality_gate_override_rate` に加えて **gateごとのprecision** と **開発者フリクション指標**(override申請までの時間、苦情件数)を追う。

### H-4. Artifactの鮮度伝播が未定義

versioning rules(§27.3)はあるが、**依存関係の無効化**がない。RequirementSpec が更新されたとき、それを参照する OracleSpec / TestDesignSpec / TestAsset / CoverageModel は自動的に stale マークされるべきで、stale な artifact に基づく gate pass は無効でなければならない。これがないと、KBは半年で「古い正しさ」の墓場になる。**artifact依存グラフと staleness propagation ルールを§6に追加**する。

### H-5. Oracle gate 100%はデッドロックする

「P0/P1要求にOracleSpecがなければrelease不可」を既存プロダクトに適用すると、初日から全リリースがblockされる。**gateの適用対象を「当該リリースで変更されたP0/P1要求」に限定し、既存機能はgrandfathering(棚卸しはバックログ化)する**方針を明記する。

### H-6. Sandbox/Testabilityの重さが過小評価

deterministic clock はアプリ側のclock injection改修、外部サービスmockは契約テスト整備、ephemeral env はインフラ投資を要求する。これは**QA基盤チームだけでは完結せず、プロダクトチームの開発工数を要する**。TestabilityReport(§6.8)で blocker を検出する設計は良いが、検出後の改修は誰の優先順位に入るのかが未定義。

**推奨:** (1) パイロット対象の選定基準に「docker-compose等で環境を複製可能」「外部依存がmock可能」を含める(testabilityが既に高いサービスから始める)。(2) testability改修をプロダクトチームとの合意事項としてRACIに追加し、Phase 1の前提条件に含める。

### H-7. QAパイプライン自体が攻撃対象という視点が欠けている

§16は「テスト対象のagentic security」は網羅的だが、**このQAパイプライン自身への攻撃**が脅威モデルにない。PR説明文・Jiraチケット・仕様書は信頼できない入力であり、それがLLMに渡って gate 判断(リスク評価、テストskip判断)に影響する。つまり「PRの説明文に細工してリスク評価を下げさせ、テストをskipさせて悪意あるコードを通す」攻撃面が存在する。OWASP Agentic Top 10 の ASI01(Goal Hijack)を、テスト対象ではなく**自システムに適用**する必要がある。

**推奨:** (1) 全source内容を「データであって指示ではない」として扱う処理原則を§16に明記。(2) 決定的フロア: セキュリティテストと過去重大障害のregressionはLLM判断ではskip不可(§12.4に一部あるが、「LLMの推奨では絶対に外せないテスト」を明示的に定義)。(3) gate操作を狙った入力汚染のeval caseをsecurity evalに追加。

---

## 3. 代替アプローチの検討(別の良い方法)

### M-1. Build vs Buy が検討されていない

本プランのうち、TIA(coverage-based test selection)、test management、coverage分析、APM連携は成熟した既製品が存在する領域。全部を内製する合理性は薄い。**内製の価値が本当に高いのは LLM固有の新規領域**: OracleSpec提案、MRSpec設計、LLM/RAG eval harness、evidence-grounded なリリースレポート生成。§2.4でTricentis製品群を「思想だけ採用」としているが、**「どの部品は買う/OSSを使う/作る」の判断表**を追加すべき。個人/小規模で始めるなら特に、既存CI・カバレッジツールの上に薄く載せる構成が現実的。

### 代替案A: Assist-first(gate なしの copilot として開始)

最初の1〜2四半期は**一切blockしない「QAレビューcopilot」**として運用する: PRに対しリスク・不足観点・oracle提案・影響テスト候補をコメントするだけ。この間に precision データと人間の修正データが蓄積され、(a) gate化の判断材料、(b) skill改善の教師データ、(c) チームの信頼、の3つが同時に得られる。gateは「精度が証明された提案」の昇格として導入する。これは「人間と協働」という目的に対しても、最初から検問所を作るより整合的。

### 代替案B: 初手ユースケースの再考 — failure triage から始める選択肢

現行プランの初手は「要求抽出→oracle定義」だが、これは最も曖昧性が高く人間の修正負荷が大きい領域。対して **failure triage / flaky診断**は、(1) 判断材料(ログ、diff、履歴)が構造化されていてLLMに向く、(2) gateに関与しないため誤りが低リスク、(3) 現場の痛みが強く即座に感謝される、という点で「最初に信頼を獲得するユースケース」として優れる。change impact要約(read-only)と並ぶ初手候補として検討の価値がある。

### M-2. 人間の修正を還流するループがない

judge の human calibration は設計されているが、**人間が RequirementSpec / OracleSpec / TestImpactPlan を修正した差分**こそ最も価値あるデータであり、これを自動的に skill eval の regression case へ変換する仕組みが必要(§24.4のproduction feedbackに人間修正の還流を追加)。これがあると「協働するほどシステムが賢くなる」ループが閉じる。

---

## 4. Medium/Low: ドキュメント品質

- **M-3. workflow定義の重複:** ほぼ同一のworkflowが §10.2、§12.3、§13.2、§20 Phase 1、§24.1、§31 に記述され、順序が微妙に異なる(例: StateModel と TestabilityReport の位置が §10.2 と Phase 1 で不一致)。実装者はどれを正とするか迷う。**canonical な workflow定義を1箇所に置き、他は参照にする。**
- **M-4. KPI 40+は運用不能:** 全部を最初から計測するとdashboard theaterになる。**North Star(推奨: high-risk escaped defect 件数 + mean time to quality decision + cost)を宣言し、残りは診断用**と位置付ける。また導入前の**ベースライン計測**(現状のescape率、レビューturnaround)がないと、ビジネス価値を証明できない。投資判断を仰ぐ立場なら致命的。
- **M-5. 閾値の根拠:** judge-human agreement 80%、dedup 0.85/0.90、human sample 10〜20%(§17.2)はいずれも出発点としては妥当だが恣意的。「初期値であり、Nサイクルの実測後に較正する」というメタルールを§17に追加する。
- **L-1. 軽微な矛盾:** §18.1「MVPはPR Comment / Gate Reportで十分」に対し §21 Week 4 に「Dashboard最小版」がある(static reportならscope注記で整合させる)。§7.3 と §7.4 で skill 分類の粒度が異なる。「Oracle Agent」(§20)と「Oracle & Evaluation Agent」(§8.1)の名称ゆれ。

---

## 5. 維持すべき強み(変更不要)

1. Oracle-first と oracle優先順位(deterministic > relational > statistical > judge > human)— 本プランの最良の部分
2. Source grounding の徹底と「sourceなし要求生成の禁止」
3. Evidence-by-default と reproduction bundle、inconclusive の扱い
4. Reuse-before-generation — AIテスト生成の最大の failure mode(重複量産)への正しい対策
5. AI judge を最終判定者にしない + human calibration
6. Regression promotion(探索結果を決定的CI資産へ昇格)
7. 不採用判断の明確さ(自然言語Workflow生成、AgentOps UI、完全自律承認の排除)
8. AI は Accountable になれないという責任原則(§23)
9. vendor-neutral な eval harness 方針(OpenAI Evals Platform の2026-11-30廃止を踏まえており、先見的)

---

## 6. ファクトチェック結果

| 記載 | 検証結果 |
|---|---|
| OpenAI Evals Platform: 2026-10-31 read-only、2026-11-30 shutdown(§2.1) | **正確**。移行先としてPromptfoo等が案内されている |
| OWASP Top 10 for Agentic Applications 2026(§2.3) | **実在**(2025年12月公開)。ASI01 Goal Hijack 等 — §2.2(H-7)で自システムへの適用を推奨 |
| ISO/IEC/IEEE 29119-2:2021、Barr et al. オラクル問題、metamorphic testing、NIST AI RMF、SWE-agent(ACI) | 知識範囲内で整合 |

---

## 7. 推奨アクション(優先順)

1. **実行計画を分離する:** 本ドキュメントをNorth Starとして凍結し、「最初の8週間計画」を別文書化。tracer bullet(PR→影響要約+テスト候補のread-onlyコメント)を最初の成果物にする。体制・工数・中止基準を明記。
2. **gate昇格制度(shadow→warn→block)を§17に追加**し、初期block gateを4つに絞る。
3. **人間協働の章を新設:** レビュー負荷見積り、レビューUX要件、ラバースタンプ検知KPI、人間修正の還流ループ。
4. **コールドスタート方針を明文化:** just-in-time modeling、TestAssetIndexのサンプル監査、カバレッジ指標の分母信頼度表示。
5. **決定的フロアを定義:** TIAはcoverage-based を土台にLLMは補完、security/重大regressionテストはLLM判断でskip不可、nightlyは全件実行。
6. **QA基盤自体の運用章を追加:** 可用性SLO、degraded mode、監査付き手動オーバーライド。
7. **Build vs Buy 判断表を§22に追加。**
8. **artifact staleness propagation を§6に追加。**
9. **workflow定義をcanonical化**し、重複箇所を参照に置換。
10. **Oracle gate に grandfathering 方針を追記。**

---

## Appendix: レビューで使用した外部ソース

- OpenAI Evals Platform 廃止日程: [TheRouter.ai](https://therouter.ai/news/openai-evals-agent-builder-prompts-deprecation-november-2026/)、[OpenAI API Deprecations](https://developers.openai.com/api/docs/deprecations)
- OWASP Top 10 for Agentic Applications 2026: [OWASP Gen AI Security Project](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
