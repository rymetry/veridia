---
description: 指定タスクをCodex実装(GPT-5.5)×Claude検収の分業で実行する(run-taskフロー準拠)
argument-hint: <task_id 例: T-005> [--fast]
allowed-tools: Bash(codex:*), Bash(uv:*), Bash(git:*), Read, Edit, Write
---

タスク $ARGUMENTS を、Codex実装×Claude検収の分業で実行してください。

あなた(Claude)は**作業監督者**です。実装作業(コード・スキーマ・テスト・ドキュメント本文の執筆)は行わず、Codex CLIに委譲します。監督者の担当は着手判定・記帳(タスクfrontmatterと「記録」節の記入はドキュメント執筆ではなく記帳に含む)・依存追加(`uv add`)の代行・検収・完了処理・コミットです。

## 引数の解釈

- **task_id**: $ARGUMENTS の先頭トークン(例: `T-005`)。フラグを除いた値でタスクファイルを特定する
- **`--fast`**: 含まれる場合のみ、Codexの実装呼び出し(手順3)に `-c service_tier=fast` を付ける。既定はOFF(fast modeは同モデル1.5倍速・クレジット消費2.5倍)
- コマンド例中のプレースホルダ: `<scratchpad>` はこのセッションのscratchpadディレクトリ、`<n>` は修正の周回番号(1〜2)

## 前提

- 手順の正本は `.claude/commands/run-task.md`(以下「run-taskフロー」)。**最初に読むこと**。本コマンドはその役割分担版であり、run-taskフローの手順・ルール(DoD検証、知見記録、redaction、スコープ外変更禁止等)は全て有効
- Codex呼び出しはBash toolで `run_in_background: true` で起動する(長時間実行対応)。プロンプトはシェル引数で渡さず、**scratchpadのファイルに書いてstdin(`-`)で渡す**(クォート・変数展開事故の防止)
- Codex実行ログの冒頭ヘッダに `session id:` が印字される。**必ず控える**。修正・復旧は `codex exec resume <session_id>` で行い、`--last` は使わない(他のcodexセッションを誤って再開するリスクがあるため)
- `resume` は `-s` / `-C` フラグ非対応。**リポジトリルートをcwdにして実行し、sandboxは `-c sandbox_mode=workspace-write` で明示する**(無指定だと既定sandboxで走り書き込みに失敗しうる)

## 手順

0. **[監督者] preflight**: 以下を確認し、満たさない場合は着手せず報告して終了する
   - `codex --version` が成功する
   - `git status` でworking treeがクリーンである(dirtyだと検収のスコープ外差分チェックとコミット範囲が壊れるため)
   - `uv sync --group dev` を実行し、テスト系コマンドがオフラインで動く状態にしておく(Codexサンドボックスはネットワーク遮断)
1. **[監督者] 着手判定**: run-taskフロー手順1〜2を実施する。frontmatterの `blocked_by` に未doneのタスクがあれば着手せず報告して終了。DoDが既に全て満たされていると判断した場合は委譲せず、実ファイルで根拠を検証したうえで手順7へ進む(この場合の「検証方法・根拠」節の記入は記帳として監督者が行う)
2. **[監督者] 記帳**: タスクfrontmatterの `status` を `in_progress` に更新する
3. **[Codex] 実装**: 実装プロンプトを `<scratchpad>/codex-prompt-<task_id>.md` に書き、以下の形で委譲する

   ```bash
   codex exec -C <リポジトリルート絶対パス> -s workspace-write -m gpt-5.5 \
     -c model_reasoning_effort=high \
     -o <scratchpad>/codex-impl-<task_id>.md \
     - < <scratchpad>/codex-prompt-<task_id>.md
   ```

   実装プロンプトに含めるもの:
   - タスクファイルの絶対パスと、実装に関わる作業内容(run-taskフロー手順3〜5相当): 実装・検証、DoD各項目の検証結果を「検証方法・根拠」節へ記入、知見の記録。記録先の使い分けを明記する: 対象プロダクトの業務知識→`docs/domain/<product>/` / 運用・プロセスの学び、gate較正の気づき→`docs/knowledge/learning-log.md`(エントリに型を付ける) / 設計判断→`docs/decisions/`(North Starからの逸脱は実施**前**にADR起票。勝手に逸脱しない)
   - 契約定義系タスク(schema等)では、その契約のproducer / consumerとなる下流タスク(当該タスクを `blocked_by` に持つタスク)のファイルパスも渡し、契約の必須度(required / minItems / nullable)を各下流タスクのDoD・Phase能力と突き合わせて決めるよう指示する(North Starのサンプルinstanceが全fieldを埋めていても必須化の根拠にしない。learning-log 2026-07-02「出力契約schemaの必須度は最初のproducerのPhase能力と突き合わせて決める」の再発防止)
   - 制約:
     - AGENTS.mdの実装規約・変更ルールに従う。タスクスコープ外の変更をしない
     - `docs/` 配下にsecret / PII / 本番データの生値を書かない(redaction必須)
     - `uv run pytest` / `uv run ruff check .` / `uv run ruff format --check .`(schema変更時は `uv run python scripts/gen_models.py` も)をグリーンにする
     - 依存パッケージの追加・更新はしない。必要になったら作業を止めて最終メッセージで報告する(サンドボックスがネットワーク遮断のため。監督者が `uv add` を代行してから `resume <session_id>` で再委譲する)
     - uv cacheの書き込み先が必要な場合(サンドボックスは `~/.cache/uv` に書けない)は `UV_CACHE_DIR=$TMPDIR/uv-cache` などrepo外を使う。repo直下に `.uv-cache` 等のキャッシュを作らない(サンドボックスは `/tmp` / `$TMPDIR` にも書ける)
     - `status` は `in_progress` のまま(done化・`_index.md` 再生成・gitコミット・push は監督者が行うので**しない**)
     - ADR起票が目的のタスク(例: T-011, T-017)ではADRのdraft(status: proposed)作成までを行い、採択はしない。それ以外でも人間の承認が必要な事項(技術選定等)に当たったら作業を止め、最終メッセージで理由を報告する
