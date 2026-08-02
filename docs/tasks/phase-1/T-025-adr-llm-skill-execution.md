---
task_id: T-025
epic: phase1-setup
plan_ref: phase-1-crud-mvp.md#7-リスクと未確定事項
status: done
owner:
blocked_by:
---

# T-025: ADR-0005 LLM skill実行方式の決定(OQ-5)

## 目的

Phase 1で初めてLLM駆動のskill(source-grounding、requirement-risk-analysis等)を実装するにあたり、LLM呼び出しの方式を決定しADRとして記録する。Phase 0は決定的実装のみでLLM統合が存在しないため、この決定なしにskill実装(T-027以降)へ進めない。

## 参照

- 計画: §7 リスクと未確定事項(OQ-5、「候補生成+人間レビュー必須」方針)
- North Star: §7.1(skill package構造)、§16.4(QAパイプライン自体の防御)、§15.4(保存しないもの)

## DoD

- [x] `docs/decisions/adr-0005-llm-skill-execution.md` が作成され、以下が決定されている:
  - [x] provider / model(既定モデルと切替方法。コスト効率のためタスク種別ごとのmodel選択方針を含む)
  - [x] 呼び出し境界(skillからのLLM呼び出しをどのモジュールが仲介するか。Tool Gateway経由か直接かの判断と理由)
  - [x] 認証情報の扱い(veridiaが扱う環境変数名。秘密情報のハードコード禁止、起動時検証。**API直結ならAPI key管理、サブスクリプションCLI経由ならCLIの資格情報ストアへの委任とbackend可用性検証**。どちらの経路かはADRの決定に従う)
  - [x] コスト管理(トークン使用量の記録先、上限方針)
  - [x] LLM出力の扱い(構造化出力→schema検証→候補として保存、human review必須の実装形)
  - [x] 再現性の限界の扱い(LLM出力は非決定的である前提で、prompt / model / パラメータをtraceへ記録する方針)
- [x] 既存ADR(0001〜0004)と同じフォーマット(status / context / decision / consequences)で書かれている
- [x] `docs/plan/00-overview.md` の未決事項表でOQ-5が「決定済み(日付)」になっている

## 検証方法・根拠

**成果物**: [ADR-0005](../../decisions/adr-0005-llm-skill-execution.md)(status: accepted、2026-08-02)

**DoD 3項目目の文言について。** 起票時は「API key管理(環境変数名。ハードコード禁止、起動時検証)」であり、従量課金APIの利用を暗黙の前提としていた。オーナー確認の結果、利用可能な契約はClaude / Codexのサブスクリプション範囲でAPI keyを保有しないことが判明したため、**要件の趣旨(秘密情報を安全に扱う / 起動時に検証する)を保ったまま「認証情報の扱い」へ文言を改めた**(オーナー承認済み)。ADR-0005 Decision 4の決定により、veridiaは資格情報に一切触れず、認証はCLIの資格情報ストアへ委任し、起動時検証はbackendの可用性確認(CLI存在・バージョンallowlist・認証状態・capability probe)に置き換わる。**要件を緩めていない** — 扱う秘密が無くなる分、趣旨としては強化されている。

**決定の根拠**: 机上判断を避けるため、両CLIの非対話実行をリポジトリ外の空ディレクトリで実測した(ADR-0005 Context「実行環境の実測」)。API key未設定でのサブスクリプション認証、JSON Schema制約出力、消費量の自己申告、終了状態を確認。あわせて、両CLIが既定でprompt本文をローカルへ平文永続化することを実データで確認した(Decision 5.5の根拠)。

**オーナー確認**(タスク備考の指示。provider契約・課金に関わるため):

| 確認事項 | 回答 |
|---|---|
| 利用可能なprovider契約 | Claude / Codexのサブスクリプション範囲。従量課金APIの契約なし |
| API keyの既存運用 | 未設定 |
| 既定model | Claude Opus 5でよい。Codex(GPT-5.6 Sol)も利用可能にする(位置づけは選択可能なbackend) |
| コスト上限 | 設けない |
| prompt記録と§15.4の整合 | 指示部は全文・データ部は参照 |
| Codexの分離保証がClaudeより弱い件 | 制限を明記したうえで制約なしに使う |
| DoD文言の読み替え | 誤認しない形にする(上記のとおり改訂) |

**レビュー**: オーナー指示によりCodex(gpt-5.6-sol、effort high、read-only sandbox)で計5回レビュー。判定は `request-changes` ×4 → **`approve`**。指摘は延べ blocker 6 / major 16 / minor 5。全ての事実主張をCLIの実挙動・既存コード・North Starで裏付けたうえで反映した。主な修正:

- CLI自身のセッション永続化の見落とし(`--no-session-persistence` / `--ephemeral` を必須化)
- 「空cwdで指示ファイル経路を閉じる」の不成立(祖先方向へ探索されるため、cwdは指示ファイルを持つ祖先の外に置く)
- `trust_level` をLLMに生成させるとtrust gateが自己申告で迂回可能になる問題(authorityをingestion層へ)
- ArtifactBase必須の `confidence` が生成経路から欠落
- 複数artifact出力(T-030)の契約が未定義
- trace保存順とinsert-only制約の矛盾

**検証**: `uv run pytest` 658 passed / `uv run ruff check .` / `uv run ruff format --check .` いずれもgreen。ADR内の相対リンク・節番号参照はすべて実在先に解決することを確認。

**未解決の前提**: ADR-0005「前提の欠落と申し送り」節にP-1〜P-4として記録した。**P-1(生成artifactの保存先が存在しない)はT-027着手前のhard gateであり、オーナー判断が必要**。本ADRの妥当性には影響しない。

## 備考

決定に際してオーナーの確認を取ること(provider契約・課金に関わるため)。既定候補はClaude API(Anthropic)だが、オーナーの利用可能な契約を確認してから決定する。

→ 確認の結果、**API直結ではなくサブスクリプション契約下のCLI(headless)経由**に決定した(ADR-0005 Options A)。API直結は排除せず `LLMClient` に実装の口を残すが、移行にはADR-0005のamendまたはsupersedeを要する。

## 記録(完了時に記入)

- domain / learning-log / decisions へ記録した知見:
  - [ADR-0005](../../decisions/adr-0005-llm-skill-execution.md)(本タスクの成果物)
  - [learning-log 2026-08-02](../../knowledge/learning-log.md) に5件記帳
