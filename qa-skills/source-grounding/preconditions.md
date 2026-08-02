# Preconditions

- `ChangeSet` が1件与えられ、`repository_label` / `base_sha` / `head_sha` / `source_refs` を持つ。
- `source_refs` が空でない(空のsourceからgroundingは作れない。§6.1)。
- `base_sha` / `head_sha` が解決済みのcommit SHAである(`HEAD` 等の可変refでは、同じ結果を後から再現できない)。
- `diff_text` と `changed_files` が同じrangeから取得されている。
