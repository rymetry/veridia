---
task_id: T-002
epic: artifact-schema
plan_ref: phase-0-foundation.md#5-技術選定adr起票が必要な決定
status: done
owner:
blocked_by: [T-001]
---

# T-002: 開発環境scaffolding(build / test / lint)

## 目的

ADR-0002の決定に基づき、以降の全実装タスクが使うbuild / test / lint環境を整備する。AGENTS.mdの「実装規約」節(コード導入後に追記する、とされている箇所)を埋める。

## 参照

- 計画: §5 技術選定
- ADR-0002(T-001の成果物)

## 技術選定(T-002で確定)

ADR-0002がPython 3.12+ / Pydantic v2 / jsonschemaを決定済み。T-002に委任された具体化は次の通り(ADR委任範囲内のため新規ADR不要):

- **パッケージ/環境/ツール管理: uv**。理由: 依存・仮想環境・Pythonツールチェーン(3.12)を単一ツールで管理でき、install / test / lint が各1コマンドで完結する。Python本体もuvが自動取得するためグローバルなPoetry/ruff/pytestが未インストールでも初期セットアップが最短。個人開発の保守負荷が最小(ADR-0002の判断軸「学習コスト・保守負荷・エコシステムの一体性」に合致)。
- 開発Pythonは `.python-version` で 3.12 に固定(`requires-python >=3.12` を満たしつつ環境を再現可能にする)。
- test=pytest、lint/format=ruff。datamodel-code-generatorはdev依存として用意(生成コマンドの配線はschema実体が揃うT-003へ申し送り。下記「記録」参照)。

## DoD

- [x] 依存インストール・テスト実行・lintがそれぞれ単一コマンドで実行でき、ローカルでの実行が成功する(実行ログで確認)
- [x] サンプルテスト1件がパスする
- [x] AGENTS.md「実装規約」にbuild / test / lintコマンドとスタックが追記されている
- [x] `docs/tasks/phase-0/_index.md` をfrontmatterから再生成するスクリプトが追加され、その出力が現行の_index.mdと一致する(列仕様は `docs/tasks/README.md` 準拠。配置は実装時に決定)

## 検証方法・根拠

### 追加/変更ファイル

- `pyproject.toml`(project設定・依存・ruff/pytest設定)、`.python-version`(3.12固定)
- `scripts/regen_task_index.py`(CLIエントリ)+ `scripts/task_index/`(`models.py` / `frontmatter.py` / `epic_labels.py` / `epic_labels.toml` / `render.py` / `cli.py`)
- `tests/test_frontmatter.py` / `tests/test_render.py` / `tests/test_cli.py`(計15件)
- `AGENTS.md`「実装規約」節、`docs/knowledge/learning-log.md`

### 単一コマンド実行(DoD 1・2)

```text
# install(build相当)
$ uv sync --group dev
Resolved 34 packages ... Installed 32 packages   # 成功(Python 3.12.9 の.venv作成)

# test(サンプルテスト = _index再生成のパース/整形ロジックのテストが兼ねる)
$ uv run pytest
collected 15 items
tests/test_cli.py ....  tests/test_frontmatter.py .......  tests/test_render.py ....
15 passed in 0.02s

# lint
$ uv run ruff check .
All checks passed!
```

### _index再生成のバイト一致検証(DoD 4)

T-002のstatus変更で集計が変わるのを避けるため、**HEADコミット時点**のタスクファイル群に対して検証した。手順: `git show HEAD:docs/tasks/phase-0/<file>` で全23タスクmd + `_index.md` を一時ディレクトリへ展開 → スクリプトを実行 → HEADの `_index.md` とdiff。

```text
$ uv run python scripts/regen_task_index.py <headdir> --generated-on 2026-07-02
wrote: <headdir>/_index.md

$ diff <golden: git show HEAD:.../_index.md> <headdir>/_index.md
DIFF: no differences (identical)

$ cmp <golden> <headdir>/_index.md
CMP: byte-identical

$ shasum -a 256 <golden> <headdir>/_index.md
d4ae0c89e9b6596128ddca506ef83279f1c0fd59d5859d75eef5584e6c27c609  <golden>
d4ae0c89e9b6596128ddca506ef83279f1c0fd59d5859d75eef5584e6c27c609  <headdir>/_index.md

$ wc -c <golden> <headdir>/_index.md
3888 <golden>   3888 <headdir>   # 両者3888バイトで一致
```

HEAD時点の集計(not_started: 22 / done: 1)を含め全文がバイト一致。スクリプトは frontmatter欠落・不正status値・H1不在/task_id不一致・未定義epic を例外化(黙って壊れない)し、`--check` でCI用の差分検出も可能。

### 作業ツリーの最終 _index.md 再生成(DoD 4・作業フロー5)

T-002をdoneにした最終状態で、リポジトリ内 `docs/tasks/phase-0/` に対して再生成した。集計は not_started: 21 / done: 2(T-001・T-002がdone)。

## 記録

- learning-log: [datamodel-code-generator生成コマンド+CI diff検証をT-003へ申し送り](../../knowledge/learning-log.md)(2026-07-02, process-learning)。schema実体が無い段階では生成の配線・CI diffが検証不能なため、T-002ではツール用意に留め配線はT-003へ移した。
- decisions: 新規ADRなし(uv/ruff/pytestの具体化はADR-0002がT-002へ委任済み)。確定スタックはAGENTS.md「実装規約」に反映。
- domain: なし。