4. **[監督者] 一次検収**: Codexの最終メッセージ(`-o` ファイル)を読み、**自己申告を信用せず**実ファイルで裏取りする:
   - テスト一式を自分で再実行する(pytest / ruff check / ruff format --check / gen_models --check)
   - DoD各項目を実ファイルと突き合わせる
   - 成果物がNorth Star・計画の該当§に準拠しているか照合する
   - ドキュメント記入(検証方法・根拠、知見記録)の漏れ、スコープ外差分の混入(`git status` / `git diff`)を確認する
   - 検収の深さ: 通常タスクは要点を絞った検収でよい。論理密度の高いタスク(validator実装、ID設計、決定性検証、ADR系)は時間をかけて深く検証する
   - **指摘ゼロの場合は手順5・6をスキップして手順7へ進む**
5. **[Codex] 修正**(指摘がある場合のみ): 指摘を「ファイル / 問題 / 期待する状態」の具体的リストとしてファイルに書き、手順3で控えたsession idに対して追撃する(推論はmediumへ下げる)。リポジトリルートで実行すること:

   ```bash
   codex exec resume <session_id> \
     -c sandbox_mode=workspace-write \
     -c model_reasoning_effort=medium \
     -o <scratchpad>/codex-fix-<task_id>-<n>.md \
     - < <scratchpad>/codex-fix-prompt-<task_id>-<n>.md
   ```
6. **[監督者] 二次検収**: 修正差分に絞って確認し、テスト一式を再実行する。問題が残る場合は手順5へ戻る。**修正→検収は最大2周**(カウントするのは検収指摘に基づく手順5の修正のみ。失敗復旧のresumeや依存追加後の再委譲は数えない)。超えたら「blocked化の共通手順」(ルール節)を実施して終了する
7. **[監督者] 完了処理**: run-taskフロー手順6〜7を実施する(「記録」節に記録先リンクを記入(なければ「なし」)、`status: done` へ更新、`_index.md` 再生成)。再生成後の整合確認に `--check` を使う場合はAGENTS.mdの `--generated-on` 注記に従う(省略すると日付差の偽陽性が出る)。Codexサンドボックスの残渣(repo内に作られた `.uv-cache` 等のキャッシュ。自己ignoreされ `git status` に出ないことがある)が残っていれば削除する
8. **[監督者] コミット&push**: タスクで変更・追加したファイルのみを明示的にステージし(`git add -A` 禁止)、conventional commits形式(例: `feat: T-xxx <内容>`)でコミットしてpushする

## ルール

- run-taskフローの「ルール」節を全て適用する
- 人間の承認が必要な決定(ADR採択、技術選定等)に到達したら、進めずに AskUserQuestion で確認する(ADR draftの起票まではCodexが実施してよい)
- `model_reasoning_effort=minimal` は使わない(Codex側ツール構成と非互換でAPIエラーになることを確認済み)
- 失敗時の分岐:
  - Codexが**途中停止**した場合(session id取得済み・成果物が中途半端): 原因を特定し、`resume <session_id>` で1回だけ復旧を試みる
  - **CLIエラー・認証エラー・session id取得前の失敗**: resumeせず、原因を解消できる場合のみ新規実行を1回試す。解消できなければ「blocked化の共通手順」を実施する
  - **30分以上ログが進まない場合**: ハングとみなしてプロセスを終了し、上記と同様に扱う
- **blocked化の共通手順**: (1) 実装差分を `git stash push -u -m "<task_id> blocked"` で退避する(タスクファイルの記帳も一旦退避される) → (2) タスクfrontmatterの `status` を `blocked` に更新し、理由とstashへ退避した旨をタスクファイルに追記する → (3) `_index.md` を再生成する → (4) タスクファイルと `_index.md` のみコミット・pushして報告する(working treeをクリーンに戻し、次タスクのpreflightが通る状態にする)
- Codexへの委譲は実装・修正のみ。検収・記帳・git操作を委譲しない
