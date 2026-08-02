# source_connector/ — 対象repoから変更を取得する境界

W1(source grounding)の入力を供給する。North Star §5.1(Source Connectors)/ §5.2(Ingestion & Normalization)の最小実装(T-026)。

```text
TargetRepository.from_env() → SourceConnector.fetch_change(base, head) → ChangeSet
```

```bash
uv run python -m source_connector --repo . --label veridia --base main --head HEAD --output change.json
```

## 設定

| 環境変数 | 内容 | 既定 |
|---|---|---|
| `VERIDIA_TARGET_REPO_PATH` | 対象repoのpath | なし(未設定は文脈付きエラー) |
| `VERIDIA_TARGET_REPO_LABEL` | 導出refに使う名前 | ディレクトリ名 |

CLIの `--repo` / `--label` が環境変数より優先される。

## 設計上の約束(テストで固定している)

1. **対象はコードではなく設定。** Phase 1の対象はveridia自身([T-024](../docs/tasks/phase-1/T-024-target-service-decision.md))だが、このモジュールはveridiaを一切名指ししない。別repoへ向けるのは環境変数の変更だけで済む(`TestConfigurationIsSwappable` が `vendor/sqk-core` を第2のrepoとして実証)。
2. **veridiaは資格情報に触れない。** ローカルgit repositoryしか読まないので漏れるものが無い(ADR-0005が推論backendでCLIへ認証を委譲しているのと同じ原則)。`TestNoCredentialsAreHandled` がソース中に認証系の環境変数名が現れないことを固定する。
3. **revisionは使う前に検証する。** argvを固定してもrevision文字列が `--upload-pack=...` のようにoptionへ化けるとgitの解釈が変わる。`-` 始まりと空文字を拒否する。
4. **解決できないrevisionは空diffにしない。** `RevisionRangeError` を送出する。「変更なし」と「refが無い」を取り違えると、後段のgateが素通りする。
5. **refはSHAへ解決してから記録する。** `HEAD` のような可変refのままでは、同じ `ChangeSet` を後から再現できない。

## `source_refs`

`ChangeSet.source_refs` はそのまま下流artifactの `source_refs` になり、**source grounding gate([T-057](../gate_evaluator/README.md))がこの値を判定する**。

- 導出ref: `git://<label>/<base_sha>...<head_sha>`(常に1件入る。空にならない)
- `change_ref`: PR URL等、repoからは分からない恒久refを呼び出し側が添えられる。あれば先頭に入る

## スコープ外(OQ-4の決定範囲)

**Phase 1で対応するsourceはローカルgit repositoryのcommit rangeのみ。** GitHub API経由のPR取得・認証・rate limit・private repoアクセスは実装せず、Phase 1では一度も踏まない。対象がveridia自身なので全変更がローカルgitで到達でき、認証を扱わない設計にできるため。PR URLのような恒久refは `change_ref` で供給できるのでprovenanceは失わない。

外部の実在サービスへ横展開する時点([phase-1計画 §1](../docs/plan/phase-1-crud-mvp.md#1-目的と対象) の移行条件)で再評価する。

## diff parserの再利用

`change_impact_generator.diff_parser.parse_unified_diff` をそのまま使う(T-010の資産)。ただし同関数は**file entryが1件も無いdiffをValueErrorにする** — CLI入力としては正しいが、commit rangeとしては「変更なし」が正当な結果なので、空出力はconnector側で短絡する。中身があって読めない場合は `DiffParseError` にする(変更なしへ退化させない)。
